using System.Text.Json;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;

namespace MultiAgentDevTeam.Orchestrator.Services;

public class FileSessionRepository : ISessionRepository
{
    private readonly string _baseDir;
    private readonly ILogger<FileSessionRepository> _logger;

    private static readonly JsonSerializerOptions JsonOptions = new() { WriteIndented = true };

    public FileSessionRepository(IOptions<AgentConfiguration> config, ILogger<FileSessionRepository> logger)
    {
        _baseDir = Path.IsPathRooted(config.Value.SessionStoragePath)
            ? config.Value.SessionStoragePath
            : Path.Combine(AppContext.BaseDirectory, config.Value.SessionStoragePath);

        Directory.CreateDirectory(_baseDir);
        _logger = logger;
        _logger.LogInformation("Session storage at: {Path}", _baseDir);
    }

    public async Task SaveAsync(SessionRecord record, CancellationToken ct = default)
    {
        var filePath = Path.Combine(_baseDir, $"{record.SessionId}.json");
        var json = JsonSerializer.Serialize(record, JsonOptions);
        await File.WriteAllTextAsync(filePath, json, ct);
        _logger.LogInformation("Session {SessionId} persisted to {Path}", record.SessionId, filePath);
    }

    public async Task<SessionRecord?> GetAsync(Guid sessionId, CancellationToken ct = default)
    {
        var filePath = Path.Combine(_baseDir, $"{sessionId}.json");
        if (!File.Exists(filePath)) return null;

        var json = await File.ReadAllTextAsync(filePath, ct);
        return JsonSerializer.Deserialize<SessionRecord>(json);
    }

    public async Task<IReadOnlyList<SessionSummary>> ListAsync(int limit = 20, CancellationToken ct = default)
    {
        var files = Directory.GetFiles(_baseDir, "*.json")
            .OrderByDescending(File.GetLastWriteTimeUtc)
            .Take(limit);

        var summaries = new List<SessionSummary>();

        foreach (var file in files)
        {
            try
            {
                var json = await File.ReadAllTextAsync(file, ct);
                var record = JsonSerializer.Deserialize<SessionRecord>(json);
                if (record is null) continue;

                summaries.Add(new SessionSummary
                {
                    SessionId = record.SessionId,
                    Requirement = record.Requirement.Length > 120
                        ? record.Requirement[..120] + "..."
                        : record.Requirement,
                    StartedAt = record.StartedAt,
                    CompletedAt = record.CompletedAt,
                    Success = record.Success,
                    TotalDuration = record.TotalDuration,
                    ArtifactCount = record.Artifacts.Count
                });
            }
            catch (Exception ex)
            {
                _logger.LogWarning(ex, "Skipping unreadable session file {File}", file);
            }
        }

        return summaries;
    }
}
