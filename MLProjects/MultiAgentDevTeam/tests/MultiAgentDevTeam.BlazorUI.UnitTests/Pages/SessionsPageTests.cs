using Bunit;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Pages;
using MultiAgentDevTeam.BlazorUI.Services;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Pages;

public class SessionsPageTests : TestContext
{
    private readonly Mock<ISessionApiClient> _sessionClient;

    public SessionsPageTests()
    {
        _sessionClient = new Mock<ISessionApiClient>();
        Services.AddSingleton(_sessionClient.Object);
    }

    [Fact]
    public async Task Sessions_NoSessions_ShowsEmptyMessage()
    {
        _sessionClient.Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>());

        var cut = RenderComponent<Sessions>();
        await cut.InvokeAsync(() => { }); // flush async init

        cut.Find("#no-sessions").Should().NotBeNull();
    }

    [Fact]
    public async Task Sessions_WithSessions_ShowsTable()
    {
        _sessionClient.Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>
            {
                new() { SessionId = Guid.NewGuid(), Requirement = "Build TODO API", Success = true, ArtifactCount = 5, TotalDuration = "00:01:00" }
            });

        var cut = RenderComponent<Sessions>();
        await cut.InvokeAsync(() => { });

        cut.Find("#sessions-table").Should().NotBeNull();
    }

    [Fact]
    public async Task Sessions_WithMultipleSessions_ShowsCorrectRowCount()
    {
        _sessionClient.Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>
            {
                new() { SessionId = Guid.NewGuid(), Requirement = "Build API 1", Success = true },
                new() { SessionId = Guid.NewGuid(), Requirement = "Build API 2", Success = false },
                new() { SessionId = Guid.NewGuid(), Requirement = "Build API 3", Success = true }
            });

        var cut = RenderComponent<Sessions>();
        await cut.InvokeAsync(() => { });

        var rows = cut.FindAll("tbody tr");
        rows.Count.Should().Be(3);
    }

    [Fact]
    public async Task Sessions_SuccessfulSession_ShowsSuccessBadge()
    {
        _sessionClient.Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>
            {
                new() { SessionId = Guid.NewGuid(), Requirement = "Build API", Success = true }
            });

        var cut = RenderComponent<Sessions>();
        await cut.InvokeAsync(() => { });

        cut.Markup.Should().Contain("badge-success");
    }

    [Fact]
    public async Task Sessions_FailedSession_ShowsDangerBadge()
    {
        _sessionClient.Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>
            {
                new() { SessionId = Guid.NewGuid(), Requirement = "Build API", Success = false }
            });

        var cut = RenderComponent<Sessions>();
        await cut.InvokeAsync(() => { });

        cut.Markup.Should().Contain("badge-danger");
    }
}
