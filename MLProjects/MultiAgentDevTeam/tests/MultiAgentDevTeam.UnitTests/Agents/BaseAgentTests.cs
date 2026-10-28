using FluentAssertions;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using MultiAgentDevTeam.UnitTests.Helpers;
using System.Text.Json;
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
        return (AgentFactory.Create(agentType, handler), handler);
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
        var requestBody = handler.LastRequestBody!;
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
        var requestBody = handler.LastRequestBody!;
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
        var requestBody = handler.LastRequestBody!;
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
        var requestBody = handler.LastRequestBody!;
        requestBody.Should().Contain("User stories content");
        requestBody.Should().Contain("public class OrderService {}");
    }

    // ── Error handling ────────────────────────────────────────────────────────

    [Fact]
    public async Task RunAsync_WhenResponseHasNoTextContent_ReturnsEmptyContent()
    {
        // Arrange — response with empty content array exercises the ?. ?? string.Empty branch
        var handler = MockHttpMessageHandler.WithNoTextContent();
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.PMAgent.PMAgent), handler);
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
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.PMAgent.PMAgent), handler);

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
    [InlineData(System.Net.HttpStatusCode.Forbidden, AgentFailureKind.Authentication)]
    [InlineData(System.Net.HttpStatusCode.TooManyRequests, AgentFailureKind.RateLimited)]
    [InlineData(System.Net.HttpStatusCode.BadRequest, AgentFailureKind.Upstream)]
    [InlineData(System.Net.HttpStatusCode.InternalServerError, AgentFailureKind.Upstream)]
    [InlineData(System.Net.HttpStatusCode.ServiceUnavailable, AgentFailureKind.Upstream)]
    public async Task RunAsync_WhenApiReturnsErrorStatus_ClassifiesFailure(System.Net.HttpStatusCode status, AgentFailureKind expected)
    {
        // Arrange
        var handler = new MockHttpMessageHandler("error", status);
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.PMAgent.PMAgent), handler);

        // Act
        var response = await agent.RunAsync(new AgentRequest { Task = "Do something" });

        // Assert
        response.Success.Should().BeFalse();
        response.FailureKind.Should().Be(expected);
    }

    [Fact]
    public void ClassifyFailure_HttpRequestException_IsUpstream() =>
        BaseAgent.ClassifyFailure(new HttpRequestException("connection reset")).Should().Be(AgentFailureKind.Upstream);

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

    // ── Truncation detection ──────────────────────────────────────────────────

    [Theory]
    [InlineData("max_tokens", true)]
    [InlineData("end_turn", false)]
    public async Task RunAsync_ReportsWhetherOutputWasTruncated(string stopReason, bool expected)
    {
        var handler = MockHttpMessageHandler.WithStopReason("partial output", stopReason);
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent), handler);

        var response = await agent.RunAsync(new AgentRequest { Task = "Write a lot of code" });

        response.Success.Should().BeTrue();
        response.Truncated.Should().Be(expected);
    }

    // ── Requirement coverage ──────────────────────────────────────────────────

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent), true)]
    [InlineData(typeof(MultiAgentDevTeam.QAAgent.QAAgent), true)]
    [InlineData(typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent), true)]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent), false)]
    [InlineData(typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent), false)]
    [InlineData(typeof(MultiAgentDevTeam.VerifierAgent.VerifierAgent), false)]
    public async Task RunAsync_CoverageGuidance_OnlyForAgentsThatReportCoverage(Type agentType, bool expected)
    {
        var (agent, handler) = CreateAgent(agentType);

        await agent.RunAsync(new AgentRequest { Task = "Do something" });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        var system = body.RootElement.GetProperty("system")[0].GetProperty("text").GetString()!;
        system.Contains("## Requirement Coverage").Should().Be(expected);
    }

    [Fact]
    public async Task RunAsync_PMAgent_AsksForMachineReadableChecklist()
    {
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.PMAgent.PMAgent));

        await agent.RunAsync(new AgentRequest { Task = "Extract requirements" });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        var system = body.RootElement.GetProperty("system")[0].GetProperty("text").GetString()!;
        system.Should().Contain("```" + RequirementTracking.ChecklistFence);
        system.Should().Contain("\"action\"");
    }

    // ── Model settings ────────────────────────────────────────────────────────

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent), "PM", "claude-sonnet-5-5", "medium")]
    [InlineData(typeof(MultiAgentDevTeam.ArchitectAgent.ArchitectAgent), "Architect", "claude-opus-5-5", "high")]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent), "Developer", "claude-opus-5-5", "high")]
    [InlineData(typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent), "Reviewer", "claude-opus-5-5", "high")]
    [InlineData(typeof(MultiAgentDevTeam.QAAgent.QAAgent), "QA", "claude-sonnet-5-5", "medium")]
    [InlineData(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent), "Security", "claude-sonnet-5-5", "medium")]
    [InlineData(typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent), "DevOps", "claude-sonnet-5-5", "low")]
    [InlineData(typeof(MultiAgentDevTeam.DocsAgent.DocsAgent), "Docs", "claude-haiku-5-5", "medium")]
    [InlineData(typeof(MultiAgentDevTeam.VerifierAgent.VerifierAgent), "Verifier", "claude-sonnet-5-5", "medium")]
    public async Task RunAsync_SendsAgentsModelAndEffort(Type agentType, string configKey, string model, string effort)
    {
        var (agent, handler) = CreateAgent(agentType);

        await agent.RunAsync(new AgentRequest { Task = "Do something" });

        ((BaseAgent)agent).ConfigKey.Should().Be(configKey);
        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        body.RootElement.GetProperty("model").GetString().Should().Be(model);
        body.RootElement.GetProperty("output_config").GetProperty("effort").GetString().Should().Be(effort);
        body.RootElement.GetProperty("stream").GetBoolean().Should().BeTrue();
    }

    [Fact]
    public async Task RunAsync_ConfigOverride_ReplacesDefaults()
    {
        var handler = new MockHttpMessageHandler();
        var config = new AgentConfiguration();
        config.Agents["docs"] = new AgentModelOverride { Model = "claude-sonnet-5-5", Effort = "low", MaxTokens = 1234 };
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.DocsAgent.DocsAgent), handler, config);

        await agent.RunAsync(new AgentRequest { Task = "Document it" });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        body.RootElement.GetProperty("model").GetString().Should().Be("claude-sonnet-5-5");
        body.RootElement.GetProperty("output_config").GetProperty("effort").GetString().Should().Be("low");
        body.RootElement.GetProperty("max_tokens").GetInt32().Should().Be(1234);
    }

    [Fact]
    public async Task RunAsync_InvalidEffort_FailsAsInternalWithoutCallingApi()
    {
        var handler = new MockHttpMessageHandler();
        var config = new AgentConfiguration();
        config.Agents["PM"] = new AgentModelOverride { Effort = "extreme" };
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.PMAgent.PMAgent), handler, config);

        var response = await agent.RunAsync(new AgentRequest { Task = "Do something" });

        response.Success.Should().BeFalse();
        response.FailureKind.Should().Be(AgentFailureKind.Internal);
        response.ErrorMessage.Should().Contain("extreme");
        handler.CallCount.Should().Be(0);
    }

    [Fact]
    public async Task RunAsync_RequestsServerSideFallback()
    {
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent));

        await agent.RunAsync(new AgentRequest { Task = "Audit" });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        body.RootElement.GetProperty("fallbacks").GetString().Should().Be("default");
        string.Join(",", handler.LastRequest!.Headers.GetValues("anthropic-beta"))
            .Should().Contain("server-side-fallback-2026-07-01");
    }

    [Fact]
    public async Task RunAsync_AppendsOutputSizeGuidanceToSystemPrompt()
    {
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.QAAgent.QAAgent));

        await agent.RunAsync(new AgentRequest { Task = "Write tests" });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        var system = body.RootElement.GetProperty("system")[0].GetProperty("text").GetString();
        system.Should().Contain("QA engineer").And.Contain("## Output size");
    }

    // ── Prompt caching ────────────────────────────────────────────────────────

    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent), true)]
    [InlineData(typeof(MultiAgentDevTeam.QAAgent.QAAgent), false)]
    public async Task RunAsync_MarksContextForCachingOnlyWhenEnabled(Type agentType, bool expectCache)
    {
        var (agent, handler) = CreateAgent(agentType);

        await agent.RunAsync(new AgentRequest
        {
            Task = "Implement it",
            Context = new Dictionary<string, string> { ["Requirements"] = "Hello world" },
            PreviousFeedback = "Fix the bug"
        });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        var blocks = body.RootElement.GetProperty("messages")[0].GetProperty("content");
        blocks.GetArrayLength().Should().Be(2);
        blocks[0].GetProperty("text").GetString().Should().Contain("Hello world");
        blocks[0].TryGetProperty("cache_control", out _).Should().Be(expectCache);
        // Feedback changes between review loops, so it must come after the cached block
        blocks[1].GetProperty("text").GetString().Should().Contain("Fix the bug").And.Contain("Implement it");
        blocks[1].TryGetProperty("cache_control", out _).Should().BeFalse();
    }

    [Fact]
    public async Task RunAsync_WithoutContext_SendsSingleBlock()
    {
        var (agent, handler) = CreateAgent(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent));

        await agent.RunAsync(new AgentRequest { Task = "Implement it" });

        using var body = JsonDocument.Parse(handler.LastRequestBody!);
        body.RootElement.GetProperty("messages")[0].GetProperty("content").GetArrayLength().Should().Be(1);
    }

    // ── Usage and cost ────────────────────────────────────────────────────────

    [Fact]
    public async Task RunAsync_ReportsUsageAndEstimatedCost()
    {
        var handler = MockHttpMessageHandler.WithUsage("claude-opus-5-5", input: 1_000_000, output: 100_000, cacheRead: 1_000_000);
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent), handler);

        var response = await agent.RunAsync(new AgentRequest { Task = "Implement it" });

        response.Usage.Should().NotBeNull();
        response.Usage!.AgentName.Should().Be(agent.Name);
        response.Usage.Model.Should().Be("claude-opus-5-5");
        response.Usage.InputTokens.Should().Be(1_000_000);
        response.Usage.OutputTokens.Should().Be(100_000);
        response.Usage.CacheReadInputTokens.Should().Be(1_000_000);
        // $4 input + $2 output + $0.20 cache read
        response.Usage.EstimatedCostUsd.Should().Be(6.20m);
    }

    [Fact]
    public async Task RunAsync_ServedByFallbackModel_StillSucceeds()
    {
        var handler = MockHttpMessageHandler.WithUsage("claude-opus-4-8", input: 10, output: 5);
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent), handler);

        var response = await agent.RunAsync(new AgentRequest { Task = "Audit" });

        response.Success.Should().BeTrue();
        response.Usage!.Model.Should().Be("claude-opus-4-8");
    }

    // ── Refusals ──────────────────────────────────────────────────────────────

    [Fact]
    public async Task RunAsync_Refusal_FailsAsRefusedWithUsage()
    {
        var handler = MockHttpMessageHandler.WithStopReason("", "refusal");
        var agent = AgentFactory.Create(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent), handler);

        var response = await agent.RunAsync(new AgentRequest { Task = "Audit" });

        response.Success.Should().BeFalse();
        response.FailureKind.Should().Be(AgentFailureKind.Refused);
        response.ErrorMessage.Should().Contain("declined");
        response.Usage.Should().NotBeNull();
    }
}
