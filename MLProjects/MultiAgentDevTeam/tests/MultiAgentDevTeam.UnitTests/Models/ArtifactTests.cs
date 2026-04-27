using FluentAssertions;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Models;

public class ArtifactTests
{
    [Fact]
    public void Artifact_DefaultStatus_IsDraft()
    {
        // Arrange & Act
        var artifact = new Artifact { Type = ArtifactType.Requirements, Author = "PM" };

        // Assert
        artifact.Status.Should().Be(ArtifactStatus.Draft);
    }

    [Fact]
    public void Artifact_DefaultRevision_IsOne()
    {
        // Arrange & Act
        var artifact = new Artifact { Type = ArtifactType.Requirements, Author = "PM" };

        // Assert
        artifact.Revision.Should().Be(1);
    }

    [Fact]
    public void Artifact_IdIsUnique_PerInstance()
    {
        // Arrange & Act
        var a1 = new Artifact { Type = ArtifactType.Requirements, Author = "PM" };
        var a2 = new Artifact { Type = ArtifactType.Requirements, Author = "PM" };

        // Assert
        a1.Id.Should().NotBe(a2.Id);
    }

    [Fact]
    public void Artifact_StatusCanBeUpdated()
    {
        // Arrange
        var artifact = new Artifact { Type = ArtifactType.ReviewNotes, Author = "Reviewer" };

        // Act
        artifact.Status = ArtifactStatus.Approved;

        // Assert
        artifact.Status.Should().Be(ArtifactStatus.Approved);
    }

    [Fact]
    public void Artifact_FeedbackCanBeSet()
    {
        // Arrange
        var artifact = new Artifact { Type = ArtifactType.ReviewNotes, Author = "Reviewer" };

        // Act
        artifact.Feedback = "SQL injection risk on line 42";

        // Assert
        artifact.Feedback.Should().Be("SQL injection risk on line 42");
    }

    [Theory]
    [InlineData(ArtifactType.Requirements)]
    [InlineData(ArtifactType.Architecture)]
    [InlineData(ArtifactType.SourceCode)]
    [InlineData(ArtifactType.ReviewNotes)]
    [InlineData(ArtifactType.TestResults)]
    [InlineData(ArtifactType.SecurityReport)]
    [InlineData(ArtifactType.DeploymentConfig)]
    [InlineData(ArtifactType.Documentation)]
    public void Artifact_AllArtifactTypesAreValid(ArtifactType type)
    {
        // Arrange & Act
        var artifact = new Artifact { Type = type, Author = "Agent" };

        // Assert
        artifact.Type.Should().Be(type);
    }
}
