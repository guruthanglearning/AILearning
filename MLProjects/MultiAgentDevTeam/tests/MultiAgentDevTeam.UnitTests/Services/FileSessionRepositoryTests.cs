using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Orchestrator.Services;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Services;

public class FileSessionRepositoryTests : IDisposable
{
    private readonly string _tempDir;
    private readonly FileSessionRepository _repo;

    public FileSessionRepositoryTests()
    {
        _tempDir = Path.Combine(Path.GetTempPath(), $"madt_tests_{Guid.NewGuid():N}");
        var config = Options.Create(new AgentConfiguration { SessionStoragePath = _tempDir });
        _repo = new FileSessionRepository(config, NullLogger<FileSessionRepository>.Instance);
    }

    public void Dispose()
    {
        if (Directory.Exists(_tempDir))
            Directory.Delete(_tempDir, recursive: true);
    }

    // ── SaveAsync ─────────────────────────────────────────────────────────────

    [Fact]
    public async Task SaveAsync_CreatesJsonFile()
    {
        // Arrange
        var record = BuildRecord();

        // Act
        await _repo.SaveAsync(record);

        // Assert
        var file = Path.Combine(_tempDir, $"{record.SessionId}.json");
        File.Exists(file).Should().BeTrue();
    }

    [Fact]
    public async Task SaveAsync_FileContainsSessionId()
    {
        // Arrange
        var record = BuildRecord();

        // Act
        await _repo.SaveAsync(record);

        // Assert
        var file = Path.Combine(_tempDir, $"{record.SessionId}.json");
        var json = await File.ReadAllTextAsync(file);
        json.Should().Contain(record.SessionId.ToString());
    }

    [Fact]
    public async Task SaveAsync_FileContainsRequirement()
    {
        // Arrange
        var record = BuildRecord(requirement: "Build a TODO API");

        // Act
        await _repo.SaveAsync(record);

        // Assert
        var file = Path.Combine(_tempDir, $"{record.SessionId}.json");
        var json = await File.ReadAllTextAsync(file);
        json.Should().Contain("Build a TODO API");
    }

    // ── GetAsync ──────────────────────────────────────────────────────────────

    [Fact]
    public async Task GetAsync_ExistingSession_ReturnsRecord()
    {
        // Arrange
        var record = BuildRecord(requirement: "Build an auth system");
        await _repo.SaveAsync(record);

        // Act
        var retrieved = await _repo.GetAsync(record.SessionId);

        // Assert
        retrieved.Should().NotBeNull();
        retrieved!.SessionId.Should().Be(record.SessionId);
        retrieved.Requirement.Should().Be("Build an auth system");
        retrieved.Success.Should().BeTrue();
    }

    [Fact]
    public async Task GetAsync_NonExistentSession_ReturnsNull()
    {
        // Act
        var result = await _repo.GetAsync(Guid.NewGuid());

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task GetAsync_PreservesArtifacts()
    {
        // Arrange
        var record = BuildRecord();
        record.Artifacts["Requirements"] = "# User stories here";
        record.Artifacts["SourceCode"] = "public class Foo {}";
        await _repo.SaveAsync(record);

        // Act
        var retrieved = await _repo.GetAsync(record.SessionId);

        // Assert
        retrieved!.Artifacts.Should().ContainKey("Requirements");
        retrieved.Artifacts["Requirements"].Should().Be("# User stories here");
        retrieved.Artifacts.Should().ContainKey("SourceCode");
    }

    [Fact]
    public async Task GetAsync_PreservesAgentLog()
    {
        // Arrange
        var record = BuildRecord();
        record.AgentLog.Add("🤖 PM Agent started");
        record.AgentLog.Add("✅ PM Agent completed in 1.2s");
        await _repo.SaveAsync(record);

        // Act
        var retrieved = await _repo.GetAsync(record.SessionId);

        // Assert
        retrieved!.AgentLog.Should().HaveCount(2);
        retrieved.AgentLog[0].Should().Contain("PM Agent started");
    }

    [Fact]
    public async Task GetAsync_FailedSession_PreservesErrorMessage()
    {
        // Arrange
        var record = BuildRecord(success: false, errorMessage: "API timeout");
        await _repo.SaveAsync(record);

        // Act
        var retrieved = await _repo.GetAsync(record.SessionId);

        // Assert
        retrieved!.Success.Should().BeFalse();
        retrieved.ErrorMessage.Should().Be("API timeout");
    }

    // ── ListAsync ─────────────────────────────────────────────────────────────

    [Fact]
    public async Task ListAsync_EmptyDirectory_ReturnsEmptyList()
    {
        // Act
        var list = await _repo.ListAsync();

        // Assert
        list.Should().BeEmpty();
    }

    [Fact]
    public async Task ListAsync_MultipleRecords_ReturnsAll()
    {
        // Arrange
        await _repo.SaveAsync(BuildRecord());
        await _repo.SaveAsync(BuildRecord());
        await _repo.SaveAsync(BuildRecord());

        // Act
        var list = await _repo.ListAsync();

        // Assert
        list.Should().HaveCount(3);
    }

    [Fact]
    public async Task ListAsync_RespectsLimit()
    {
        // Arrange
        for (int i = 0; i < 5; i++)
            await _repo.SaveAsync(BuildRecord());

        // Act
        var list = await _repo.ListAsync(limit: 2);

        // Assert
        list.Should().HaveCount(2);
    }

    [Fact]
    public async Task ListAsync_SummaryTruncatesLongRequirements()
    {
        // Arrange
        var longReq = new string('A', 200);
        var record = BuildRecord(requirement: longReq);
        await _repo.SaveAsync(record);

        // Act
        var list = await _repo.ListAsync();

        // Assert
        list[0].Requirement.Length.Should().BeLessThanOrEqualTo(123); // 120 + "..."
        list[0].Requirement.Should().EndWith("...");
    }

    [Fact]
    public async Task ListAsync_ShortRequirement_NotTruncated()
    {
        // Arrange
        var record = BuildRecord(requirement: "Build a TODO API");
        await _repo.SaveAsync(record);

        // Act
        var list = await _repo.ListAsync();

        // Assert
        list[0].Requirement.Should().Be("Build a TODO API");
    }

    [Fact]
    public async Task ListAsync_SummaryContainsCorrectArtifactCount()
    {
        // Arrange
        var record = BuildRecord();
        record.Artifacts["Requirements"] = "req";
        record.Artifacts["SourceCode"] = "code";
        await _repo.SaveAsync(record);

        // Act
        var list = await _repo.ListAsync();

        // Assert
        list[0].ArtifactCount.Should().Be(2);
    }

    [Fact]
    public async Task ListAsync_SkipsCorruptedFiles_ReturnsValidRecords()
    {
        // Arrange — write one valid and one corrupted file
        var valid = BuildRecord();
        await _repo.SaveAsync(valid);
        await File.WriteAllTextAsync(Path.Combine(_tempDir, $"{Guid.NewGuid()}.json"), "NOT_VALID_JSON{{{{");

        // Act
        var list = await _repo.ListAsync();

        // Assert — only the valid record is returned
        list.Should().HaveCount(1);
        list[0].SessionId.Should().Be(valid.SessionId);
    }

    [Fact]
    public void Constructor_WithRelativePath_ResolvesFromBaseDirectory()
    {
        // Arrange — relative path exercises the !Path.IsPathRooted branch
        var relativePath = $"test_sessions_{Guid.NewGuid():N}";
        var config = Options.Create(new AgentConfiguration { SessionStoragePath = relativePath });

        // Act
        var repo = new FileSessionRepository(config, NullLogger<FileSessionRepository>.Instance);
        var expectedPath = Path.Combine(AppContext.BaseDirectory, relativePath);

        // Assert
        Directory.Exists(expectedPath).Should().BeTrue();

        // Cleanup
        if (Directory.Exists(expectedPath))
            Directory.Delete(expectedPath, recursive: true);
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static SessionRecord BuildRecord(
        string requirement = "Build something",
        bool success = true,
        string? errorMessage = null) =>
        new()
        {
            SessionId = Guid.NewGuid(),
            Requirement = requirement,
            StartedAt = DateTime.UtcNow.AddMinutes(-5),
            CompletedAt = DateTime.UtcNow,
            Success = success,
            Artifacts = new Dictionary<string, string>(),
            AgentLog = new List<string>(),
            TotalDuration = "00:05:00",
            ErrorMessage = errorMessage
        };
}
