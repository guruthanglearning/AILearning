using Anthropic.SDK;
using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using MultiAgentDevTeam.UnitTests.Helpers;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Agents;

/// <summary>
/// Tests BaseAgent.RunAsync and BuildUserContent logic via a mock HTTP handler —
/// no real Anthropic API calls are made.
/// </summary>
public class BaseAgentTests
{
    private static (IAgent agent, MockHttpMessageHandler handler) CreateAgent(
        Type agentType,
        string responseText = "Mock response from Claude")
    {
        var handler = new MockHttpMessageHandler(responseText);
        var client = new AnthropicClient("test-key-not-used")
        {
            HttpClient = new HttpClient(handler)
        };

        var loggerType = typeof(NullLogger<>).MakeGenericType(agentType);
        var logger = Activator.CreateInstance(loggerType)!;
        var agent = (IAgent)Activator.CreateInstance(agentType, client, logger)!;

        return (agent, handler);
    }

    // ── RunAsync success path ─────────────────────────────────────────────────

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent))]
    [InlineData(typeof(MultiAgentDevTeam.ArchitectAgent.ArchitectAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent))]
    [InlineData(typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent))]
    [InlineData(typeof(MultiAgentDevTeam.QAAgent.QAAgent))]
    [InlineData(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DocsAgent.DocsAgent))]
    public async Task RunAsync_AllAgentTypes_ReturnSuccess(Type agentType)
    {
        // Arrange
        var (agent, _) = CreateAgent(agentType, "Hello from mock Claude");
        var request = new AgentRequest { Task = "Do something useful" };

        // Act
        var response = await agent.RunAsync(request);

        // Assert
        response.Success.Should().BeTrue();
        response.ErrorMessage.Should().BeNull();
        response.AgentName.Should().NotBeNullOrEmpty();
    }

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent))]
    [InlineData(typeof(MultiAgentDevTeam.ArchitectAgent.ArchitectAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent))]
    [InlineData(typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent))]
    [InlineData(typeof(MultiAgentDevTeam.QAAgent.QAAgent))]
    [InlineData(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DocsAgent.DocsAgent))]
    public async Task RunAsync_AllAgentTypes_ReturnsExpectedContent(Type agentType)
    {
        // Arrange
        var (agent, _) = CreateAgent(agentType, "This is the response content");
        var request = new AgentRequest { Task = "Generate output" };

        // Act
        var response = await agent.RunAsync(request);

        // Assert
        response.Content.Should().Be("This is the response content");
    }

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent))]
    public async Task RunAsync_RecordsDuration(Type agentType)
    {
        // Arrange
        var (agent, _) = CreateAgent(agentType);
        var request = new AgentRequest { Task = "Generate output" };

        // Act
        var response = await agent.RunAsync(request);

        // Assert
        response.Duration.Should().BeGreaterThanOrEqualTo(TimeSpan.Zero);
    }

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent))]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent))]
    public async Task RunAsync_SetsAgentName(Type agentType)
    {
        // Arrange
        var (agent, _) = CreateAgent(agentType);
        var request = new AgentRequest { Task = "Do something" };

        // Act
        var response = await agent.RunAsync(request);

        // Assert
        response.AgentName.Should().Be(agent.Name);
    }

    // ── HTTP request count ────────────────────────────────────────────────────

    [Fact]
    public async Task RunAsync_MakesExactlyOneHttpCall()
    {
        // Arrange
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.PMAgent.PMAgent));
        var request = new AgentRequest { Task = "Extract requirements" };

        // Act
        await agent.RunAsync(request);

        // Assert
        handler.CallCount.Should().Be(1);
    }

    // ── BuildUserContent — tested indirectly via HTTP request body ────────────

    [Fact]
    public async Task RunAsync_WithContext_SendsContextInRequest()
    {
        // Arrange
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.PMAgent.PMAgent));
        var request = new AgentRequest
        {
            Task = "Design the system",
            Context = new Dictionary<string, string>
            {
                ["Requirements"] = "User needs a TODO app"
            }
        };

        // Act
        await agent.RunAsync(request);

        // Assert — verify the HTTP request body contained the context
        var requestBody = await handler.LastRequest!.Content!.ReadAsStringAsync();
        requestBody.Should().Contain("User needs a TODO app");
    }

    [Fact]
    public async Task RunAsync_WithPreviousFeedback_SendsFeedbackInRequest()
    {
        // Arrange
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent));
        var request = new AgentRequest
        {
            Task = "Fix the code",
            PreviousFeedback = "Missing null checks on line 42"
        };

        // Act
        await agent.RunAsync(request);

        // Assert
        var requestBody = await handler.LastRequest!.Content!.ReadAsStringAsync();
        requestBody.Should().Contain("Missing null checks on line 42");
    }

    [Fact]
    public async Task RunAsync_WithNoContext_OnlySendsTask()
    {
        // Arrange
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.PMAgent.PMAgent));
        var request = new AgentRequest { Task = "Extract requirements from this request" };

        // Act
        await agent.RunAsync(request);

        // Assert
        var requestBody = await handler.LastRequest!.Content!.ReadAsStringAsync();
        requestBody.Should().Contain("Extract requirements from this request");
    }

    [Fact]
    public async Task RunAsync_WithMultipleContextItems_SendsAllInRequest()
    {
        // Arrange
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.QAAgent.QAAgent));
        var request = new AgentRequest
        {
            Task = "Write tests",
            Context = new Dictionary<string, string>
            {
                ["Requirements"] = "User stories content",
                ["SourceCode"] = "public class OrderService {}"
            }
        };

        // Act
        await agent.RunAsync(request);

        // Assert
        var requestBody = await handler.LastRequest!.Content!.ReadAsStringAsync();
        requestBody.Should().Contain("User stories content");
        requestBody.Should().Contain("public class OrderService {}");
    }

    // ── Error handling ────────────────────────────────────────────────────────

    [Fact]
    public async Task RunAsync_WhenResponseHasNoTextContent_ReturnsEmptyContent()
    {
        // Arrange — response with empty content array exercises the ?. ?? string.Empty branch
        var handler = MockHttpMessageHandler.WithNoTextContent();
        var client = new AnthropicClient("test-key-not-used")
        {
            HttpClient = new HttpClient(handler)
        };
        var agent = (IAgent)Activator.CreateInstance(
            typeof(MultiAgentDevTeam.PMAgent.PMAgent),
            client,
            NullLogger<MultiAgentDevTeam.PMAgent.PMAgent>.Instance)!;
        var request = new AgentRequest { Task = "Do something" };

        // Act
        var response = await agent.RunAsync(request);

        // Assert
        response.Success.Should().BeTrue();
        response.Content.Should().BeEmpty();
    }

    [Fact]
    public async Task RunAsync_WhenHttpFails_ReturnsFailure()
    {
        // Arrange
        var handler = new MockHttpMessageHandler("error", System.Net.HttpStatusCode.InternalServerError);
        var client = new AnthropicClient("test-key") { HttpClient = new HttpClient(handler) };
        var agent = (IAgent)Activator.CreateInstance(
            typeof(MultiAgentDevTeam.PMAgent.PMAgent),
            client,
            NullLogger<MultiAgentDevTeam.PMAgent.PMAgent>.Instance)!;

        var request = new AgentRequest { Task = "Do something" };

        // Act
        var response = await agent.RunAsync(request);

        // Assert
        response.Success.Should().BeFalse();
        response.ErrorMessage.Should().NotBeNullOrEmpty();
    }
}
