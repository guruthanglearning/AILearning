using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Net;
using System.Net.Http.Json;
using Xunit;

namespace MultiAgentDevTeam.IntegrationTests;

/// <summary>
/// Integration tests for the Orchestrator API endpoints.
/// Uses WebApplicationFactory with mocked agents — no real Claude API calls.
/// </summary>
public class OrchestratorApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public OrchestratorApiTests(WebApplicationFactory<Program> factory)
    {
        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Remove real agents and replace with mocks
                var agentDescriptors = services
                    .Where(d => d.ServiceType == typeof(IAgent))
                    .ToList();
                foreach (var d in agentDescriptors)
                    services.Remove(d);

                // Register mock agents for all artifact types
                foreach (var artifactType in Enum.GetValues<ArtifactType>())
                {
                    var type = artifactType;
                    var mock = new Mock<IAgent>();
                    mock.Setup(a => a.Name).Returns($"Mock{type}Agent");
                    mock.Setup(a => a.OutputType).Returns(type);

                    var responseContent = type == ArtifactType.ReviewNotes
                        ? "APPROVED - all good"
                        : $"Mock output for {type}";

                    mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                        .ReturnsAsync(AgentResponse.Ok(responseContent, $"Mock{type}Agent", TimeSpan.FromMilliseconds(10)));

                    services.AddTransient(_ => mock.Object);
                }

                // Set dummy API key so startup doesn't throw
                Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-integration");
            });
        });
    }

    [Fact]
    public async Task GET_Health_Returns200()
    {
        // Arrange
        var client = _factory.CreateClient();

        // Act
        var response = await client.GetAsync("/health");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task POST_ApiRun_ValidRequest_Returns200()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a TODO REST API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task POST_ApiRun_ValidRequest_ReturnsOrchestratorResponse()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a TODO REST API" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run", request);
        var result = await response.Content.ReadFromJsonAsync<OrchestratorResponse>();

        // Assert
        result.Should().NotBeNull();
        result!.Success.Should().BeTrue();
        result.SessionId.Should().NotBe(Guid.Empty);
        result.Artifacts.Should().NotBeEmpty();
    }

    [Fact]
    public async Task POST_ApiRun_EmptyRequirement_Returns400()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run", request);

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task POST_ApiRun_WithSkipAgents_Returns200()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest
        {
            Requirement = "Build a TODO REST API",
            SkipAgents = ["devops", "docs"]
        };

        // Act
        var response = await client.PostAsJsonAsync("/api/run", request);
        var result = await response.Content.ReadFromJsonAsync<OrchestratorResponse>();

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        result!.Success.Should().BeTrue();
        result.Artifacts.Should().NotContainKey("DeploymentConfig");
        result.Artifacts.Should().NotContainKey("Documentation");
    }

    [Fact]
    public async Task GET_SwaggerEndpoint_Returns200()
    {
        // Arrange
        var client = _factory.CreateClient();

        // Act
        var response = await client.GetAsync("/swagger/v1/swagger.json");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task POST_ApiRun_ResponseContainsAgentLog()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a login system" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run", request);
        var result = await response.Content.ReadFromJsonAsync<OrchestratorResponse>();

        // Assert
        result!.AgentLog.Should().NotBeEmpty();
    }

    [Fact]
    public async Task POST_ApiRun_ResponseContainsTotalDuration()
    {
        // Arrange
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a login system" };

        // Act
        var response = await client.PostAsJsonAsync("/api/run", request);
        var result = await response.Content.ReadFromJsonAsync<OrchestratorResponse>();

        // Assert
        result!.TotalDuration.Should().BeGreaterThan(TimeSpan.Zero);
    }

    [Fact]
    public async Task GET_Health_Returns200_WhenApiKeyInConfiguration()
    {
        // Arrange — API key provided via config (not env var) covers the first ?? branch in Program.cs
        var factory = _factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureAppConfiguration((_, config) =>
            {
                config.AddInMemoryCollection(new Dictionary<string, string?>
                {
                    ["AgentConfiguration:AnthropicApiKey"] = "test-key-from-config"
                });
            });
            builder.ConfigureServices(RegisterMockAgents);
        });

        // Act
        var response = await factory.CreateClient().GetAsync("/health");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GET_Health_Returns200_WhenRateLimitConfigured()
    {
        // Arrange — RateLimitRequestsPerMinute > 0 covers the true branch of the ternary in Program.cs
        var factory = _factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureAppConfiguration((_, config) =>
            {
                config.AddInMemoryCollection(new Dictionary<string, string?>
                {
                    ["AgentConfiguration:RateLimitRequestsPerMinute"] = "30"
                });
            });
            builder.ConfigureServices(RegisterMockAgents);
        });

        // Act
        var response = await factory.CreateClient().GetAsync("/health");

        // Assert
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task POST_ApiRunStream_EmptyRequirement_Returns400()
    {
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "" };

        var response = await client.PostAsJsonAsync("/api/run/stream", request);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task POST_ApiRunPartial_ValidRequest_Returns200()
    {
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest
        {
            Requirement = "Build a simple calculator API",
            SkipAgents = ["qa", "security", "devops", "docs"]
        };

        var response = await client.PostAsJsonAsync("/api/run/partial", request);
        var result = await response.Content.ReadFromJsonAsync<OrchestratorResponse>();

        response.StatusCode.Should().Be(HttpStatusCode.OK);
        result!.Success.Should().BeTrue();
    }

    [Fact]
    public async Task POST_ApiRunPartial_EmptyRequirement_Returns400()
    {
        var client = _factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "" };

        var response = await client.PostAsJsonAsync("/api/run/partial", request);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }

    [Fact]
    public async Task POST_ApiRun_FailedAgent_ReturnsProblem()
    {
        // Arrange — PM agent returns a failure response, triggering Results.Problem branch
        var factory = _factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                var agentDescriptors = services.Where(d => d.ServiceType == typeof(IAgent)).ToList();
                foreach (var d in agentDescriptors) services.Remove(d);

                foreach (var artifactType in Enum.GetValues<ArtifactType>())
                {
                    var type = artifactType;
                    var mock = new Mock<IAgent>();
                    mock.Setup(a => a.Name).Returns($"Mock{type}Agent");
                    mock.Setup(a => a.OutputType).Returns(type);

                    // PM agent fails — OrchestratorService catches and returns Success=false
                    if (type == ArtifactType.Requirements)
                        mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                            .ReturnsAsync(AgentResponse.Fail("PM agent crashed", $"Mock{type}Agent"));
                    else
                        mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                            .ReturnsAsync(AgentResponse.Ok($"Mock output for {type}", $"Mock{type}Agent", TimeSpan.FromMilliseconds(10)));

                    services.AddTransient(_ => mock.Object);
                }

                Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-integration");
            });
        });

        var response = await factory.CreateClient().PostAsJsonAsync("/api/run",
            new OrchestratorRequest { Requirement = "Build a TODO REST API" });

        // OrchestratorService.RunAsync returns Success=false → Results.Problem → 500
        response.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
    }

    [Fact]
    public async Task POST_ApiRun_RateLimitExceeded_Returns429()
    {
        // Arrange — set rate limit to 1 request/min with no queue
        var factory = new WebApplicationFactory<Program>().WithWebHostBuilder(builder =>
        {
            builder.ConfigureAppConfiguration((_, config) =>
                config.AddInMemoryCollection(new Dictionary<string, string?>
                {
                    ["AgentConfiguration:RateLimitRequestsPerMinute"] = "1"
                }));
            builder.ConfigureServices(RegisterMockAgents);
        });

        var client = factory.CreateClient();
        var request = new OrchestratorRequest { Requirement = "Build a TODO REST API" };

        // With PermitLimit=1 and QueueLimit=2, the 4th concurrent request is rejected immediately
        var tasks = Enumerable.Range(0, 4)
            .Select(_ => client.PostAsJsonAsync("/api/run", request))
            .ToList();

        // Wait up to 5 seconds — the 429 comes back immediately; queued ones may still be running
        await Task.WhenAny(Task.WhenAll(tasks), Task.Delay(TimeSpan.FromSeconds(5)));

        var completedStatuses = tasks
            .Where(t => t.IsCompletedSuccessfully)
            .Select(t => t.Result.StatusCode);

        completedStatuses.Should().Contain(HttpStatusCode.TooManyRequests);
    }

    private static void RegisterMockAgents(IServiceCollection services)
    {
        var agentDescriptors = services.Where(d => d.ServiceType == typeof(IAgent)).ToList();
        foreach (var d in agentDescriptors)
            services.Remove(d);

        foreach (var artifactType in Enum.GetValues<ArtifactType>())
        {
            var type = artifactType;
            var mock = new Mock<IAgent>();
            mock.Setup(a => a.Name).Returns($"Mock{type}Agent");
            mock.Setup(a => a.OutputType).Returns(type);
            var content = type == ArtifactType.ReviewNotes ? "APPROVED" : $"Mock output for {type}";
            mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                .ReturnsAsync(AgentResponse.Ok(content, $"Mock{type}Agent", TimeSpan.FromMilliseconds(10)));
            services.AddTransient(_ => mock.Object);
        }

        Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-integration");
    }
}
