using FluentAssertions;
using Microsoft.Playwright;
using MultiAgentDevTeam.BlazorUI.E2ETests.Fixtures;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.E2ETests.Tests;

[Collection("Playwright")]
public class HomePageE2ETests : IClassFixture<PlaywrightFixture>
{
    private readonly PlaywrightFixture _fixture;

    public HomePageE2ETests(PlaywrightFixture fixture)
    {
        _fixture = fixture;
    }

    /// <summary>
    /// Navigate to <paramref name="url"/> and wait until Blazor Server's SignalR
    /// circuit is established.  The negotiate request MUST be registered before the
    /// navigation call, otherwise Playwright can miss the request and wait forever.
    /// </summary>
    private static async Task NavigateAndWaitForCircuitAsync(IPage page, string url)
    {
        // Register the response-wait BEFORE GotoAsync so we never miss the request.
        // Blazor Server's SignalR hub is at /_blazor; the first circuit request is
        // a negotiate.  Match on "_blazor" to catch both the hub path variants.
        var circuitReady = page.WaitForResponseAsync(
            r => r.Url.Contains("_blazor"),
            new PageWaitForResponseOptions { Timeout = 20000 });

        await page.GotoAsync(url);
        await circuitReady;

        // Give the WebSocket connection a moment to fully establish before interacting.
        await page.WaitForTimeoutAsync(600);
    }

    [Fact]
    public async Task HomePage_HasTitle()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await page.GotoAsync(_fixture.BaseUrl);
        var title = await page.TitleAsync();
        title.Should().Contain("MultiAgent");
    }

    [Fact]
    public async Task HomePage_HasRequirementTextarea()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await page.GotoAsync(_fixture.BaseUrl);
        var textarea = page.Locator("#requirement");
        await textarea.WaitForAsync(new LocatorWaitForOptions { Timeout = 10000 });
        (await textarea.IsVisibleAsync()).Should().BeTrue();
    }

    [Fact]
    public async Task HomePage_HasSubmitButton()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await page.GotoAsync(_fixture.BaseUrl);
        var btn = page.Locator("#submit-btn");
        await btn.WaitForAsync(new LocatorWaitForOptions { Timeout = 10000 });
        (await btn.IsVisibleAsync()).Should().BeTrue();
    }

    [Fact]
    public async Task HomePage_EmptySubmit_ShowsValidationError()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await NavigateAndWaitForCircuitAsync(page, _fixture.BaseUrl);
        await page.WaitForSelectorAsync("#submit-btn", new PageWaitForSelectorOptions { Timeout = 10000 });
        await page.ClickAsync("#submit-btn");
        // Wait for Blazor validation message (more robust than a fixed sleep + ContentAsync)
        var validationMessage = page.Locator(".validation-message").First;
        await validationMessage.WaitForAsync(new LocatorWaitForOptions { Timeout = 10000 });
        var text = await validationMessage.TextContentAsync();
        text!.Should().Contain("Requirement is required");
    }

    [Fact]
    public async Task HomePage_ValidSubmit_ShowsProgressLog()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await NavigateAndWaitForCircuitAsync(page, _fixture.BaseUrl);
        await page.WaitForSelectorAsync("#requirement", new PageWaitForSelectorOptions { Timeout = 10000 });
        await page.FillAsync("#requirement", "Build a REST API with JWT authentication and CRUD operations");
        await page.ClickAsync("#submit-btn");
        await page.WaitForSelectorAsync("#progress-log", new PageWaitForSelectorOptions { Timeout = 15000 });
        var log = await page.IsVisibleAsync("#progress-log");
        log.Should().BeTrue();
    }

    [Fact]
    public async Task HomePage_AfterCompletion_ShowsArtifactsSection()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await NavigateAndWaitForCircuitAsync(page, _fixture.BaseUrl);
        await page.WaitForSelectorAsync("#requirement", new PageWaitForSelectorOptions { Timeout = 10000 });
        await page.FillAsync("#requirement", "Build a REST API with JWT authentication and CRUD operations");
        await page.ClickAsync("#submit-btn");
        await page.WaitForSelectorAsync("#artifacts-section", new PageWaitForSelectorOptions { Timeout = 30000 });
        (await page.IsVisibleAsync("#artifacts-section")).Should().BeTrue();
    }

    [Fact]
    public async Task HomePage_AfterCompletion_ShowsNewPipelineButton()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await NavigateAndWaitForCircuitAsync(page, _fixture.BaseUrl);
        await page.WaitForSelectorAsync("#requirement", new PageWaitForSelectorOptions { Timeout = 10000 });
        await page.FillAsync("#requirement", "Build a REST API with JWT authentication and CRUD operations");
        await page.ClickAsync("#submit-btn");
        await page.WaitForSelectorAsync("#new-pipeline-btn", new PageWaitForSelectorOptions { Timeout = 30000 });
        (await page.IsVisibleAsync("#new-pipeline-btn")).Should().BeTrue();
    }
}
