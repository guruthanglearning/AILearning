namespace MultiAgentDevTeam.BlazorUI.Models;

public class PipelineRequest
{
    public string Requirement { get; set; } = string.Empty;
    public List<string> SkipAgents { get; set; } = new();
    public int MaxReviewLoops { get; set; } = 3;
}

public class PipelineResponse
{
    public bool Success { get; set; }
    public Guid SessionId { get; set; }
    public Dictionary<string, string> Artifacts { get; set; } = new();
    public List<string> AgentLog { get; set; } = new();
    public TimeSpan TotalDuration { get; set; }
    public string? ErrorMessage { get; set; }
}

public class SessionSummary
{
    public Guid SessionId { get; set; }
    public string Requirement { get; set; } = string.Empty;
    public DateTime StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public bool Success { get; set; }
    public string TotalDuration { get; set; } = string.Empty;
    public int ArtifactCount { get; set; }
}

public class SessionRecord
{
    public Guid SessionId { get; set; }
    public string Requirement { get; set; } = string.Empty;
    public DateTime StartedAt { get; set; }
    public DateTime? CompletedAt { get; set; }
    public bool Success { get; set; }
    public Dictionary<string, string> Artifacts { get; set; } = new();
    public List<string> AgentLog { get; set; } = new();
    public string TotalDuration { get; set; } = string.Empty;
    public string? ErrorMessage { get; set; }
}
