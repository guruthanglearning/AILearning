using System.Net.Http.Json;
using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Services;

public class SessionApiClient : ISessionApiClient
{
    private readonly HttpClient _http;
    private readonly ILogger<SessionApiClient> _logger;

    public SessionApiClient(HttpClient http, ILogger<SessionApiClient> logger)
    {
        _http = http;
        _logger = logger;
    }

    public async Task<IReadOnlyList<SessionSummary>> ListAsync(int limit = 20, CancellationToken ct = default)
    {
        try
        {
            var result = await _http.GetFromJsonAsync<List<SessionSummary>>($"/api/sessions?limit={limit}", ct);
            return result ?? [];
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to list sessions");
            return [];
        }
    }

    public async Task<SessionRecord?> GetAsync(Guid sessionId, CancellationToken ct = default)
    {
        try
        {
            return await _http.GetFromJsonAsync<SessionRecord>($"/api/sessions/{sessionId}", ct);
        }
        catch (HttpRequestException ex) when (ex.StatusCode == System.Net.HttpStatusCode.NotFound)
        {
            return null;
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to get session {SessionId}", sessionId);
            return null;
        }
    }
}
