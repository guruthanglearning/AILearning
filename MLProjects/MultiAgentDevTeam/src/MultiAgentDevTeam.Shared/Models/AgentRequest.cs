using System.Text.Json.Serialization;

namespace MultiAgentDevTeam.Shared.Models;

public class AgentRequest
{
    public string Task { get; init; } = string.Empty;
    public Dictionary<string, string> Context { get; init; } = new();
    public string? PreviousFeedback { get; init; }
}

/// <summary>
/// Why an agent (and therefore the pipeline) failed — lets the API return a meaningful
/// HTTP status instead of a generic 500 for problems that aren't bugs in this service.
/// </summary>
[JsonConverter(typeof(JsonStringEnumConverter<AgentFailureKind>))]
public enum AgentFailureKind
{
    None,
    Internal,
    Authentication,
    RateLimited,
    Timeout,
    Upstream
}

public class AgentResponse
{
    public bool Success { get; init; }
    public string Content { get; init; } = string.Empty;
    public string AgentName { get; init; } = string.Empty;
    public string? ErrorMessage { get; init; }
    public AgentFailureKind FailureKind { get; init; }
    public TimeSpan Duration { get; init; }

    /// <summary>True when the model stopped because it hit the token limit, so Content is incomplete.</summary>
    public bool Truncated { get; init; }

    public static AgentResponse Ok(string content, string agentName, TimeSpan duration, bool truncated = false) =>
        new() { Success = true, Content = content, AgentName = agentName, Duration = duration, Truncated = truncated };

    public static AgentResponse Fail(string error, string agentName, AgentFailureKind kind = AgentFailureKind.Internal) =>
        new() { Success = false, ErrorMessage = error, AgentName = agentName, FailureKind = kind };
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
    public AgentFailureKind FailureKind { get; init; }
    public TimeSpan TotalDuration { get; init; }
}

/// <summary>
/// Thrown by the orchestrator when an agent fails, carrying the failure category
/// so it survives up to the HTTP layer.
/// </summary>
public class AgentFailedException(string agentName, string message, AgentFailureKind kind)
    : Exception($"Agent '{agentName}' failed: {message}")
{
    public string AgentName { get; } = agentName;
    public AgentFailureKind Kind { get; } = kind;
}
