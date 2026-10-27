using Anthropic.SDK;
using Anthropic.SDK.Messaging;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Diagnostics;
using System.Net;
using System.Security.Authentication;
using System.Text.RegularExpressions;

namespace MultiAgentDevTeam.Shared.Agents;

public abstract class BaseAgent : IAgent
{
    private readonly AnthropicClient _client;
    protected readonly ILogger Logger;

    protected BaseAgent(AnthropicClient client, ILogger logger)
    {
        _client = client;
        Logger = logger;
    }

    public abstract string Name { get; }
    public abstract ArtifactType OutputType { get; }
    protected abstract string SystemPrompt { get; }
    protected virtual string Model => "claude-opus-4-6";
    protected virtual int MaxTokens => 8192;

    public async Task<AgentResponse> RunAsync(AgentRequest request, CancellationToken cancellationToken = default)
    {
        var stopwatch = Stopwatch.StartNew();
        Logger.LogInformation("[{Agent}] Starting task: {Task}", Name, request.Task[..Math.Min(80, request.Task.Length)]);

        try
        {
            var userContent = BuildUserContent(request);
            var messages = new List<Message>
            {
                new() { Role = RoleType.User, Content = userContent }
            };

            var response = await _client.Messages.GetClaudeMessageAsync(
                new MessageParameters
                {
                    Model = Model,
                    MaxTokens = MaxTokens,
                    SystemMessage = SystemPrompt,
                    Messages = messages
                }, null, cancellationToken);

            var content = response.Content.OfType<TextContent>().FirstOrDefault()?.Text ?? string.Empty;
            stopwatch.Stop();

            Logger.LogInformation("[{Agent}] Completed in {Duration}ms", Name, stopwatch.ElapsedMilliseconds);
            return AgentResponse.Ok(content, Name, stopwatch.Elapsed);
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            Logger.LogError(ex, "[{Agent}] Failed after {Duration}ms", Name, stopwatch.ElapsedMilliseconds);
            return AgentResponse.Fail(ex.Message, Name, ClassifyFailure(ex, cancellationToken));
        }
    }

    /// <summary>
    /// Maps an exception from the Anthropic SDK / HttpClient to a failure category.
    /// The SDK throws AuthenticationException for a rejected key and HttpRequestException
    /// for other non-success responses.
    /// </summary>
    public static AgentFailureKind ClassifyFailure(Exception ex, CancellationToken cancellationToken = default) =>
        ex switch
        {
            AuthenticationException => AgentFailureKind.Authentication,
            HttpRequestException httpEx => GetStatusCode(httpEx) switch
            {
                HttpStatusCode.Unauthorized or HttpStatusCode.Forbidden => AgentFailureKind.Authentication,
                HttpStatusCode.TooManyRequests => AgentFailureKind.RateLimited,
                _ => AgentFailureKind.Upstream
            },
            // HttpClient.Timeout surfaces as TaskCanceledException without the caller having cancelled
            OperationCanceledException when !cancellationToken.IsCancellationRequested => AgentFailureKind.Timeout,
            TimeoutException => AgentFailureKind.Timeout,
            _ => AgentFailureKind.Internal
        };

    // Anthropic.SDK 3.x leaves HttpRequestException.StatusCode null and only reports the
    // status in the message ("... with HTTP status code: TooManyRequests. Content: ...")
    private static readonly Regex StatusInMessage = new(@"HTTP status code: (\w+)", RegexOptions.Compiled);

    private static HttpStatusCode? GetStatusCode(HttpRequestException ex)
    {
        if (ex.StatusCode is not null)
            return ex.StatusCode;

        var match = StatusInMessage.Match(ex.Message);
        return match.Success && Enum.TryParse<HttpStatusCode>(match.Groups[1].Value, out var status)
            ? status
            : null;
    }

    private string BuildUserContent(AgentRequest request)
    {
        var parts = new List<string>();

        if (request.Context.Count > 0)
        {
            parts.Add("## Context from previous agents:");
            foreach (var (key, value) in request.Context)
                parts.Add($"### {key}\n{value}");
        }

        if (!string.IsNullOrWhiteSpace(request.PreviousFeedback))
            parts.Add($"## Feedback to address:\n{request.PreviousFeedback}");

        parts.Add($"## Your Task:\n{request.Task}");
        return string.Join("\n\n", parts);
    }
}
