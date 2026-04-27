using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Net;
using System.Net.Http.Json;
using System.Text.Json;
using Xunit;

namespace MultiAgentDevTeam.IntegrationTests;

/// <summary>
/// Integration tests for the SSE streaming endpoint: POST /api/run/stream
/// </summary>
public class StreamApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public StreamApiTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Replace real agents with fast mocks
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

                // Use a no-op session repository so no files are written
                var repoDescriptor = services.FirstOrDefault(d => d.ServiceType == typeof(ISessionRepository));
                if (repoDescriptor != null) services.Remove(repoDescriptor);
                var noopRepo = new Mock<ISessionRepository>();
                noopRepo.Setup(r => r.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
                    .Returns(Task.CompletedTask);
                services.AddSingleton(noopRepo.Object);

                Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-stream");
            });
        });
    }

    [Fact]
    public async Task POST_ApiRunStream_ValidRequest_Returns200()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a REST API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task POST_ApiRunStream_ValidRequest_ReturnsSSEContentType()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a REST API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);

        // Assert
        response.Content.Headers.ContentType?.MediaType.Should().Be("text/event-stream");
    }

    [Fact]
    public async Task POST_ApiRunStream_ValidRequest_YieldsDataEvents()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a REST API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);
        var body = await response.Content.ReadAsStringAsync();

        // Assert — SSE events are prefixed with "data: "
        body.Should().Contain("data:");
    }

    [Fact]
    public async Task POST_ApiRunStream_ValidRequest_EventsContainMessageField()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a REST API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);
        var body = await response.Content.ReadAsStringAsync();

        // Parse SSE events — each line is "data: {json}"
        var events = body.Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Where(l => l.StartsWith("data:"))
            .Select(l => l["data:".Length..].Trim())
            .ToList();

        // Assert
        events.Should().NotBeEmpty();
        foreach (var evt in events)
        {
            using var doc = JsonDocument.Parse(evt);
            doc.RootElement.TryGetProperty("message", out _).Should().BeTrue(
                $"every SSE event should have a 'message' field, but got: {evt}");
        }
    }

    [Fact]
    public async Task POST_ApiRunStream_ValidRequest_ContainsAgentStartedEvents()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a payment API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);
        var body = await response.Content.ReadAsStringAsync();

        // Assert — PM agent at minimum should appear in the stream
        body.Should().Contain("started");
    }

    [Fact]
    public async Task POST_ApiRunStream_EmptyRequirement_Returns400()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task POST_ApiRunStream_WithSkipAgents_ReturnsOk()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest
        {
            Requirement = "Build a REST API",
            SkipAgents = ["devops", "docs", "security", "qa", "reviewer"]
        };

        // Act
        var response = await client.PostAsJsonAsync("/api/run/stream", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }
}
