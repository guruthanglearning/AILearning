using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.Shared.Interfaces;

public interface ISessionRepository
{
    Task SaveAsync(SessionRecord record, CancellationToken ct = default);
    Task<SessionRecord?> GetAsync(Guid sessionId, CancellationToken ct = default);
    Task<IReadOnlyList<SessionSummary>> ListAsync(int limit = 20, CancellationToken ct = default);
}

public class SessionRecord
{
    public Guid SessionId { get; init; }
    public string Requirement { get; init; } = string.Empty;
    public DateTime StartedAt { get; init; }
    public DateTime CompletedAt { get; init; }
    public bool Success { get; init; }
    public Dictionary<string, string> Artifacts { get; init; } = new();
    public List<string> AgentLog { get; init; } = new();
    public string TotalDuration { get; init; } = string.Empty;
    public string? ErrorMessage { get; init; }
}

public class SessionSummary
{
    public Guid SessionId { get; init; }
    public string Requirement { get; init; } = string.Empty;
    public DateTime StartedAt { get; init; }
    public DateTime CompletedAt { get; init; }
    public bool Success { get; init; }
    public string TotalDuration { get; init; } = string.Empty;
    public int ArtifactCount { get; init; }
}
