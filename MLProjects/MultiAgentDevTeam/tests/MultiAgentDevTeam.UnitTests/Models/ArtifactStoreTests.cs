using FluentAssertions;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Models;

public class ArtifactStoreTests
{
    [Fact]
    public void Set_NewArtifact_ShouldBeRetrievable()
    {
        // Arrange
        var store = new ArtifactStore();
        var artifact = new Artifact { Type = ArtifactType.Requirements, Content = "# Requirements", Author = "PM" };

        // Act
        store.Set(artifact);

        // Assert
        store.Has(ArtifactType.Requirements).Should().BeTrue();
        store.GetContent(ArtifactType.Requirements).Should().Be("# Requirements");
    }

    [Fact]
    public void Set_ExistingArtifact_ShouldOverwrite()
    {
        // Arrange
        var store = new ArtifactStore();
        store.Set(new Artifact { Type = ArtifactType.Requirements, Content = "v1", Author = "PM" });

        // Act
        store.Set(new Artifact { Type = ArtifactType.Requirements, Content = "v2", Author = "PM" });

        // Assert
        store.GetContent(ArtifactType.Requirements).Should().Be("v2");
    }

    [Fact]
    public void Has_MissingArtifact_ReturnsFalse()
    {
        // Arrange
        var store = new ArtifactStore();

        // Act & Assert
        store.Has(ArtifactType.Architecture).Should().BeFalse();
    }

    [Fact]
    public void GetContent_MissingArtifact_ReturnsEmptyString()
    {
        // Arrange
        var store = new ArtifactStore();

        // Act
        var result = store.GetContent(ArtifactType.SourceCode);

        // Assert
        result.Should().BeEmpty();
    }

    [Fact]
    public void Get_MissingArtifact_ReturnsNull()
    {
        // Arrange
        var store = new ArtifactStore();

        // Act
        var result = store.Get(ArtifactType.Documentation);

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public void All_WithMultipleArtifacts_ReturnsAll()
    {
        // Arrange
        var store = new ArtifactStore();
        store.Set(new Artifact { Type = ArtifactType.Requirements, Content = "req", Author = "PM" });
        store.Set(new Artifact { Type = ArtifactType.Architecture, Content = "arch", Author = "Architect" });

        // Act
        var all = store.All;

        // Assert
        all.Should().HaveCount(2);
        all.Keys.Should().Contain(ArtifactType.Requirements);
        all.Keys.Should().Contain(ArtifactType.Architecture);
    }

    [Fact]
    public void Set_UpdatesTimestamp()
    {
        // Arrange
        var store = new ArtifactStore();
        var artifact = new Artifact { Type = ArtifactType.Requirements, Content = "req", Author = "PM" };
        var before = DateTime.UtcNow;

        // Act
        store.Set(artifact);

        // Assert
        artifact.UpdatedAt.Should().BeOnOrAfter(before);
    }

    [Fact]
    public void Summary_WithArtifacts_ContainsArtifactTypes()
    {
        // Arrange
        var store = new ArtifactStore();
        store.Set(new Artifact { Type = ArtifactType.Requirements, Content = "req", Author = "PM" });

        // Act
        var summary = store.Summary();

        // Assert
        summary.Should().Contain("Requirements");
    }

    [Fact]
    public void SessionId_IsUniquePerInstance()
    {
        // Arrange & Act
        var store1 = new ArtifactStore();
        var store2 = new ArtifactStore();

        // Assert
        store1.SessionId.Should().NotBe(store2.SessionId);
    }
}
