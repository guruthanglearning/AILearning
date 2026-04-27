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
