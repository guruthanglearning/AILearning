using FluentAssertions;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Models;

public class RequirementTrackingTests
{
    private const string Requirements = """
        # Requirements
        1. FR-1 Print Hello, World!

        ```requirements-checklist
        [
          {"id": "FR-1", "text": "Print Hello, World!", "kind": "code", "criterion": "stdout is Hello, World!"},
          {"id": "FR-2", "text": "Unit test the greeting", "kind": "test"},
          {"id": "FR-3", "text": "Create it under D:\\Temp\\App", "kind": "action"},
          {"id": "fr-1", "text": "duplicate", "kind": "code"},
        ]
        ```
        """;

    private static readonly List<RequirementItem> Checklist =
    [
        new() { Id = "FR-1", Text = "Print Hello, World!", Kind = RequirementKind.Code },
        new() { Id = "FR-2", Text = "Unit test the greeting", Kind = RequirementKind.Test },
        new() { Id = "FR-3", Text = "Create it under D:\\Temp\\App", Kind = RequirementKind.Action }
    ];

    // ── ParseChecklist ────────────────────────────────────────────────────────

    [Fact]
    public void ParseChecklist_ValidBlock_ReturnsItemsWithoutDuplicateIds()
    {
        var items = RequirementTracking.ParseChecklist(Requirements);

        items.Should().NotBeNull();
        items!.Select(i => i.Id).Should().Equal("FR-1", "FR-2", "FR-3");
        items[0].Criterion.Should().Be("stdout is Hello, World!");
        items.Select(i => i.Kind).Should().Equal(RequirementKind.Code, RequirementKind.Test, RequirementKind.Action);
    }

    [Theory]
    [InlineData("")]
    [InlineData("# Requirements with no checklist")]
    [InlineData("```requirements-checklist\nnot json\n```")]
    [InlineData("```requirements-checklist\n[{\"id\": \"FR-1\", \"kind\": \"unknown-kind\"}]\n```")]
    public void ParseChecklist_MissingOrInvalidBlock_ReturnsNull(string content)
    {
        RequirementTracking.ParseChecklist(content).Should().BeNull();
    }

    [Fact]
    public void ParseChecklist_UsesTheLastBlock()
    {
        var content = """
            ```requirements-checklist
            [{"id": "OLD-1", "text": "old"}]
            ```
            ```requirements-checklist
            [{"id": "NEW-1", "text": "new"}]
            ```
            """;

        RequirementTracking.ParseChecklist(content)!.Single().Id.Should().Be("NEW-1");
    }

    // ── ParseCoverage ─────────────────────────────────────────────────────────

    [Fact]
    public void ParseCoverage_ReadsClaimsInSupportedFormats()
    {
        var content = """
            ### File: src/App/Program.cs
            ```csharp
            Console.WriteLine("Hello, World!");
            ```

            ## Requirement Coverage
            - FR-1: src/App/Program.cs
            * **NFR-1** — targets net10.0
            - fr-2 - N/A - a test, written by QA
            - FR-3: Not applicable (an action for the user)
            not a claim line

            ## Notes
            - FR-9: after the section, ignored
            """;

        var claims = RequirementTracking.ParseCoverage(content, "Developer");

        claims.Select(c => c.RequirementId).Should().Equal("FR-1", "NFR-1", "FR-2", "FR-3");
        claims.Select(c => c.NotApplicable).Should().Equal(false, false, true, true);
        claims[0].Evidence.Should().Be("src/App/Program.cs");
        claims.Should().OnlyContain(c => c.AgentName == "Developer");
    }

    [Fact]
    public void ParseCoverage_NoSection_ReturnsEmpty()
    {
        RequirementTracking.ParseCoverage("- FR-1: claimed outside a coverage section", "Developer")
            .Should().BeEmpty();
    }

    [Fact]
    public void ParseCoverage_UsesTheLastSection()
    {
        var content = "## Requirement Coverage\n- FR-1: first\n\n## Requirement Coverage\n- FR-2: second\n";

        RequirementTracking.ParseCoverage(content, "QA").Single().RequirementId.Should().Be("FR-2");
    }

    // ── Uncovered ─────────────────────────────────────────────────────────────

    [Fact]
    public void Uncovered_IgnoresNotApplicableClaimsAndOtherKinds()
    {
        var claims = new List<CoverageClaim> { new("FR-1", "Developer", "N/A", NotApplicable: true) };

        RequirementTracking.Uncovered(Checklist, claims, RequirementKind.Code).Single().Id.Should().Be("FR-1");
        RequirementTracking.Uncovered(Checklist, [new("fr-1", "Developer", "Program.cs", false)], RequirementKind.Code)
            .Should().BeEmpty();
    }

    // ── ParseVerification ─────────────────────────────────────────────────────

    [Fact]
    public void ParseVerification_ReadsStatusesCaseInsensitively()
    {
        var report = """
            | id | status |
            ```verification-results
            [{"id": "FR-1", "status": "passed", "evidence": "Program.cs"},
             {"id": "MISSED-1", "text": "Run the app", "kind": "action", "status": "MANUAL"}]
            ```
            """;

        var entries = RequirementTracking.ParseVerification(report)!;

        entries.Select(e => e.Status).Should().Equal(RequirementStatus.Passed, RequirementStatus.Manual);
        entries[1].Kind.Should().Be(RequirementKind.Action);
    }

    [Fact]
    public void ParseVerification_NoBlock_ReturnsNull()
    {
        RequirementTracking.ParseVerification("APPROVED, looks fine").Should().BeNull();
    }

    // ── Evaluate ──────────────────────────────────────────────────────────────

    [Fact]
    public void Evaluate_CombinesClaimsAndVerdicts()
    {
        var claims = new List<CoverageClaim>
        {
            new("FR-1", "Developer", "Program.cs", false),
            new("FR-2", "QA", "GreetingTests.cs", false)
        };
        var verdicts = new List<VerificationEntry>
        {
            new() { Id = "FR-1", Status = RequirementStatus.Passed, Evidence = "prints the greeting" },
            new() { Id = "FR-2", Status = RequirementStatus.Failed, Evidence = "test asserts the wrong text" },
            new() { Id = "FR-3", Status = RequirementStatus.Passed, Evidence = "README says so" }
        };

        var results = RequirementTracking.Evaluate(Checklist, claims, verdicts);

        results.Select(r => r.Status).Should().Equal(
            RequirementStatus.Passed, RequirementStatus.Failed, RequirementStatus.Manual);
        results[0].CoveredBy.Should().Equal("Developer");
        results[1].Evidence.Should().Be("test asserts the wrong text");
        results.Should().OnlyContain(r => r.Source == "Product Manager");
    }

    [Fact]
    public void Evaluate_UnclaimedRequirement_FailsEvenIfVerifierPassedIt()
    {
        var verdicts = new List<VerificationEntry> { new() { Id = "FR-1", Status = RequirementStatus.Passed } };

        var result = RequirementTracking.Evaluate(Checklist, [], verdicts)[0];

        result.Status.Should().Be(RequirementStatus.Failed);
        result.Evidence.Should().StartWith("No agent reported covering it.");
    }

    [Fact]
    public void Evaluate_WithoutVerifier_ClaimedIsUnverifiedAndActionIsManual()
    {
        var claims = new List<CoverageClaim> { new("FR-1", "Developer", "Program.cs", false) };

        var results = RequirementTracking.Evaluate(Checklist, claims, verification: null);

        results[0].Status.Should().Be(RequirementStatus.Unverified);
        results[0].Evidence.Should().Be("Developer: Program.cs");
        results[1].Status.Should().Be(RequirementStatus.Failed);
        results[2].Status.Should().Be(RequirementStatus.Manual);
    }

    [Fact]
    public void Evaluate_ActionTheVerifierFailed_StaysFailed()
    {
        var verdicts = new List<VerificationEntry>
        {
            new() { Id = "FR-3", Status = RequirementStatus.Failed, Evidence = "writes to a different folder" }
        };

        RequirementTracking.Evaluate(Checklist, [], verdicts)[2].Status.Should().Be(RequirementStatus.Failed);
    }

    [Fact]
    public void Evaluate_RequirementsTheChecklistMissed_AreAddedFromTheVerifier()
    {
        var verdicts = new List<VerificationEntry>
        {
            new() { Id = "MISSED-1", Text = "Open the app", Kind = RequirementKind.Action, Status = RequirementStatus.Passed },
            new() { Id = "MISSED-2", Text = "Use .NET 10", Status = RequirementStatus.Failed, Evidence = "targets net8.0" }
        };

        var results = RequirementTracking.Evaluate([], [], verdicts, verifierSource: "Acceptance Verifier");

        results.Select(r => r.Status).Should().Equal(RequirementStatus.Manual, RequirementStatus.Failed);
        results[1].Kind.Should().Be(RequirementKind.Code);
        results.Should().OnlyContain(r => r.Source == "Acceptance Verifier");
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    [Fact]
    public void ToJson_RoundTripsThroughTheChecklistParser()
    {
        var json = RequirementTracking.ToJson(Checklist);

        json.Should().Contain("\"kind\":\"Action\"").And.NotContain("criterion");
        RequirementTracking.ParseChecklist($"```requirements-checklist\n{json}\n```").Should().BeEquivalentTo(Checklist);
    }

    [Theory]
    [InlineData(RequirementStatus.Passed, "✅")]
    [InlineData(RequirementStatus.Failed, "❌")]
    [InlineData(RequirementStatus.Manual, "🖐️")]
    [InlineData(RequirementStatus.Unverified, "❔")]
    public void StatusIcon_MapsEachStatus(RequirementStatus status, string icon)
    {
        RequirementTracking.StatusIcon(status).Should().Be(icon);
    }

    [Fact]
    public void RequirementsMet_ReflectsFailures()
    {
        new OrchestratorResponse().RequirementsMet.Should().BeNull();
        new OrchestratorResponse { Requirements = [new() { Status = RequirementStatus.Manual }] }
            .RequirementsMet.Should().BeTrue();
        new OrchestratorResponse { Requirements = [new() { Status = RequirementStatus.Failed }] }
            .RequirementsMet.Should().BeFalse();
    }

    [Fact]
    public void MarkProjectWritten_PassesOnlyActionsAboutTheRequestedFolder()
    {
        List<RequirementResult> results =
        [
            new() { Id = "FR-1", Text = "Print it", Kind = RequirementKind.Code, Status = RequirementStatus.Passed },
            new() { Id = "FR-3", Text = "Project created under d:/temp/app", Kind = RequirementKind.Action,
                    Status = RequirementStatus.Manual, CoveredBy = ["Software Developer"] },
            new() { Id = "FR-4", Text = "Run the app", Kind = RequirementKind.Action, Status = RequirementStatus.Manual },
            new() { Id = "FR-5", Text = @"Code mentions D:\Temp\App", Kind = RequirementKind.Code, Status = RequirementStatus.Failed }
        ];

        var marked = RequirementTracking.MarkProjectWritten(results, @"D:\Temp\App\", @"D:\Temp\App", 7);

        marked.Select(r => r.Status).Should().Equal(
            RequirementStatus.Passed, RequirementStatus.Passed, RequirementStatus.Manual, RequirementStatus.Failed);
        marked[1].Evidence.Should().Be(@"7 files written to D:\Temp\App");
        marked[1].CoveredBy.Should().Equal("Software Developer", "Orchestrator");
    }

    [Fact]
    public void MarkProjectWritten_BareDriveMatchesNothing()
    {
        List<RequirementResult> results =
            [new() { Id = "FR-1", Text = "Add: a greeting", Kind = RequirementKind.Action, Status = RequirementStatus.Manual }];

        RequirementTracking.MarkProjectWritten(results, @"D:\", @"D:\hello-1a2b3c4d", 3)
            .Single().Status.Should().Be(RequirementStatus.Manual);
    }

    [Theory]
    [InlineData(@"Build and run the application in D:\Temp\App", RequirementStatus.Manual)]
    [InlineData(@"Open D:\Temp\App in Visual Studio", RequirementStatus.Manual)]
    [InlineData(@"Back it up to D:\Temp\AppBackup", RequirementStatus.Manual)]
    [InlineData(@"Put the tests in D:\Temp\App\tests", RequirementStatus.Manual)]
    [InlineData(@"Delete temporary files in D:\Temp\App", RequirementStatus.Manual)]
    [InlineData(@"D:\Temp\App must be backed up nightly", RequirementStatus.Manual)]
    [InlineData(@"Create the project in D:\Temp\App.", RequirementStatus.Passed)]
    [InlineData(@"Save it to ""D:\Temp\App""", RequirementStatus.Passed)]
    [InlineData(@"Place it under D:\Temp\App\", RequirementStatus.Passed)]
    public void MarkProjectWritten_OnlyPassesPlacingFilesInExactlyThatFolder(string text, RequirementStatus expected)
    {
        List<RequirementResult> results =
            [new() { Id = "FR-1", Text = text, Kind = RequirementKind.Action, Status = RequirementStatus.Manual }];

        RequirementTracking.MarkProjectWritten(results, @"D:\Temp\App", @"D:\Temp\App", 3)
            .Single().Status.Should().Be(expected);
    }

    [Fact]
    public void MarkProjectWritten_KeepsTheVerifiersFailure()
    {
        List<RequirementResult> results =
        [
            new() { Id = "FR-1", Text = @"Create it in D:\Temp\App", Kind = RequirementKind.Action,
                    Status = RequirementStatus.Failed, Evidence = "Wrong framework" }
        ];

        var marked = RequirementTracking.MarkProjectWritten(results, @"D:\Temp\App", @"D:\Temp\App", 3).Single();

        marked.Status.Should().Be(RequirementStatus.Failed);
        marked.Evidence.Should().Be("Wrong framework");
    }
}
