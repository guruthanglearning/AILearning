namespace MultiAgentDevTeam.Shared.Configuration;

public class AgentConfiguration
{
    public const string SectionName = "AgentConfiguration";

    public string AnthropicApiKey { get; set; } = string.Empty;
    public int MaxReviewLoops { get; set; } = 3;
    // Streamed responses with up to 64K output tokens can run well past 10 minutes
    public int TimeoutSeconds { get; set; } = 1800;
    public int MaxRetries { get; set; } = 4;
    public string SessionStoragePath { get; set; } = "sessions";
    public int RateLimitRequestsPerMinute { get; set; } = 10;

    /// <summary>Per-agent overrides keyed by agent key (PM, Architect, Developer, Reviewer, QA, Security, DevOps, Docs).</summary>
    public Dictionary<string, AgentModelOverride> Agents { get; set; } = new(StringComparer.OrdinalIgnoreCase);

    public AgentModelSettings ResolveAgent(string agentKey, AgentModelSettings defaults) =>
        Agents.TryGetValue(agentKey, out var overrides) ? overrides.ApplyTo(defaults) : defaults;
}
