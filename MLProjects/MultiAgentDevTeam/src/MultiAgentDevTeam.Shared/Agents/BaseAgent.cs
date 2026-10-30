using Anthropic;
using Anthropic.Exceptions;
using Anthropic.Models.Beta.Messages;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Diagnostics;

namespace MultiAgentDevTeam.Shared.Agents;

public abstract class BaseAgent : IAgent
{
    // Lets a request the model declines for policy reasons be re-served by the server's
    // default fallback model instead of failing the pipeline
    private const string ServerSideFallbackBeta = "server-side-fallback-2026-07-01";

    // Output tokens cost 5x input, and without this the agents produce enterprise-sized
    // test suites and docs for a Hello World
    internal const string OutputSizeGuidance = """


        ## Output size
        Match the size of your output to the size of the request. A small or simple request gets a
        short, complete answer: no boilerplate, filler, or sections that don't apply to it. Never drop
        anything the request actually needs just to be brief.
        """;

    private readonly AnthropicClient _client;
    private readonly AgentConfiguration _config;
    private AgentModelSettings? _settings;
    protected readonly ILogger Logger;

    protected BaseAgent(AnthropicClient client, ILogger logger, IOptions<AgentConfiguration> options)
    {
        _client = client;
        _config = options.Value;
        Logger = logger;
    }

    public abstract string Name { get; }
    public abstract ArtifactType OutputType { get; }
    protected abstract string SystemPrompt { get; }

    /// <summary>The model, effort and token budget this agent runs with unless configuration overrides them.</summary>
    protected abstract AgentModelSettings DefaultSettings { get; }

    /// <summary>Key under <c>AgentConfiguration:Agents</c>, e.g. "QA" for QAAgent.</summary>
    public string ConfigKey
    {
        get
        {
            var typeName = GetType().Name;
            return typeName.EndsWith("Agent", StringComparison.Ordinal) ? typeName[..^"Agent".Length] : typeName;
        }
    }

    public AgentModelSettings Settings => _settings ??= _config.ResolveAgent(ConfigKey, DefaultSettings);

    public async Task<AgentResponse> RunAsync(AgentRequest request, CancellationToken cancellationToken = default)
    {
        var settings = Settings;
        var stopwatch = Stopwatch.StartNew();
        Logger.LogInformation("[{Agent}] Starting task on {Model} ({Effort} effort): {Task}",
            Name, settings.Model, settings.Effort, request.Task[..Math.Min(80, request.Task.Length)]);

        try
        {
            var parameters = new MessageCreateParams
            {
                Model = settings.Model,
                MaxTokens = settings.MaxTokens,
                System = new List<BetaTextBlockParam> { new() { Text = SystemPrompt + OutputSizeGuidance } },
                Messages = [new BetaUserMessageParam { Content = BuildUserContent(request, settings.CacheContext) }],
                OutputConfig = new BetaOutputConfig { Effort = ParseEffort(settings.Effort) },
                Betas = [ServerSideFallbackBeta],
                Fallbacks = new Default()
            };

            // Streaming keeps long, high-max_tokens responses clear of HTTP timeouts
            var message = await _client.Beta.Messages.CreateStreaming(parameters, cancellationToken).Aggregate();
            stopwatch.Stop();

            var content = string.Concat(message.Content.Select(b => b.Value).OfType<BetaTextBlock>().Select(t => t.Text));
            var usage = ToUsage(message);
            Logger.LogInformation(
                "[{Agent}] Completed in {Duration}ms on {Model}: {InputTokens} input, {OutputTokens} output, " +
                "{CacheReadTokens} cache read, {CacheWriteTokens} cache write tokens, ~${Cost}",
                Name, stopwatch.ElapsedMilliseconds, usage.Model, usage.InputTokens, usage.OutputTokens,
                usage.CacheReadInputTokens, usage.CacheCreationInputTokens, usage.EstimatedCostUsd);

            if (!string.Equals(usage.Model, settings.Model, StringComparison.OrdinalIgnoreCase))
                Logger.LogWarning("[{Agent}] Request was served by fallback model {Model}", Name, usage.Model);

            var stopReason = message.StopReason?.Raw();
            if (stopReason == "refusal")
            {
                Logger.LogWarning("[{Agent}] {Model} declined the request", Name, usage.Model);
                return AgentResponse.Fail($"{usage.Model} declined the request", Name, AgentFailureKind.Refused, usage);
            }

            var truncated = stopReason == "max_tokens";
            if (truncated)
                Logger.LogWarning("[{Agent}] Output hit the {MaxTokens}-token limit and is incomplete", Name, settings.MaxTokens);

            return AgentResponse.Ok(content, Name, stopwatch.Elapsed, truncated, usage);
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            Logger.LogError(ex, "[{Agent}] Failed after {Duration}ms", Name, stopwatch.ElapsedMilliseconds);
            return AgentResponse.Fail(ex.Message, Name, ClassifyFailure(ex, cancellationToken));
        }
    }

    /// <summary>Maps an exception from the Anthropic SDK / HttpClient to a failure category.</summary>
    public static AgentFailureKind ClassifyFailure(Exception ex, CancellationToken cancellationToken = default) =>
        ex switch
        {
            AnthropicUnauthorizedException or AnthropicForbiddenException => AgentFailureKind.Authentication,
            AnthropicRateLimitException => AgentFailureKind.RateLimited,
            AnthropicApiException or AnthropicIOException or AnthropicSseException or HttpRequestException => AgentFailureKind.Upstream,
            // A client timeout surfaces as TaskCanceledException without the caller having cancelled
            OperationCanceledException when !cancellationToken.IsCancellationRequested => AgentFailureKind.Timeout,
            TimeoutException => AgentFailureKind.Timeout,
            _ => AgentFailureKind.Internal
        };

    internal static Effort ParseEffort(string effort) =>
        Enum.TryParse<Effort>(effort, ignoreCase: true, out var parsed)
            ? parsed
            : throw new InvalidOperationException($"Unknown effort '{effort}'. Use low, medium, high, xhigh or max.");

    private TokenUsage ToUsage(BetaMessage message)
    {
        var model = message.Model.Raw();
        var input = message.Usage.InputTokens;
        var output = message.Usage.OutputTokens;
        var cacheWrite = message.Usage.CacheCreationInputTokens ?? 0;
        var cacheRead = message.Usage.CacheReadInputTokens ?? 0;

        return new TokenUsage
        {
            AgentName = Name,
            Model = model,
            InputTokens = input,
            OutputTokens = output,
            CacheCreationInputTokens = cacheWrite,
            CacheReadInputTokens = cacheRead,
            EstimatedCostUsd = ModelPricing.EstimateCostUsd(model, input, output, cacheWrite, cacheRead)
        };
    }

    private static List<BetaContentBlockParam> BuildUserContent(AgentRequest request, bool cacheContext)
    {
        var blocks = new List<BetaContentBlockParam>();

        // Context goes in its own block ahead of the feedback and task, so a re-run with the
        // same context (the Developer review loop) can read it from the prompt cache
        if (request.Context.Count > 0)
        {
            var contextParts = new List<string> { "## Context from previous agents:" };
            foreach (var (key, value) in request.Context)
                contextParts.Add($"### {key}\n{value}");

            var contextText = string.Join("\n\n", contextParts);
            // Assigning null would still send "cache_control": null, so only set it when caching
            blocks.Add(cacheContext
                ? new BetaTextBlockParam { Text = contextText, CacheControl = new BetaCacheControlEphemeral() }
                : new BetaTextBlockParam { Text = contextText });
        }

        var parts = new List<string>();
        if (!string.IsNullOrWhiteSpace(request.PreviousFeedback))
            parts.Add($"## Feedback to address:\n{request.PreviousFeedback}");
        parts.Add($"## Your Task:\n{request.Task}");

        blocks.Add(new BetaTextBlockParam { Text = string.Join("\n\n", parts) });
        return blocks;
    }
}
