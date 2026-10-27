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
/// Verifies that agent failures surface with a meaningful HTTP status (502/503/504)
/// instead of a generic 500 — e.g. a rejected Anthropic API key.
/// </summary>
public class PipelineFailureApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly WebApplicationFactory<Program> _factory;

    public PipelineFailureApiTests(WebApplicationFactory<Program> factory) => _factory = factory;

    private HttpClient CreateClientWithFailingPm(AgentFailureKind kind) =>
        _factory.WithWebHostBuilder(builder => builder.ConfigureServices(services =>
        {
            var agentDescriptors = services.Where(d => d.ServiceType == typeof(IAgent)).ToList();
            foreach (var d in agentDescriptors) services.Remove(d);

            foreach (var artifactType in Enum.GetValues<ArtifactType>())
            {
                var type = artifactType;
                var mock = new Mock<IAgent>();
                mock.Setup(a => a.Name).Returns($"Mock{type}Agent");
                mock.Setup(a => a.OutputType).Returns(type);

                if (type == ArtifactType.Requirements)
                    mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                        .ReturnsAsync(AgentResponse.Fail("invalid x-api-key", $"Mock{type}Agent", kind));
                else
                    mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                        .ReturnsAsync(AgentResponse.Ok("APPROVED", $"Mock{type}Agent", TimeSpan.FromMilliseconds(5)));

                services.AddTransient(_ => mock.Object);
            }

            // No-op session repository so no files are written
            var repoDescriptor = services.FirstOrDefault(d => d.ServiceType == typeof(ISessionRepository));
            if (repoDescriptor != null) services.Remove(repoDescriptor);
            var noopRepo = new Mock<ISessionRepository>();
            noopRepo.Setup(r => r.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
                .Returns(Task.CompletedTask);
            services.AddSingleton(noopRepo.Object);

            Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-failure");
        })).CreateClient();

    [Theory]
    [InlineData(AgentFailureKind.Authentication, HttpStatusCode.BadGateway)]
    [InlineData(AgentFailureKind.Upstream, HttpStatusCode.BadGateway)]
    [InlineData(AgentFailureKind.RateLimited, HttpStatusCode.ServiceUnavailable)]
    [InlineData(AgentFailureKind.Timeout, HttpStatusCode.GatewayTimeout)]
    [InlineData(AgentFailureKind.Internal, HttpStatusCode.InternalServerError)]
    public async Task POST_ApiRun_AgentFailure_ReturnsMappedStatus(AgentFailureKind kind, HttpStatusCode expected)
    {
        var response = await CreateClientWithFailingPm(kind)
            .PostAsJsonAsync("/api/run", new OrchestratorRequest { Requirement = "Build a TODO API" });

        response.StatusCode.Should().Be(expected);
    }

    [Fact]
    public async Task POST_ApiRunPartial_AgentFailure_ReturnsMappedStatus()
    {
        var response = await CreateClientWithFailingPm(AgentFailureKind.Timeout)
            .PostAsJsonAsync("/api/run/partial", new OrchestratorRequest { Requirement = "Build a TODO API" });

        response.StatusCode.Should().Be(HttpStatusCode.GatewayTimeout);
    }

    [Fact]
    public async Task POST_ApiRun_RejectedApiKey_ReturnsActionableProblemDetails()
    {
        var response = await CreateClientWithFailingPm(AgentFailureKind.Authentication)
            .PostAsJsonAsync("/api/run", new OrchestratorRequest { Requirement = "Build a TODO API" });

        response.Content.Headers.ContentType!.MediaType.Should().Be("application/problem+json");
        using var problem = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var root = problem.RootElement;
        root.GetProperty("status").GetInt32().Should().Be(502);
        root.GetProperty("title").GetString().Should().Be("Anthropic API key rejected");
        root.GetProperty("detail").GetString().Should().Contain("AnthropicApiKey").And.Contain("invalid x-api-key");
        root.GetProperty("failureKind").GetString().Should().Be("Authentication");
        root.GetProperty("sessionId").GetString().Should().NotBeNullOrEmpty();
    }

    [Fact]
    public async Task POST_ApiRunStream_RejectedApiKey_StreamsReadableFailureMessage()
    {
        var response = await CreateClientWithFailingPm(AgentFailureKind.Authentication)
            .PostAsJsonAsync("/api/run/stream", new OrchestratorRequest { Requirement = "Build a TODO API" });

        // Headers are flushed before the pipeline runs, so the stream itself stays 200 —
        // the failure is reported as the final SSE message instead
        response.StatusCode.Should().Be(HttpStatusCode.OK);
        var messages = (await response.Content.ReadAsStringAsync())
            .Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Where(l => l.StartsWith("data:"))
            .Select(l => JsonDocument.Parse(l["data:".Length..]).RootElement.GetProperty("message").GetString()!)
            .ToList();

        messages.Last().Should().StartWith("🛑 Pipeline failed:").And.Contain("rejected the configured API key");
    }
}
