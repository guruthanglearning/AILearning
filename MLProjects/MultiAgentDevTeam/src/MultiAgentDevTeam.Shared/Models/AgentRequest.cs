namespace MultiAgentDevTeam.Shared.Models;

public class AgentRequest
{
    public string Task { get; init; } = string.Empty;
    public Dictionary<string, string> Context { get; init; } = new();
    public string? PreviousFeedback { get; init; }
}

public class AgentResponse
{
    public bool Success { get; init; }
    public string Content { get; init; } = string.Empty;
    public string AgentName { get; init; } = string.Empty;
    public string? ErrorMessage { get; init; }
    public TimeSpan Duration { get; init; }

    public static AgentResponse Ok(string content, string agentName, TimeSpan duration) =>
        new() { Success = true, Content = content, AgentName = agentName, Duration = duration };

    public static AgentResponse Fail(string error, string agentName) =>
        new() { Success = false, ErrorMessage = error, AgentName = agentName };
}

public class OrchestratorRequest
{
    public string Requirement { get; init; } = string.Empty;
    public List<string> SkipAgents { get; init; } = new();
    public string? StartFromAgent { get; init; }
    public int MaxReviewLoops { get; init; } = 3;
}

public class OrchestratorResponse
{
    public bool Success { get; init; }
    public Guid SessionId { get; init; }
    public Dictionary<string, string> Artifacts { get; init; } = new();
    public List<string> AgentLog { get; init; } = new();
    public string? ErrorMessage { get; init; }
    public TimeSpan TotalDuration { get; init; }
}
