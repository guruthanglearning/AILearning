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
}
