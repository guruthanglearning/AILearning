using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Services;

public interface ISessionApiClient
{
    Task<IReadOnlyList<SessionSummary>> ListAsync(int limit = 20, CancellationToken ct = default);
    Task<SessionRecord?> GetAsync(Guid sessionId, CancellationToken ct = default);
}
