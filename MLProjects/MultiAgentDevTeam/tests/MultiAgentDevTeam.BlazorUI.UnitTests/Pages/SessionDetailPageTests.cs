using Bunit;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Pages;
using MultiAgentDevTeam.BlazorUI.Services;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Pages;

public class SessionDetailPageTests : TestContext
{
    private readonly Mock<ISessionApiClient> _sessionClient;

    public SessionDetailPageTests()
    {
        _sessionClient = new Mock<ISessionApiClient>();
        Services.AddSingleton(_sessionClient.Object);
    }

    [Fact]
    public async Task SessionDetail_NotFound_ShowsErrorMessage()
    {
        _sessionClient.Setup(c => c.GetAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((SessionRecord?)null);

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, Guid.NewGuid()));
        await cut.InvokeAsync(() => { });

        cut.Markup.Should().Contain("not found");
    }

    [Fact]
    public async Task SessionDetail_ExistingSession_ShowsRequirement()
    {
        var id = Guid.NewGuid();
        _sessionClient.Setup(c => c.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new SessionRecord { SessionId = id, Requirement = "Build TODO API", Success = true });

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, id));
        await cut.InvokeAsync(() => { });

        cut.Markup.Should().Contain("Build TODO API");
    }

    [Fact]
    public async Task SessionDetail_WithRequirements_ShowsChecklist()
    {
        var id = Guid.NewGuid();
        _sessionClient.Setup(c => c.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new SessionRecord
            {
                SessionId = id,
                Requirement = "Hello World",
                Success = true,
                Requirements =
                [
                    new() { Id = "FR-1", Text = "Print it", Kind = "Code", Status = "Passed", Evidence = "Program.cs" },
                    new() { Id = "FR-2", Text = "Run it", Kind = "Action", Status = "Manual" }
                ]
            });

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, id));
        await cut.InvokeAsync(() => { });

        cut.FindAll(".requirement-row").Should().HaveCount(2);
        cut.Markup.Should().Contain("✅ Passed").And.Contain("🖐️ Manual").And.Contain("Program.cs");
    }

    [Fact]
    public async Task SessionDetail_NoRequirements_HidesChecklist()
    {
        var id = Guid.NewGuid();
        _sessionClient.Setup(c => c.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new SessionRecord { SessionId = id, Requirement = "Hello World", Success = true });

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, id));
        await cut.InvokeAsync(() => { });

        cut.FindAll("#requirements-section").Should().BeEmpty();
    }

    [Theory]
    [InlineData("Passed", "✅")]
    [InlineData("Failed", "❌")]
    [InlineData("Manual", "🖐️")]
    [InlineData("Unverified", "❔")]
    public void RequirementResult_StatusIcon_MapsStatus(string status, string icon) =>
        new RequirementResult { Status = status }.StatusIcon.Should().Be(icon);

    [Fact]
    public async Task SessionDetail_WithArtifacts_ShowsArtifactsSection()
    {
        var id = Guid.NewGuid();
        _sessionClient.Setup(c => c.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new SessionRecord
            {
                SessionId = id,
                Requirement = "Build something long enough",
                Success = true,
                Artifacts = new Dictionary<string, string>
                {
                    ["Requirements"] = "# Requirements content",
                    ["SourceCode"] = "public class Foo {}"
                }
            });

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, id));
        await cut.InvokeAsync(() => { });

        cut.Find("#artifacts-section").Should().NotBeNull();
        var details = cut.FindAll("details");
        details.Count.Should().Be(2);
    }

    [Fact]
    public async Task SessionDetail_WithAgentLog_ShowsLog()
    {
        var id = Guid.NewGuid();
        _sessionClient.Setup(c => c.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new SessionRecord
            {
                SessionId = id,
                Requirement = "Build something",
                Success = true,
                AgentLog = ["🤖 PM started", "✅ PM done"]
            });

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, id));
        await cut.InvokeAsync(() => { });

        cut.Find("#agent-log").Should().NotBeNull();
        cut.FindAll(".log-entry").Count.Should().Be(2);
    }

    [Fact]
    public async Task SessionDetail_FailedSession_ShowsErrorMessage()
    {
        var id = Guid.NewGuid();
        _sessionClient.Setup(c => c.GetAsync(id, It.IsAny<CancellationToken>()))
            .ReturnsAsync(new SessionRecord
            {
                SessionId = id,
                Requirement = "Build something",
                Success = false,
                ErrorMessage = "PM Agent failed"
            });

        var cut = RenderComponent<SessionDetail>(p => p.Add(x => x.SessionId, id));
        await cut.InvokeAsync(() => { });

        cut.Markup.Should().Contain("PM Agent failed");
    }
}
