using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using Moq;
using MultiAgentDevTeam.Orchestrator.Services;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Services;

/// <summary>Requirement checklist, developer coverage gate, Verifier phase and per-requirement results.</summary>
public class OrchestratorRequirementTests
{
    private const string PmOutput = """
        # Requirements
        ```requirements-checklist
        [{"id": "FR-1", "text": "Print Hello, World!", "kind": "code", "criterion": "stdout is Hello, World!"},
         {"id": "FR-2", "text": "Test the greeting", "kind": "test"},
         {"id": "FR-3", "text": "Create it under D:\\Temp\\App", "kind": "action"}]
        ```
        """;

    private const string CoveredCode = "### File: Program.cs\n\n## Requirement Coverage\n- FR-1: Program.cs\n- FR-2: N/A - QA\n- FR-3: N/A - action";
    private const string UncoveredCode = "### File: Program.cs\n\n## Requirement Coverage\n- FR-1: N/A - forgot";
    private const string QaOutput = "### File: tests/GreetingTests.cs\n\n## Requirement Coverage\n- FR-2: tests/GreetingTests.cs";

    private const string VerifierOutput = """
        | id | status |
        ```verification-results
        [{"id": "FR-1", "status": "passed", "evidence": "Program.cs prints it"},
         {"id": "FR-2", "status": "passed", "evidence": "GreetingTests"},
         {"id": "FR-3", "status": "manual"},
         {"id": "MISSED-1", "text": "Open the app", "kind": "action", "status": "manual"}]
        ```
        """;

    private readonly Mock<ISessionRepository> _sessions = new();
    private readonly List<AgentRequest> _developerRequests = [];
    private AgentRequest? _verifierRequest;
    private AgentRequest? _devOpsRequest;
    private int _reviewerCalls;

    private static Mock<IAgent> Agent(ArtifactType type, string name, Func<string> content, Action<AgentRequest>? onRun = null)
    {
        var mock = new Mock<IAgent>();
        mock.Setup(a => a.Name).Returns(name);
        mock.Setup(a => a.OutputType).Returns(type);
        mock.Setup(a => a.RunAsync(It.IsAny<AgentRequest>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((AgentRequest r, CancellationToken _) =>
            {
                onRun?.Invoke(r);
                return AgentResponse.Ok(content(), name, TimeSpan.Zero);
            });
        return mock;
    }

    private List<IAgent> Agents(
        string pm = PmOutput,
        Func<int, string>? developer = null,
        string? verifier = VerifierOutput)
    {
        developer ??= _ => CoveredCode;
        var agents = new List<IAgent>
        {
            Agent(ArtifactType.Requirements, "Product Manager", () => pm).Object,
            Agent(ArtifactType.Architecture, "Architect", () => "arch").Object,
            Agent(ArtifactType.SourceCode, "Developer", () => developer(_developerRequests.Count),
                r => _developerRequests.Add(r)).Object,
            Agent(ArtifactType.ReviewNotes, "Reviewer", () => "APPROVED", _ => _reviewerCalls++).Object,
            Agent(ArtifactType.TestResults, "QA", () => QaOutput).Object,
            Agent(ArtifactType.SecurityReport, "Security", () => "no issues").Object,
            Agent(ArtifactType.DeploymentConfig, "DevOps", () => "config", r => _devOpsRequest = r).Object,
            Agent(ArtifactType.Documentation, "Docs", () => "readme").Object,
        };
        if (verifier is not null)
            agents.Add(Agent(ArtifactType.VerificationReport, "Acceptance Verifier", () => verifier,
                r => _verifierRequest = r).Object);
        return agents;
    }

    private OrchestratorService Build(List<IAgent> agents) =>
        new(agents, Options.Create(new AgentConfiguration { MaxReviewLoops = 3 }), _sessions.Object,
            NullLogger<OrchestratorService>.Instance);

    private static OrchestratorRequest Request(params string[] skip) =>
        new() { Requirement = "1.) Hello World in C#\n2.) Put it in D:\\Temp\\App\n3.) Open it", SkipAgents = [.. skip] };

    [Fact]
    public async Task RunAsync_FullyCovered_ReportsEachRequirement()
    {
        var result = await Build(Agents()).RunAsync(Request());

        result.Success.Should().BeTrue();
        result.Requirements.Select(r => (r.Id, r.Status)).Should().Equal(
            ("FR-1", RequirementStatus.Passed),
            ("FR-2", RequirementStatus.Passed),
            ("FR-3", RequirementStatus.Manual),
            ("MISSED-1", RequirementStatus.Manual));
        result.Requirements[1].CoveredBy.Should().Equal("QA");
        result.RequirementsMet.Should().BeTrue();
        result.AgentLog.Should().Contain("📋 3 requirements to track (1 code, 1 test, 1 action)");
        result.AgentLog.Should().Contain("📋 Requirement check: 2 passed, 2 manual");
        result.AgentLog.Should().Contain("🖐️ Needs a manual step: FR-3, MISSED-1");
        result.AgentLog.Should().Contain(l => l.StartsWith("✅ FR-1 [code] Print Hello, World! — Program.cs prints it"));
        result.AgentLog.Should().NotContain("✅ All requirements met");
        _developerRequests.Should().ContainSingle();
    }

    [Fact]
    public async Task RunAsync_AllPassed_SaysAllRequirementsMet()
    {
        var verifier = """
            ```verification-results
            [{"id": "FR-1", "status": "passed"}]
            ```
            """;
        var pm = """
            ```requirements-checklist
            [{"id": "FR-1", "text": "Print it", "kind": "code"}]
            ```
            """;

        var result = await Build(Agents(pm: pm, verifier: verifier)).RunAsync(Request());

        result.AgentLog.Should().Contain("✅ All requirements met");
    }

    [Fact]
    public async Task RunAsync_DeveloperMissesCodeRequirement_RetriesWithCoverageFeedbackBeforeReview()
    {
        var result = await Build(Agents(developer: n => n == 1 ? UncoveredCode : CoveredCode)).RunAsync(Request());

        _developerRequests.Should().HaveCount(2);
        _developerRequests[1].PreviousFeedback.Should().Contain("- FR-1: Print Hello, World! (acceptance: stdout is Hello, World!)");
        _reviewerCalls.Should().Be(1, "the uncovered attempt is sent back without an Opus review");
        result.AgentLog.Should().Contain("⚠️ Attempt 1 doesn't cover FR-1 — sending back to developer");
        result.Requirements[0].Status.Should().Be(RequirementStatus.Passed);
    }

    [Fact]
    public async Task RunAsync_DeveloperNeverCovers_FailsThatRequirementButStillCompletes()
    {
        var result = await Build(Agents(developer: _ => UncoveredCode)).RunAsync(Request());

        result.Success.Should().BeTrue();
        _developerRequests.Should().HaveCount(3);
        _reviewerCalls.Should().Be(1);
        result.AgentLog.Should().Contain("⚠️ Still not covered after 3 attempts: FR-1");
        result.Requirements[0].Status.Should().Be(RequirementStatus.Failed);
        result.RequirementsMet.Should().BeFalse();
        result.AgentLog.Should().Contain("⚠️ Finished with 1 requirement(s) not met");
    }

    [Fact]
    public async Task RunAsync_VerifierGetsOriginalRequestAndClaims()
    {
        await Build(Agents()).RunAsync(Request());

        _verifierRequest!.Context["OriginalRequest"].Should().Contain("D:\\Temp\\App");
        _verifierRequest.Context["CoverageClaims"].Should().Contain("- QA / FR-2: tests/GreetingTests.cs");
        _verifierRequest.Context.Should().ContainKeys("Requirements", "SourceCode", "TestResults", "DeploymentConfig");
    }

    [Fact]
    public async Task RunAsync_DevOpsGetsTheChecklist()
    {
        await Build(Agents()).RunAsync(Request());

        _devOpsRequest!.Context["RequirementChecklist"].Should().Contain("\"id\":\"FR-3\"");
    }

    [Fact]
    public async Task RunAsync_VerifierSkipped_ClaimedRequirementsAreUnverified()
    {
        var result = await Build(Agents()).RunAsync(Request("verifier"));

        _verifierRequest.Should().BeNull();
        result.Requirements.Select(r => r.Status).Should().Equal(
            RequirementStatus.Unverified, RequirementStatus.Unverified, RequirementStatus.Manual);
    }

    [Fact]
    public async Task RunAsync_NoVerifierRegistered_StillTracksRequirements()
    {
        var result = await Build(Agents(verifier: null)).RunAsync(Request());

        result.Success.Should().BeTrue();
        result.Requirements.Should().HaveCount(3);
        result.Artifacts.Should().NotContainKey(nameof(ArtifactType.VerificationReport));
    }

    [Fact]
    public async Task RunAsync_NoChecklist_WarnsAndSkipsTheGate()
    {
        var result = await Build(Agents(pm: "plain requirements", developer: _ => "code", verifier: "no block"))
            .RunAsync(Request());

        result.AgentLog.Should().Contain("⚠️ No requirement checklist in the requirements; per-requirement coverage won't be checked");
        result.AgentLog.Should().Contain("⚠️ The verifier's report had no machine-readable results");
        _developerRequests.Should().ContainSingle();
        result.Requirements.Should().BeEmpty();
        result.RequirementsMet.Should().BeNull();
    }

    [Fact]
    public async Task StreamAsync_FirstMessageIsTheSessionId()
    {
        var messages = new List<string>();
        await foreach (var m in Build(Agents()).StreamAsync(Request()))
            messages.Add(m);

        messages[0].Should().MatchRegex(@"^🆔 Session [0-9a-f-]{36}$");
    }

    [Fact]
    public async Task RunAsync_PersistsRequirementResults()
    {
        SessionRecord? saved = null;
        _sessions.Setup(s => s.SaveAsync(It.IsAny<SessionRecord>(), It.IsAny<CancellationToken>()))
            .Callback<SessionRecord, CancellationToken>((r, _) => saved = r)
            .Returns(Task.CompletedTask);

        await Build(Agents()).RunAsync(Request());

        saved!.Requirements.Should().HaveCount(4);
    }

    [Fact]
    public void CoverageFeedback_OmitsEmptyCriterion()
    {
        OrchestratorService.CoverageFeedback([new RequirementItem { Id = "FR-9", Text = "Do it" }])
            .Should().EndWith("\n- FR-9: Do it");
    }
}
