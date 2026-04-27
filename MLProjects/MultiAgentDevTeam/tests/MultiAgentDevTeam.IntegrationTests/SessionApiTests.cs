using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Net;
using System.Net.Http.Json;
using Xunit;

namespace MultiAgentDevTeam.IntegrationTests;

/// <summary>
/// Integration tests for session management endpoints:
/// GET /api/sessions and GET /api/sessions/{id}
/// </summary>
public class SessionApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;
    private readonly Mock<ISessionRepository> _sessionRepo;

    public SessionApiTests(WebApplicationFactory<Program> factory)
    {
        _sessionRepo = new Mock<ISessionRepository>();

        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real agents with mocks
                var agentDescriptors = services.Where(d => d.ServiceType == typeof(IAgent)).ToList();
                foreach (var d in agentDescriptors) services.Remove(d);

                foreach (var artifactType in Enum.GetValues<ArtifactType>())
                {
                    var type = artifactType;
                    var mock = new Mock<IAgent>();
                    mock.Setup(a => a.Name).Returns($"Mock{type}Agent");
                    mock.Setup(a => a.OutputType).Returns(type);
                    var content = type == ArtifactType.ReviewNotes ? "APPROVED" : $"Mock {type}";
                    mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                        .ReturnsAsync(AgentResponse.Ok(content, $"Mock{type}Agent", TimeSpan.FromMilliseconds(5)));
                    services.AddTransient(_ => mock.Object);
                }

                // Replace FileSessionRepository with our controllable mock
                var repoDescriptor = services.FirstOrDefault(d => d.ServiceType == typeof(ISessionRepository));
                if (repoDescriptor != null) services.Remove(repoDescriptor);
                services.AddSingleton(_sessionRepo.Object);

                Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-sessions");
            });
        });
    }

    // ── GET /api/sessions ──────────────────────────────────────────────────────

    [Fact]
    public async Task GET_ApiSessions_Returns200()
    {
        // Arrange
        _sessionRepo.Setup(r => r.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>());

        // Act
        var response = await _factory.CreateClient().GetAsync("/api/sessions");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GET_ApiSessions_EmptyRepo_ReturnsEmptyArray()
    {
        // Arrange
        _sessionRepo.Setup(r => r.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>());

        // Act
        var response = await _factory.CreateClient().GetAsync("/api/sessions");
        var list = await response.Content.ReadFromJsonAsync<List<SessionSummary>>();

        // Assert
        list.Should().NotBeNull().And.BeEmpty();
    }

    [Fact]
    public async Task GET_ApiSessions_WithRecords_ReturnsSummaries()
    {
        // Arrange
        var summaries = new List<SessionSummary>
        {
            new() { SessionId = Guid.NewGuid(), Requirement = "Build a TODO app", Success = true, ArtifactCount = 8 },
            new() { SessionId = Guid.NewGuid(), Requirement = "Build a login system", Success = true, ArtifactCount = 6 }
        };
        _sessionRepo.Setup(r => r.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(summaries);

        // Act
        var response = await _factory.CreateClient().GetAsync("/api/sessions");
        var list = await response.Content.ReadFromJsonAsync<List<SessionSummary>>();

        // Assert
        list.Should().HaveCount(2);
        list![0].Requirement.Should().Be("Build a TODO app");
    }

    [Fact]
    public async Task GET_ApiSessions_PassesLimitQueryParam()
    {
        // Arrange
        _sessionRepo.Setup(r => r.ListAsync(5, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>())
            .Verifiable();

        // Act
        await _factory.CreateClient().GetAsync("/api/sessions?limit=5");

        // Assert
        _sessionRepo.Verify(r => r.ListAsync(5, It.IsAny<CancellationToken>()), Times.Once);
    }

    // ── GET /api/sessions/{id} ─────────────────────────────────────────────────

    [Fact]
    public async Task GET_ApiSessions_ById_NotFound_Returns404()
    {
        // Arrange
        var id = Guid.NewGuid();
        _sessionRepo.Setup(r => r.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync((SessionRecord?)null);

        // Act
        var response = await _factory.CreateClient().GetAsync($"/api/sessions/{id}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.NotFound);
    }

    [Fact]
    public async Task GET_ApiSessions_ById_Found_Returns200()
    {
        // Arrange
        var id = Guid.NewGuid();
        var record = BuildRecord(id);
        _sessionRepo.Setup(r => r.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(record);

        // Act
        var response = await _factory.CreateClient().GetAsync($"/api/sessions/{id}");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GET_ApiSessions_ById_ReturnsCorrectRecord()
    {
        // Arrange
        var id = Guid.NewGuid();
        var record = BuildRecord(id, "Build a payment gateway");
        _sessionRepo.Setup(r => r.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(record);

        // Act
        var response = await _factory.CreateClient().GetAsync($"/api/sessions/{id}");
        var result = await response.Content.ReadFromJsonAsync<SessionRecord>();

        // Assert
        result.Should().NotBeNull();
        result!.SessionId.Should().Be(id);
        result.Requirement.Should().Be("Build a payment gateway");
        result.Success.Should().BeTrue();
    }

    [Fact]
    public async Task GET_ApiSessions_ById_ReturnsArtifacts()
    {
        // Arrange
        var id = Guid.NewGuid();
        var record = BuildRecord(id);
        record.Artifacts["Requirements"] = "# User Stories";
        record.Artifacts["SourceCode"] = "public class Foo {}";
        _sessionRepo.Setup(r => r.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(record);

        // Act
        var response = await _factory.CreateClient().GetAsync($"/api/sessions/{id}");
        var result = await response.Content.ReadFromJsonAsync<SessionRecord>();

        // Assert
        result!.Artifacts.Should().ContainKey("Requirements");
        result.Artifacts.Should().ContainKey("SourceCode");
    }

    // ── Session persisted after /api/run ──────────────────────────────────────

    [Fact]
    public async Task POST_ApiRun_PersistsSessionToRepository()
    {
        // Arrange
        _sessionRepo.Setup(r => r.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask)
            .Verifiable();
        _sessionRepo.Setup(r => r.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>());

        var request = new OrchestratorRequest { Requirement = "Build a notification service" };

        // Act
        await _factory.CreateClient().PostAsJsonAsync("/api/run", request);

        // Assert — SaveAsync was called once after pipeline completed
        _sessionRepo.Verify(r => r.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()), Times.Once);
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static SessionRecord BuildRecord(Guid id, string requirement = "Build something") =>
        new()
        {
            SessionId = id,
            Requirement = requirement,
            StartedAt = DateTime.UtcNow.AddMinutes(-2),
            CompletedAt = DateTime.UtcNow,
            Success = true,
            Artifacts = new Dictionary<string, string>(),
            AgentLog = new List<string>(),
            TotalDuration = "00:02:00"
        };
}
