namespace MultiAgentDevTeam.Shared.Configuration;

public class AgentConfiguration
{
    public const string SectionName = "AgentConfiguration";

    public string AnthropicApiKey { get; set; } = string.Empty;
    public string DefaultModel { get; set; } = "claude-opus-4-6";
    public string FastModel { get; set; } = "claude-haiku-4-5-20251001";
    public int MaxReviewLoops { get; set; } = 3;
    public int MaxTokens { get; set; } = 16384;
    public int TimeoutSeconds { get; set; } = 600;
    public string SessionStoragePath { get; set; } = "sessions";
    public int RateLimitRequestsPerMinute { get; set; } = 10;
}
