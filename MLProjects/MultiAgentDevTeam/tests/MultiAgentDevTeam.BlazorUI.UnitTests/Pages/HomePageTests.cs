using Bunit;
using FluentAssertions;
using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.Extensions.DependencyInjection;
using Moq;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Pages;
using MultiAgentDevTeam.BlazorUI.Services;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Pages;

public class HomePageTests : TestContext
{
    private readonly Mock<IPipelineClient> _pipelineClient;

    public HomePageTests()
    {
        _pipelineClient = new Mock<IPipelineClient>();
        Services.AddSingleton(_pipelineClient.Object);
    }

    [Fact]
    public void Home_RendersRequirementInput_OnIdle()
    {
        var cut = RenderComponent<Home>();
        cut.Find("#requirement").Should().NotBeNull();
    }

    [Fact]
    public void Home_RendersSkipAgentsInput()
    {
        var cut = RenderComponent<Home>();
        cut.Find("#skipAgents").Should().NotBeNull();
    }

    [Fact]
    public void Home_RendersMaxLoopsInput()
    {
        var cut = RenderComponent<Home>();
        cut.Find("#maxLoops").Should().NotBeNull();
    }

    [Fact]
    public void Home_RendersSubmitButton()
    {
        var cut = RenderComponent<Home>();
        cut.Find("#submit-btn").Should().NotBeNull();
    }

    [Fact]
    public async Task Home_EmptyRequirement_ShowsValidationError()
    {
        var cut = RenderComponent<Home>();

        // Submit with empty form
        await cut.Find("form").SubmitAsync();

        cut.Markup.Should().Contain("Requirement is required");
    }

    [Fact]
    public async Task Home_ShortRequirement_ShowsValidationError()
    {
        var cut = RenderComponent<Home>();

        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="short" });
        await cut.Find("form").SubmitAsync();

        cut.Markup.Should().Contain("at least 10 characters");
    }

    [Fact]
    public async Task Home_ValidSubmit_ShowsProgressLog()
    {
        // Arrange — mock returns a few progress messages
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncMessages("🤖 PM started", "✅ PM completed"));

        var cut = RenderComponent<Home>();

        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        cut.Find("#progress-log").Should().NotBeNull();
    }

    [Fact]
    public async Task Home_StreamingMessages_DisplayedInLog()
    {
        // Arrange
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncMessages("🤖 PM started", "✅ PM done", "🤖 Architect started"));

        var cut = RenderComponent<Home>();
        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        var logEntries = cut.FindAll(".log-entry");
        logEntries.Count.Should().BeGreaterThan(0);
    }

    [Fact]
    public async Task Home_StreamCompletes_ShowsArtifactsSection()
    {
        // Arrange — stream completes immediately
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncMessages("✅ Pipeline done"));

        var cut = RenderComponent<Home>();
        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        cut.Find("#artifacts-section").Should().NotBeNull();
    }

    [Fact]
    public async Task Home_StreamCompletes_ShowsNewPipelineButton()
    {
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(AsyncMessages("done"));

        var cut = RenderComponent<Home>();
        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        cut.Find("#new-pipeline-btn").Should().NotBeNull();
    }

    [Fact]
    public async Task Home_ClientThrows_ShowsErrorMessage()
    {
        // Arrange — stream throws
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(ThrowingAsyncEnum(new HttpRequestException("Connection refused")));

        var cut = RenderComponent<Home>();
        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        cut.Find("#error-message").Should().NotBeNull();
        cut.Markup.Should().Contain("Connection refused");
    }

    [Fact]
    public async Task Home_ErrorState_ShowsTryAgainButton()
    {
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(ThrowingAsyncEnum(new HttpRequestException("timeout")));

        var cut = RenderComponent<Home>();
        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        cut.Find("#try-again-btn").Should().NotBeNull();
    }

    [Fact]
    public async Task Home_TryAgain_ResetsToIdle()
    {
        _pipelineClient
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(ThrowingAsyncEnum(new HttpRequestException("timeout")));

        var cut = RenderComponent<Home>();
        var input = cut.Find("#requirement");
        await input.ChangeAsync(new ChangeEventArgs { Value ="Build a TODO REST API with authentication" });
        await cut.Find("form").SubmitAsync();

        // Click Try Again
        await cut.Find("#try-again-btn").ClickAsync(new MouseEventArgs());

        // Form should be visible again
        cut.Find("#pipeline-form").Should().NotBeNull();
    }

    [Fact]
    public void Home_Dispose_DoesNotThrow()
    {
        var cut = RenderComponent<Home>();
        var act = () => cut.Instance.Dispose();
        act.Should().NotThrow();
    }

    // ── Helpers ───────────────────────────────────────────────────────────────

    private static async IAsyncEnumerable<string> AsyncMessages(params string[] messages)
    {
        foreach (var msg in messages)
        {
            yield return msg;
            await Task.Yield();
        }
    }

    private static async IAsyncEnumerable<string> ThrowingAsyncEnum(Exception ex)
    {
        await Task.Yield();
        throw ex;
#pragma warning disable CS0162 // Unreachable code — yield break is required to make this an iterator method
        yield break;
#pragma warning restore CS0162
    }
}
