using Anthropic.SDK;
using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using MultiAgentDevTeam.Shared.Agents;
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

    // ── Failure classification ────────────────────────────────────────────────

    [Theory]
    [InlineData(System.Net.HttpStatusCode.Unauthorized, AgentFailureKind.Authentication)]
    [InlineData(System.Net.HttpStatusCode.TooManyRequests, AgentFailureKind.RateLimited)]
    [InlineData(System.Net.HttpStatusCode.InternalServerError, AgentFailureKind.Upstream)]
    [InlineData(System.Net.HttpStatusCode.ServiceUnavailable, AgentFailureKind.Upstream)]
    public async Task RunAsync_WhenApiReturnsErrorStatus_ClassifiesFailure(System.Net.HttpStatusCode status, AgentFailureKind expected)
    {
        // Arrange
        var handler = new MockHttpMessageHandler("error", status);
        var client = new AnthropicClient("test-key") { HttpClient = new HttpClient(handler) };
        var agent = (IAgent)Activator.CreateInstance(
            typeof(MultiAgentDevTeam.PMAgent.PMAgent),
            client,
            NullLogger<MultiAgentDevTeam.PMAgent.PMAgent>.Instance)!;

        // Act
        var response = await agent.RunAsync(new AgentRequest { Task = "Do something" });

        // Assert
        response.Success.Should().BeFalse();
        response.FailureKind.Should().Be(expected);
    }

    [Fact]
    public void ClassifyFailure_AuthenticationException_IsAuthentication() =>
        BaseAgent.ClassifyFailure(new System.Security.Authentication.AuthenticationException("invalid x-api-key"))
            .Should().Be(AgentFailureKind.Authentication);

    [Fact]
    public void ClassifyFailure_Http403_IsAuthentication() =>
        BaseAgent.ClassifyFailure(new HttpRequestException("forbidden", null, System.Net.HttpStatusCode.Forbidden))
            .Should().Be(AgentFailureKind.Authentication);

    [Theory]
    [InlineData("Error at https://api.anthropic.com/v1/messages with HTTP status code: TooManyRequests. Content: {}", AgentFailureKind.RateLimited)]
    [InlineData("Error at https://api.anthropic.com/v1/messages with HTTP status code: Forbidden. Content: {}", AgentFailureKind.Authentication)]
    [InlineData("Error at https://api.anthropic.com/v1/messages with HTTP status code: BadGateway. Content: {}", AgentFailureKind.Upstream)]
    [InlineData("with HTTP status code: NotARealStatus. Content: {}", AgentFailureKind.Upstream)]
    [InlineData("connection reset", AgentFailureKind.Upstream)]
    public void ClassifyFailure_SdkHttpError_ReadsStatusFromMessage(string message, AgentFailureKind expected) =>
        // Anthropic.SDK leaves StatusCode null and only reports the status in the message
        BaseAgent.ClassifyFailure(new HttpRequestException(message)).Should().Be(expected);

    [Fact]
    public void ClassifyFailure_HttpClientTimeout_IsTimeout() =>
        // HttpClient.Timeout elapsing throws TaskCanceledException while the caller's token is not cancelled
        BaseAgent.ClassifyFailure(new TaskCanceledException("The request was canceled due to the configured HttpClient.Timeout"))
            .Should().Be(AgentFailureKind.Timeout);

    [Fact]
    public void ClassifyFailure_TimeoutException_IsTimeout() =>
        BaseAgent.ClassifyFailure(new TimeoutException()).Should().Be(AgentFailureKind.Timeout);

    [Fact]
    public void ClassifyFailure_CallerCancelled_IsNotTimeout()
    {
        using var cts = new CancellationTokenSource();
        cts.Cancel();

        BaseAgent.ClassifyFailure(new OperationCanceledException(cts.Token), cts.Token)
            .Should().Be(AgentFailureKind.Internal);
    }

    [Fact]
    public void ClassifyFailure_UnknownException_IsInternal() =>
        BaseAgent.ClassifyFailure(new InvalidOperationException("bug")).Should().Be(AgentFailureKind.Internal);
}
