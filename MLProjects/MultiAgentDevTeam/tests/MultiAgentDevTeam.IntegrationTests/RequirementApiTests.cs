using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Net.Http.Json;
using System.Text.Json;
using Xunit;

namespace MultiAgentDevTeam.IntegrationTests;

/// <summary>Requirement results through the HTTP API: POST /api/run and POST /api/run/stream.</summary>
public class RequirementApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private static readonly Dictionary<ArtifactType, string> Outputs = new()
    {
        [ArtifactType.Requirements] = """
            ```requirements-checklist
            [{"id": "FR-1", "text": "Print Hello, World!", "kind": "code"},
             {"id": "FR-2", "text": "Run the app", "kind": "action"}]
            ```
            """,
        [ArtifactType.SourceCode] = "## Requirement Coverage\n- FR-1: Program.cs\n- FR-2: N/A - action",
        [ArtifactType.ReviewNotes] = "APPROVED",
        [ArtifactType.VerificationReport] = """
            ```verification-results
            [{"id": "FR-1", "status": "passed", "evidence": "Program.cs"}, {"id": "FR-2", "status": "manual"}]
            ```
            """
    };

    private readonly WebApplicationFactory<Program> _factory;

    public RequirementApiTests(WebApplicationFactory<Program> factory)
    {
        Environment.SetEnvironmentVariable("ANTHROPIC_API_KEY", "test-key-requirements");
        _factory = factory.WithWebHostBuilder(builder => builder.ConfigureServices(services =>
        {
            foreach (var d in services.Where(d => d.ServiceType == typeof(IAgent)).ToList())
                services.Remove(d);

            foreach (var type in Enum.GetValues<ArtifactType>())
            {
                var mock = new Mock<IAgent>();
                mock.Setup(a => a.Name).Returns($"Mock{type}Agent");
                mock.Setup(a => a.OutputType).Returns(type);
                var content = Outputs.GetValueOrDefault(type, $"Mock {type}");
                mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
                    .ReturnsAsync(AgentResponse.Ok(content, $"Mock{type}Agent", TimeSpan.FromMilliseconds(5)));
                services.AddTransient(_ => mock.Object);
            }

            foreach (var d in services.Where(d => d.ServiceType == typeof(ISessionRepository)).ToList())
                services.Remove(d);
            var repo = new Mock<ISessionRepository>();
            repo.Setup(r => r.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>())).Returns(Task.CompletedTask);
            services.AddSingleton(repo.Object);
        }));
    }

    [Fact]
    public async Task POST_ApiRun_ReturnsRequirementResults()
    {
        var response = await _factory.CreateClient()
            .PostAsJsonAsync("/api/run", new OrchestratorRequest { Requirement = "Hello World, then run it" });

        using var body = JsonDocument.Parse(await response.Content.ReadAsStringAsync());
        var requirements = body.RootElement.GetProperty("requirements");
        requirements.GetArrayLength().Should().Be(2);
        requirements[0].GetProperty("id").GetString().Should().Be("FR-1");
        requirements[0].GetProperty("status").GetString().Should().Be("Passed");
        requirements[0].GetProperty("kind").GetString().Should().Be("Code");
        requirements[1].GetProperty("status").GetString().Should().Be("Manual");
        body.RootElement.GetProperty("requirementsMet").GetBoolean().Should().BeTrue();
    }

    [Fact]
    public async Task POST_ApiRunStream_StartsWithSessionIdAndEndsWithRequirementLines()
    {
        var response = await _factory.CreateClient()
            .PostAsJsonAsync("/api/run/stream", new OrchestratorRequest { Requirement = "Hello World, then run it" });

        var messages = (await response.Content.ReadAsStringAsync())
            .Split('\n', StringSplitOptions.RemoveEmptyEntries)
            .Where(l => l.StartsWith("data:"))
            .Select(l => JsonDocument.Parse(l["data:".Length..]).RootElement.GetProperty("message").GetString()!)
            .ToList();

        messages[0].Should().StartWith("🆔 Session ");
        messages.Should().Contain("📋 Requirement check: 1 passed, 1 manual");
        messages.Should().Contain(m => m.StartsWith("🖐️ FR-2 [action] Run the app"));
    }

    [Fact]
    public void Host_RegistersTheVerifierAgent()
    {
        using var factory = new WebApplicationFactory<Program>();

        var agents = factory.Services.GetServices<IAgent>();

        agents.Should().Contain(a => a.OutputType == ArtifactType.VerificationReport && a.Name == "Acceptance Verifier");
    }
}
