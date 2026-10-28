using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Text.RegularExpressions;
using System.Threading.Channels;

namespace MultiAgentDevTeam.Orchestrator.Services;

public interface IOrchestratorService
{
    Task<OrchestratorResponse> RunAsync(OrchestratorRequest request, CancellationToken cancellationToken = default);
    IAsyncEnumerable<string> StreamAsync(OrchestratorRequest request, CancellationToken cancellationToken = default);
}

public class OrchestratorService : IOrchestratorService
{
    private readonly IAgent _pmAgent;
    private readonly IAgent _architectAgent;
    private readonly IAgent _developerAgent;
    private readonly IAgent _reviewerAgent;
    private readonly IAgent _qaAgent;
    private readonly IAgent _securityAgent;
    private readonly IAgent _devOpsAgent;
    private readonly IAgent _docsAgent;
    private readonly AgentConfiguration _config;
    private readonly ISessionRepository _sessions;
    private readonly ILogger<OrchestratorService> _logger;

    public OrchestratorService(
        IEnumerable<IAgent> agents,
        IOptions<AgentConfiguration> config,
        ISessionRepository sessions,
        ILogger<OrchestratorService> logger)
    {
        var agentList = agents.ToList();
        _pmAgent        = GetAgent(agentList, ArtifactType.Requirements);
        _architectAgent = GetAgent(agentList, ArtifactType.Architecture);
        _developerAgent = GetAgent(agentList, ArtifactType.SourceCode);
        _reviewerAgent  = GetAgent(agentList, ArtifactType.ReviewNotes);
        _qaAgent        = GetAgent(agentList, ArtifactType.TestResults);
        _securityAgent  = GetAgent(agentList, ArtifactType.SecurityReport);
        _devOpsAgent    = GetAgent(agentList, ArtifactType.DeploymentConfig);
        _docsAgent      = GetAgent(agentList, ArtifactType.Documentation);
        _config         = config.Value;
        _sessions       = sessions;
        _logger         = logger;
    }

    private static IAgent GetAgent(List<IAgent> agents, ArtifactType type) =>
        agents.FirstOrDefault(a => a.OutputType == type)
        ?? throw new InvalidOperationException($"No agent registered for {type}");

    // ── Full blocking run ──────────────────────────────────────────────────────

    public async Task<OrchestratorResponse> RunAsync(OrchestratorRequest request, CancellationToken cancellationToken = default)
    {
        var channel = Channel.CreateUnbounded<string>(new UnboundedChannelOptions { SingleReader = true });

        // Run pipeline in background, drain progress channel (we don't need it here)
        var pipelineTask = ExecutePipelineAsync(request, channel.Writer, cancellationToken);
        _ = Task.Run(async () =>
        {
            await foreach (var _ in channel.Reader.ReadAllAsync(CancellationToken.None)) { }
        }, CancellationToken.None);

        return await pipelineTask;
    }

    // ── Streaming run (SSE) ────────────────────────────────────────────────────

    public async IAsyncEnumerable<string> StreamAsync(
        OrchestratorRequest request,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        var channel = Channel.CreateUnbounded<string>(new UnboundedChannelOptions { SingleReader = true });

        var pipelineTask = ExecutePipelineAsync(request, channel.Writer, cancellationToken);

        await foreach (var message in channel.Reader.ReadAllAsync(cancellationToken))
            yield return message;

        // Await to surface any unhandled exception from the pipeline task
        await pipelineTask;
    }

    // ── Core pipeline ──────────────────────────────────────────────────────────

    private async Task<OrchestratorResponse> ExecutePipelineAsync(
        OrchestratorRequest request,
        ChannelWriter<string> progress,
        CancellationToken ct)
    {
        var stopwatch = Stopwatch.StartNew();
        var store = new ArtifactStore { OriginalRequirement = request.Requirement };
        var log = new List<string>();
        var usage = new List<TokenUsage>();
        var maxLoops = request.MaxReviewLoops > 0 ? request.MaxReviewLoops : _config.MaxReviewLoops;

        _logger.LogInformation("=== Orchestrator starting session {SessionId} ===", store.SessionId);

        OrchestratorResponse response;

        try
        {
            // ── Phase 1: Requirements ──────────────────────────────────────────
            if (!ShouldSkip(request, "pm"))
            {
                await RunAgent(usage, _pmAgent, store, log, progress,
                    new AgentRequest { Task = $"Extract complete requirements from this request:\n\n{request.Requirement}" },
                    ct);
            }

            // ── Phase 2: Architecture ──────────────────────────────────────────
            if (!ShouldSkip(request, "architect"))
            {
                await RunAgent(usage, _architectAgent, store, log, progress,
                    new AgentRequest
                    {
                        Task = "Design the complete system architecture for the following requirements.",
                        Context = BuildContext(store, ArtifactType.Requirements)
                    }, ct);
            }

            // ── Phase 3: Development + Review feedback loop ────────────────────
            if (!ShouldSkip(request, "developer"))
            {
                string? feedback = null;

                for (int attempt = 1; attempt <= maxLoops; attempt++)
                {
                    _logger.LogInformation("Developer attempt {Attempt}/{Max}", attempt, maxLoops);

                    await RunAgent(usage, _developerAgent, store, log, progress,
                        new AgentRequest
                        {
                            Task = "Implement the complete system based on requirements and architecture.",
                            Context = BuildContext(store, ArtifactType.Requirements, ArtifactType.Architecture),
                            PreviousFeedback = feedback
                        }, ct);

                    if (ShouldSkip(request, "reviewer")) break;

                    await RunAgent(usage, _reviewerAgent, store, log, progress,
                        new AgentRequest
                        {
                            Task = "Review the following source code thoroughly.",
                            Context = BuildContext(store, ArtifactType.SourceCode)
                        }, ct);

                    var reviewContent = store.GetContent(ArtifactType.ReviewNotes);
                    // The reviewer often prefixes its verdict with blank lines
                    if (reviewContent.TrimStart().StartsWith("APPROVED", StringComparison.OrdinalIgnoreCase))
                    {
                        var msg = $"✅ Code approved on attempt {attempt}";
                        log.Add(msg);
                        await progress.WriteAsync(msg, ct);
                        break;
                    }

                    feedback = reviewContent;
                    var rejected = $"⚠️ Code rejected on attempt {attempt} — sending back to developer";
                    log.Add(rejected);
                    await progress.WriteAsync(rejected, ct);

                    if (attempt == maxLoops)
                    {
                        var maxMsg = "⚠️ Max review loops reached — proceeding with last version";
                        log.Add(maxMsg);
                        await progress.WriteAsync(maxMsg, ct);
                    }
                }
            }

            // ── Phase 4: QA + Security in parallel ────────────────────────────
            var parallelTasks = new List<Task>();

            if (!ShouldSkip(request, "qa"))
                parallelTasks.Add(RunAgent(usage, _qaAgent, store, log, progress,
                    new AgentRequest
                    {
                        Task = "Write the tests this code needs, targeting 80%+ coverage.",
                        Context = BuildContext(store, ArtifactType.Requirements, ArtifactType.SourceCode)
                    }, ct));

            if (!ShouldSkip(request, "security"))
                parallelTasks.Add(RunAgent(usage, _securityAgent, store, log, progress,
                    new AgentRequest
                    {
                        Task = "Perform a full security audit of the source code.",
                        Context = BuildContext(store, ArtifactType.SourceCode)
                    }, ct));

            if (parallelTasks.Count > 0)
            {
                var parallelMsg = "⚡ Running QA + Security agents in parallel";
                log.Add(parallelMsg);
                await progress.WriteAsync(parallelMsg, ct);
                await Task.WhenAll(parallelTasks);
            }

            // ── Phase 5: DevOps ────────────────────────────────────────────────
            if (!ShouldSkip(request, "devops"))
            {
                await RunAgent(usage, _devOpsAgent, store, log, progress,
                    new AgentRequest
                    {
                        Task = "Create the deployment configuration this project needs.",
                        // CI only needs to know where the tests live, not their full source
                        Context = WithTestFileIndex(store, BuildContext(store, ArtifactType.Architecture, ArtifactType.SourceCode))
                    }, ct);
            }

            // ── Phase 6: Documentation ─────────────────────────────────────────
            if (!ShouldSkip(request, "docs"))
            {
                await RunAgent(usage, _docsAgent, store, log, progress,
                    new AgentRequest
                    {
                        Task = "Generate the developer documentation this project needs.",
                        Context = BuildContext(store,
                            ArtifactType.Requirements, ArtifactType.Architecture,
                            ArtifactType.SourceCode, ArtifactType.DeploymentConfig)
                    }, ct);
            }

            stopwatch.Stop();
            _logger.LogInformation("=== Orchestrator completed session {SessionId} in {Duration}s ===",
                store.SessionId, stopwatch.Elapsed.TotalSeconds);
            await ReportCostAsync(usage, log, progress, ct);

            response = new OrchestratorResponse
            {
                Success = true,
                SessionId = store.SessionId,
                Artifacts = store.All.ToDictionary(kvp => kvp.Key.ToString(), kvp => kvp.Value.Content),
                AgentLog = log,
                TotalDuration = stopwatch.Elapsed,
                Usage = usage
            };
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            _logger.LogError(ex, "Orchestrator failed for session {SessionId}", store.SessionId);
            var kind = ex is AgentFailedException agentEx ? agentEx.Kind : AgentFailureKind.Internal;

            // SSE has already sent 200 by now, so the reason has to travel as a final message
            var failedMsg = $"🛑 Pipeline failed: {PipelineFailure.Describe(kind)}";
            log.Add(failedMsg);
            progress.TryWrite(failedMsg);

            var costMsg = CostSummary(usage);
            if (costMsg is not null)
            {
                log.Add(costMsg);
                progress.TryWrite(costMsg);
            }

            response = new OrchestratorResponse
            {
                Success = false,
                SessionId = store.SessionId,
                ErrorMessage = ex.Message,
                FailureKind = kind,
                AgentLog = log,
                TotalDuration = stopwatch.Elapsed,
                Usage = usage
            };
        }
        finally
        {
            progress.Complete();
        }

        // Persist session regardless of success/failure
        await PersistSessionAsync(store, response);

        return response;
    }

    // ── Helpers ────────────────────────────────────────────────────────────────

    private async Task RunAgent(
        List<TokenUsage> usage,
        IAgent agent,
        ArtifactStore store,
        List<string> log,
        ChannelWriter<string> progress,
        AgentRequest request,
        CancellationToken ct)
    {
        _logger.LogInformation("[Orchestrator] Dispatching to {Agent}", agent.Name);
        var startMsg = $"🤖 {agent.Name} started";
        log.Add(startMsg);
        await progress.WriteAsync(startMsg, ct);

        var agentResponse = await agent.RunAsync(request, ct);

        // QA and Security run in parallel and share the list
        if (agentResponse.Usage is not null)
            lock (usage) usage.Add(agentResponse.Usage);

        if (!agentResponse.Success)
        {
            var failMsg = $"❌ {agent.Name} failed: {agentResponse.ErrorMessage}";
            log.Add(failMsg);
            await progress.WriteAsync(failMsg, ct);
            throw new AgentFailedException(agent.Name, agentResponse.ErrorMessage ?? "unknown error", agentResponse.FailureKind);
        }

        store.Set(new Artifact
        {
            Type = agent.OutputType,
            Content = agentResponse.Content,
            Author = agent.Name,
            Status = ArtifactStatus.Approved
        });

        var cost = agentResponse.Usage?.EstimatedCostUsd is { } c ? $" (~${c:F4})" : string.Empty;
        var doneMsg = $"✅ {agent.Name} completed in {agentResponse.Duration.TotalSeconds:F1}s{cost}";
        log.Add(doneMsg);
        await progress.WriteAsync(doneMsg, ct);

        if (agentResponse.Truncated)
        {
            var truncatedMsg = $"⚠️ {agent.Name} output hit the token limit and is incomplete";
            log.Add(truncatedMsg);
            await progress.WriteAsync(truncatedMsg, ct);
        }
    }

    private async Task PersistSessionAsync(ArtifactStore store, OrchestratorResponse response)
    {
        try
        {
            var record = new SessionRecord
            {
                SessionId = response.SessionId,
                Requirement = store.OriginalRequirement,
                StartedAt = store.StartedAt,
                CompletedAt = DateTime.UtcNow,
                Success = response.Success,
                Artifacts = response.Artifacts,
                AgentLog = response.AgentLog,
                TotalDuration = response.TotalDuration.ToString(),
                ErrorMessage = response.ErrorMessage,
                Usage = response.Usage,
                EstimatedCostUsd = response.EstimatedCostUsd
            };

            await _sessions.SaveAsync(record);
        }
        catch (Exception ex)
        {
            _logger.LogWarning(ex, "Failed to persist session {SessionId} — pipeline result is unaffected", response.SessionId);
        }
    }

    private static Dictionary<string, string> BuildContext(ArtifactStore store, params ArtifactType[] types) =>
        types
            .Where(store.Has)
            .ToDictionary(t => t.ToString(), t => store.GetContent(t));

    private async Task ReportCostAsync(List<TokenUsage> usage, List<string> log, ChannelWriter<string> progress, CancellationToken ct)
    {
        var costMsg = CostSummary(usage);
        if (costMsg is null) return;

        _logger.LogInformation("{CostSummary}", costMsg);
        log.Add(costMsg);
        await progress.WriteAsync(costMsg, ct);
    }

    public static string? CostSummary(IReadOnlyCollection<TokenUsage> usage)
    {
        if (usage.Count == 0) return null;

        var total = usage.Sum(u => u.EstimatedCostUsd ?? 0m);
        return $"💰 Estimated API cost: ${total:F4} across {usage.Count} calls " +
               $"({usage.Sum(u => u.InputTokens):N0} input, {usage.Sum(u => u.OutputTokens):N0} output, " +
               $"{usage.Sum(u => u.CacheReadInputTokens):N0} cache-read, " +
               $"{usage.Sum(u => u.CacheCreationInputTokens):N0} cache-write tokens)";
    }

    private static readonly Regex FileHeader = new(@"^### File:\s*(.+)$", RegexOptions.Multiline | RegexOptions.Compiled);

    private static Dictionary<string, string> WithTestFileIndex(ArtifactStore store, Dictionary<string, string> context)
    {
        if (!store.Has(ArtifactType.TestResults)) return context;

        var files = FileHeader.Matches(store.GetContent(ArtifactType.TestResults))
            .Select(m => $"- {m.Groups[1].Value.Trim()}")
            .ToList();
        if (files.Count > 0)
            context["TestFiles"] = string.Join("\n", files);
        return context;
    }

    private static bool ShouldSkip(OrchestratorRequest request, string agentKey) =>
        request.SkipAgents.Contains(agentKey, StringComparer.OrdinalIgnoreCase);
}
