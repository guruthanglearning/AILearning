namespace MultiAgentDevTeam.Shared.Models;

public class ArtifactStore
{
    public Guid SessionId { get; init; } = Guid.NewGuid();
    public string OriginalRequirement { get; set; } = string.Empty;
    public DateTime StartedAt { get; init; } = DateTime.UtcNow;

    private readonly Dictionary<ArtifactType, Artifact> _artifacts = new();

    public void Set(Artifact artifact)
    {
        artifact.UpdatedAt = DateTime.UtcNow;
        _artifacts[artifact.Type] = artifact;
    }

    public Artifact? Get(ArtifactType type) =>
        _artifacts.TryGetValue(type, out var artifact) ? artifact : null;

    public string GetContent(ArtifactType type) =>
        Get(type)?.Content ?? string.Empty;

    public bool Has(ArtifactType type) => _artifacts.ContainsKey(type);

    public IReadOnlyDictionary<ArtifactType, Artifact> All => _artifacts;

    public string Summary()
    {
        var lines = _artifacts.Select(kvp =>
            $"- {kvp.Key}: {kvp.Value.Status} (rev {kvp.Value.Revision})");
        return string.Join(Environment.NewLine, lines);
    }
}
