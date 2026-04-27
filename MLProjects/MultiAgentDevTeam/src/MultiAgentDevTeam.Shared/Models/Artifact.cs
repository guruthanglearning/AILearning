namespace MultiAgentDevTeam.Shared.Models;

public enum ArtifactStatus { Draft, Approved, Rejected }

public enum ArtifactType
{
    Requirements,
    Architecture,
    SourceCode,
    ReviewNotes,
    TestResults,
    SecurityReport,
    DeploymentConfig,
    Documentation
}

public class Artifact
{
    public Guid Id { get; init; } = Guid.NewGuid();
    public ArtifactType Type { get; init; }
    public string Content { get; set; } = string.Empty;
    public string Author { get; init; } = string.Empty;
    public ArtifactStatus Status { get; set; } = ArtifactStatus.Draft;
    public string? Feedback { get; set; }
    public int Revision { get; set; } = 1;
    public DateTime CreatedAt { get; init; } = DateTime.UtcNow;
    public DateTime UpdatedAt { get; set; } = DateTime.UtcNow;
}
