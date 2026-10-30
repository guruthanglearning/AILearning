using FluentAssertions;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using Moq;
using MultiAgentDevTeam.Orchestrator.Services;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Services;

public class OrchestratorServiceTests
{
    private readonly Mock<ILogger<OrchestratorService>> _logger;
    private readonly Mock<ISessionRepository> _sessions;
    private readonly AgentConfiguration _config;

    public OrchestratorServiceTests()
    {
        _logger = new Mock<ILogger<OrchestratorService>>();
        _sessions = new Mock<ISessionRepository>();
        _sessions
            .Setup(s => s.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);
        _config = new AgentConfiguration { MaxReviewLoops = 3 };
    }

    private static Mock<IAgent> CreateAgentMock(ArtifactType outputType, string agentName, string content = "mock output")
    {
        var mock = new Mock<IAgent>();
        mock.Setup(a => a.Name).Returns(agentName);
        mock.Setup(a => a.OutputType).Returns(outputType);
        mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Ok(content, agentName, TimeSpan.FromMilliseconds(100)));
        return mock;
    }

    private OrchestratorService BuildOrchestrator(IEnumerable<IAgent> agents) =>
        new(agents, Options.Create(_config), _sessions.Object, _logger.Object);

    private List<IAgent> BuildAllAgents(string reviewerContent = "APPROVED")
    {
        return new List<IAgent>
        {
            CreateAgentMock(ArtifactType.Requirements,     "PM").Object,
            CreateAgentMock(ArtifactType.Architecture,     "Architect").Object,
            CreateAgentMock(ArtifactType.SourceCode,       "Developer").Object,
            CreateAgentMock(ArtifactType.ReviewNotes,      "Reviewer", reviewerContent).Object,
            CreateAgentMock(ArtifactType.TestResults,      "QA").Object,
            CreateAgentMock(ArtifactType.SecurityReport,   "Security").Object,
            CreateAgentMock(ArtifactType.DeploymentConfig, "DevOps").Object,
            CreateAgentMock(ArtifactType.Documentation,    "Docs").Object,
        };
    }

    [Fact]
    public async Task RunAsync_ValidRequest_ReturnsSuccess()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "Build a TODO API" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.Success.Should().BeTrue();
        result.ErrorMessage.Should().BeNull();
    }

    [Fact]
    public async Task RunAsync_ValidRequest_ProducesAllArtifacts()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "Build a TODO API" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.Artifacts.Should().ContainKey("Requirements");
        result.Artifacts.Should().ContainKey("Architecture");
        result.Artifacts.Should().ContainKey("SourceCode");
        result.Artifacts.Should().ContainKey("TestResults");
        result.Artifacts.Should().ContainKey("SecurityReport");
        result.Artifacts.Should().ContainKey("DeploymentConfig");
        result.Artifacts.Should().ContainKey("Documentation");
    }

    [Fact]
    public async Task RunAsync_SkipAgent_DoesNotProduceThatArtifact()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest
        {
            Requirement = "Build a TODO API",
            SkipAgents = ["devops", "docs", "security", "qa", "reviewer"]
        };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.Success.Should().BeTrue();
        result.Artifacts.Should().NotContainKey("DeploymentConfig");
        result.Artifacts.Should().NotContainKey("Documentation");
    }

    [Fact]
    public async Task RunAsync_ReviewerApproves_DoesNotRetry()
    {
        // Arrange
        var developerMock = CreateAgentMock(ArtifactType.SourceCode, "Developer");
        var agents = new List<IAgent>
        {
            CreateAgentMock(ArtifactType.Requirements,     "PM").Object,
            CreateAgentMock(ArtifactType.Architecture,     "Architect").Object,
            developerMock.Object,
            CreateAgentMock(ArtifactType.ReviewNotes,      "Reviewer", "APPROVED - code is clean").Object,
            CreateAgentMock(ArtifactType.TestResults,      "QA").Object,
            CreateAgentMock(ArtifactType.SecurityReport,   "Security").Object,
            CreateAgentMock(ArtifactType.DeploymentConfig, "DevOps").Object,
            CreateAgentMock(ArtifactType.Documentation,    "Docs").Object,
        };
        var orchestrator = BuildOrchestrator(agents);
        var request = new OrchestratorRequest { Requirement = "Build a TODO API", MaxReviewLoops = 3 };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.Success.Should().BeTrue();
        // Developer called exactly once since reviewer approved first time
        developerMock.Verify(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task RunAsync_ReviewerRejects_RetriesDeveloper()
    {
        // Arrange
        var developerMock = CreateAgentMock(ArtifactType.SourceCode, "Developer");
        var reviewerCallCount = 0;
        var reviewerMock = new Mock<IAgent>();
        reviewerMock.Setup(a => a.Name).Returns("Reviewer");
        reviewerMock.Setup(a => a.OutputType).Returns(ArtifactType.ReviewNotes);
        reviewerMock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(() =>
            {
                reviewerCallCount++;
                var content = reviewerCallCount >= 2 ? "APPROVED" : "REJECTED - missing null check";
                return AgentResponse.Ok(content, "Reviewer", TimeSpan.FromMilliseconds(100));
            });

        var agents = new List<IAgent>
        {
            CreateAgentMock(ArtifactType.Requirements,     "PM").Object,
            CreateAgentMock(ArtifactType.Architecture,     "Architect").Object,
            developerMock.Object,
            reviewerMock.Object,
            CreateAgentMock(ArtifactType.TestResults,      "QA").Object,
            CreateAgentMock(ArtifactType.SecurityReport,   "Security").Object,
            CreateAgentMock(ArtifactType.DeploymentConfig, "DevOps").Object,
            CreateAgentMock(ArtifactType.Documentation,    "Docs").Object,
        };

        var orchestrator = BuildOrchestrator(agents);
        var request = new OrchestratorRequest { Requirement = "Build a TODO API", MaxReviewLoops = 3 };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.Success.Should().BeTrue();
        developerMock.Verify(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()), Times.Exactly(2));
        reviewerCallCount.Should().Be(2);
    }

    [Fact]
    public async Task RunAsync_AgentFails_ReturnsFailure()
    {
        // Arrange
        var failingPmMock = new Mock<IAgent>();
        failingPmMock.Setup(a => a.Name).Returns("PM");
        failingPmMock.Setup(a => a.OutputType).Returns(ArtifactType.Requirements);
        failingPmMock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Fail("API timeout", "PM"));

        var agents = new List<IAgent>
        {
            failingPmMock.Object,
            CreateAgentMock(ArtifactType.Architecture,     "Architect").Object,
            CreateAgentMock(ArtifactType.SourceCode,       "Developer").Object,
            CreateAgentMock(ArtifactType.ReviewNotes,      "Reviewer").Object,
            CreateAgentMock(ArtifactType.TestResults,      "QA").Object,
            CreateAgentMock(ArtifactType.SecurityReport,   "Security").Object,
            CreateAgentMock(ArtifactType.DeploymentConfig, "DevOps").Object,
            CreateAgentMock(ArtifactType.Documentation,    "Docs").Object,
        };

        var orchestrator = BuildOrchestrator(agents);
        var request = new OrchestratorRequest { Requirement = "Build a TODO API" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.Success.Should().BeFalse();
        result.ErrorMessage.Should().Contain("PM");
    }

    [Fact]
    public async Task RunAsync_AgentLog_ContainsExpectedEntries()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "Build a TODO API" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.AgentLog.Should().NotBeEmpty();
        result.AgentLog.Should().Contain(entry => entry.Contains("PM"));
        result.AgentLog.Should().Contain(entry => entry.Contains("✅"));
    }

    [Fact]
    public async Task RunAsync_EmptyRequirement_StillRuns()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "   " };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert — orchestrator itself does not validate, endpoint does
        result.Should().NotBeNull();
    }

    [Fact]
    public async Task RunAsync_RecordsSessionId()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "Build something" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.SessionId.Should().NotBe(Guid.Empty);
    }

    [Fact]
    public async Task RunAsync_RecordsTotalDuration()
    {
        // Arrange
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "Build something" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert
        result.TotalDuration.Should().BeGreaterThan(TimeSpan.Zero);
    }

    [Fact]
    public void Constructor_MissingAgentType_ThrowsInvalidOperationException()
    {
        // Arrange — register only PM agent, all others missing
        var agents = new List<IAgent>
        {
            CreateAgentMock(ArtifactType.Requirements, "PM").Object
        };

        // Act & Assert — GetAgent throws for missing ArtifactType.Architecture
        var act = () => BuildOrchestrator(agents);
        act.Should().Throw<InvalidOperationException>()
            .WithMessage("*No agent registered*");
    }

    [Fact]
    public async Task RunAsync_ReviewerAlwaysRejects_ProceedsAfterMaxLoops()
    {
        // Arrange — reviewer always rejects, should proceed after maxLoops
        var developerMock = CreateAgentMock(ArtifactType.SourceCode, "Developer");
        var reviewerMock = new Mock<IAgent>();
        reviewerMock.Setup(a => a.Name).Returns("Reviewer");
        reviewerMock.Setup(a => a.OutputType).Returns(ArtifactType.ReviewNotes);
        reviewerMock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Ok("REJECTED - code is bad", "Reviewer", TimeSpan.FromMilliseconds(10)));

        var agents = new List<IAgent>
        {
            CreateAgentMock(ArtifactType.Requirements,     "PM").Object,
            CreateAgentMock(ArtifactType.Architecture,     "Architect").Object,
            developerMock.Object,
            reviewerMock.Object,
            CreateAgentMock(ArtifactType.TestResults,      "QA").Object,
            CreateAgentMock(ArtifactType.SecurityReport,   "Security").Object,
            CreateAgentMock(ArtifactType.DeploymentConfig, "DevOps").Object,
            CreateAgentMock(ArtifactType.Documentation,    "Docs").Object,
        };

        var orchestrator = BuildOrchestrator(agents);
        var request = new OrchestratorRequest { Requirement = "Build something", MaxReviewLoops = 2 };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert — pipeline completes and logs max loops warning
        result.Success.Should().BeTrue();
        developerMock.Verify(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()), Times.Exactly(2));
        result.AgentLog.Should().Contain(entry => entry.Contains("Max review loops reached"));
    }

    [Fact]
    public async Task RunAsync_QaAndSecurityBothSkipped_NoParallelPhaseMessage()
    {
        // Arrange — skip both parallel agents so parallelTasks.Count == 0
        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest
        {
            Requirement = "Build a TODO API",
            SkipAgents = ["qa", "security"]
        };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert — parallel phase message should not appear
        result.Success.Should().BeTrue();
        result.AgentLog.Should().NotContain(entry => entry.Contains("Running QA + Security agents in parallel"));
    }

    [Fact]
    public async Task RunAsync_SessionPersistFails_StillReturnsSuccess()
    {
        // Arrange — session save throws to exercise PersistSessionAsync catch branch
        _sessions
            .Setup(s => s.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
            .ThrowsAsync(new IOException("Disk full"));

        var orchestrator = BuildOrchestrator(BuildAllAgents());
        var request = new OrchestratorRequest { Requirement = "Build something" };

        // Act
        var result = await orchestrator.RunAsync(request);

        // Assert — persist failure must not affect pipeline result
        result.Success.Should().BeTrue();
    }

    private List<IAgent> BuildAgentsWithFailingPm(AgentFailureKind kind)
    {
        var failingPmMock = new Mock<IAgent>();
        failingPmMock.Setup(a => a.Name).Returns("PM");
        failingPmMock.Setup(a => a.OutputType).Returns(ArtifactType.Requirements);
        failingPmMock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Fail("invalid x-api-key", "PM", kind));

        var agents = BuildAllAgents();
        agents[0] = failingPmMock.Object;
        return agents;
    }

    [Theory]
    [InlineData(AgentFailureKind.Authentication)]
    [InlineData(AgentFailureKind.RateLimited)]
    [InlineData(AgentFailureKind.Timeout)]
    [InlineData(AgentFailureKind.Refused)]
    [InlineData(AgentFailureKind.Internal)]
    public async Task RunAsync_AgentFails_PropagatesFailureKind(AgentFailureKind kind)
    {
        var orchestrator = BuildOrchestrator(BuildAgentsWithFailingPm(kind));

        var result = await orchestrator.RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.Success.Should().BeFalse();
        result.FailureKind.Should().Be(kind);
        result.ErrorMessage.Should().Be("Agent 'PM' failed: invalid x-api-key");
    }

    [Fact]
    public async Task RunAsync_AgentFails_LogsReadableFailureReason()
    {
        var orchestrator = BuildOrchestrator(BuildAgentsWithFailingPm(AgentFailureKind.Authentication));

        var result = await orchestrator.RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.AgentLog.Last().Should().StartWith("🛑 Pipeline failed:")
            .And.Contain("rejected the configured API key");
    }

    [Fact]
    public async Task StreamAsync_AgentFails_EmitsFinalFailureMessage()
    {
        var orchestrator = BuildOrchestrator(BuildAgentsWithFailingPm(AgentFailureKind.Authentication));

        var messages = new List<string>();
        await foreach (var message in orchestrator.StreamAsync(new OrchestratorRequest { Requirement = "Build a TODO API" }))
            messages.Add(message);

        messages.Should().Contain(m => m.StartsWith("❌ PM failed"));
        messages.Last().Should().Contain("rejected the configured API key");
    }

    [Fact]
    public async Task RunAsync_AgentFails_PersistsFailureMessageInSession()
    {
        SessionRecord? saved = null;
        _sessions.Setup(s => s.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
            .Callback<SessionRecord, CancellationToken>((r, _) => saved = r)
            .Returns(Task.CompletedTask);
        var orchestrator = BuildOrchestrator(BuildAgentsWithFailingPm(AgentFailureKind.Authentication));

        await orchestrator.RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        saved!.AgentLog.Should().Contain(m => m.StartsWith("🛑 Pipeline failed:"));
    }

    [Theory]
    [InlineData("\n\nAPPROVED\n\n## Summary")]
    [InlineData("   APPROVED")]
    public async Task RunAsync_ApprovalWithLeadingWhitespace_DoesNotRetry(string reviewContent)
    {
        var developerMock = CreateAgentMock(ArtifactType.SourceCode, "Developer");
        var agents = BuildAllAgents(reviewContent);
        agents[2] = developerMock.Object;
        var orchestrator = BuildOrchestrator(agents);

        var result = await orchestrator.RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        developerMock.Verify(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()), Times.Once);
        result.AgentLog.Should().Contain("✅ Code approved on attempt 1");
    }

    [Fact]
    public async Task RunAsync_TruncatedAgentOutput_LogsWarning()
    {
        var developerMock = new Mock<IAgent>();
        developerMock.Setup(a => a.Name).Returns("Developer");
        developerMock.Setup(a => a.OutputType).Returns(ArtifactType.SourceCode);
        developerMock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Ok("partial code", "Developer", TimeSpan.FromSeconds(1), truncated: true));
        var agents = BuildAllAgents();
        agents[2] = developerMock.Object;
        var orchestrator = BuildOrchestrator(agents);

        var result = await orchestrator.RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.Success.Should().BeTrue();
        result.AgentLog.Should().Contain("⚠️ Developer output hit the token limit and is incomplete");
    }

    [Fact]
    public async Task RunAsync_UntruncatedOutput_LogsNoTokenLimitWarning()
    {
        var result = await BuildOrchestrator(BuildAllAgents()).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.AgentLog.Should().NotContain(m => m.Contains("token limit"));
    }

    // ── Usage and cost ────────────────────────────────────────────────────────

    private static Mock<IAgent> CreateAgentMockWithUsage(ArtifactType outputType, string agentName, decimal cost, string content = "mock output")
    {
        var usage = new TokenUsage
        {
            AgentName = agentName, Model = "claude-opus-5-5",
            InputTokens = 1000, OutputTokens = 200, CacheReadInputTokens = 50, EstimatedCostUsd = cost
        };
        var mock = new Mock<IAgent>();
        mock.Setup(a => a.Name).Returns(agentName);
        mock.Setup(a => a.OutputType).Returns(outputType);
        mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Ok(content, agentName, TimeSpan.FromMilliseconds(10), usage: usage));
        return mock;
    }

    private static List<IAgent> BuildAllAgentsWithUsage() =>
    [
        CreateAgentMockWithUsage(ArtifactType.Requirements,     "PM", 0.01m).Object,
        CreateAgentMockWithUsage(ArtifactType.Architecture,     "Architect", 0.02m).Object,
        CreateAgentMockWithUsage(ArtifactType.SourceCode,       "Developer", 0.03m).Object,
        CreateAgentMockWithUsage(ArtifactType.ReviewNotes,      "Reviewer", 0.04m, "APPROVED").Object,
        CreateAgentMockWithUsage(ArtifactType.TestResults,      "QA", 0.05m).Object,
        CreateAgentMockWithUsage(ArtifactType.SecurityReport,   "Security", 0.06m).Object,
        CreateAgentMockWithUsage(ArtifactType.DeploymentConfig, "DevOps", 0.07m).Object,
        CreateAgentMockWithUsage(ArtifactType.Documentation,    "Docs", 0.08m).Object,
    ];

    [Fact]
    public async Task RunAsync_CollectsUsageFromEveryAgentCall()
    {
        var result = await BuildOrchestrator(BuildAllAgentsWithUsage()).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.Usage.Should().HaveCount(8);
        result.Usage.Select(u => u.AgentName).Should().Contain(["PM", "Developer", "QA", "Security", "Docs"]);
        result.EstimatedCostUsd.Should().Be(0.36m);
    }

    [Fact]
    public async Task RunAsync_LogsPerAgentAndTotalCost()
    {
        var result = await BuildOrchestrator(BuildAllAgentsWithUsage()).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.AgentLog.Should().Contain("✅ PM completed in 0.0s (~$0.0100)");
        result.AgentLog.Should().Contain(m =>
            m.StartsWith("💰 Estimated API cost: $0.3600 across 8 calls") && m.Contains("8,000 input") && m.Contains("400 cache-read") && m.Contains("0 cache-write"));
    }

    [Fact]
    public async Task RunAsync_NoUsageReported_LogsNoCostLine()
    {
        var result = await BuildOrchestrator(BuildAllAgents()).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.Usage.Should().BeEmpty();
        result.AgentLog.Should().NotContain(m => m.Contains("Estimated API cost"));
    }

    [Fact]
    public async Task RunAsync_AgentFails_StillReportsCostSoFar()
    {
        var agents = BuildAllAgentsWithUsage();
        var architect = new Mock<IAgent>();
        architect.Setup(a => a.Name).Returns("Architect");
        architect.Setup(a => a.OutputType).Returns(ArtifactType.Architecture);
        architect.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(AgentResponse.Fail("declined", "Architect", AgentFailureKind.Refused,
                new TokenUsage { AgentName = "Architect", EstimatedCostUsd = 0.02m }));
        agents[1] = architect.Object;

        var result = await BuildOrchestrator(agents).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        result.Success.Should().BeFalse();
        result.Usage.Should().HaveCount(2);
        result.AgentLog.Should().Contain(m => m.StartsWith("💰 Estimated API cost: $0.0300 across 2 calls"));
    }

    [Fact]
    public async Task RunAsync_PersistsUsageInSession()
    {
        SessionRecord? saved = null;
        _sessions.Setup(s => s.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
            .Callback<SessionRecord, CancellationToken>((r, _) => saved = r)
            .Returns(Task.CompletedTask);

        await BuildOrchestrator(BuildAllAgentsWithUsage()).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        saved!.Usage.Should().HaveCount(8);
        saved.EstimatedCostUsd.Should().Be(0.36m);
    }

    [Fact]
    public void CostSummary_EmptyUsage_ReturnsNull() =>
        OrchestratorService.CostSummary([]).Should().BeNull();

    // ── Context trimming ──────────────────────────────────────────────────────

    [Fact]
    public async Task RunAsync_DevOpsGetsTestFileListInsteadOfTestSource()
    {
        var agents = BuildAllAgents();
        agents[4] = CreateAgentMock(ArtifactType.TestResults, "QA",
            "### File: tests/App.Tests/ProgramTests.cs\n```csharp\npublic class SecretTestBody {}\n```\n" +
            "### File: tests/App.Tests/App.Tests.csproj\n```xml\n<Project />\n```").Object;

        AgentRequest? devOpsRequest = null;
        var devOps = new Mock<IAgent>();
        devOps.Setup(a => a.Name).Returns("DevOps");
        devOps.Setup(a => a.OutputType).Returns(ArtifactType.DeploymentConfig);
        devOps.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .Callback<AgentRequest, CancellationToken>((r, _) => devOpsRequest = r)
            .ReturnsAsync(AgentResponse.Ok("config", "DevOps", TimeSpan.Zero));
        agents[6] = devOps.Object;

        await BuildOrchestrator(agents).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        devOpsRequest!.Context.Should().NotContainKey("TestResults");
        devOpsRequest.Context["TestFiles"].Should().Be("- tests/App.Tests/ProgramTests.cs\n- tests/App.Tests/App.Tests.csproj");
        devOpsRequest.Context.Values.Should().NotContain(v => v.Contains("SecretTestBody"));
        devOpsRequest.Context.Should().ContainKeys("Architecture", "SourceCode");
    }

    [Fact]
    public async Task RunAsync_QaOutputWithoutFileHeaders_SendsNoTestFileList()
    {
        AgentRequest? devOpsRequest = null;
        var agents = BuildAllAgents();
        var devOps = new Mock<IAgent>();
        devOps.Setup(a => a.Name).Returns("DevOps");
        devOps.Setup(a => a.OutputType).Returns(ArtifactType.DeploymentConfig);
        devOps.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .Callback<AgentRequest, CancellationToken>((r, _) => devOpsRequest = r)
            .ReturnsAsync(AgentResponse.Ok("config", "DevOps", TimeSpan.Zero));
        agents[6] = devOps.Object;

        await BuildOrchestrator(agents).RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API" });

        devOpsRequest!.Context.Should().NotContainKey("TestFiles");
    }

    [Fact]
    public async Task RunAsync_QaSkipped_DevOpsStillRuns()
    {
        var result = await BuildOrchestrator(BuildAllAgents())
            .RunAsync(new OrchestratorRequest { Requirement = "Build a TODO API", SkipAgents = ["qa"] });

        result.Success.Should().BeTrue();
        result.Artifacts.Should().ContainKey(nameof(ArtifactType.DeploymentConfig));
    }
}
