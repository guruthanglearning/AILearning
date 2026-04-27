using FluentAssertions;
using MultiAgentDevTeam.BlazorUI.E2ETests.Fixtures;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.E2ETests.Tests;

[Collection("Playwright")]
public class SessionsE2ETests : IClassFixture<PlaywrightFixture>
{
    private readonly PlaywrightFixture _fixture;

    public SessionsE2ETests(PlaywrightFixture fixture)
    {
        _fixture = fixture;
    }

    [Fact]
    public async Task SessionsPage_Loads_Returns200Content()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await page.GotoAsync($"{_fixture.BaseUrl}/sessions");
        await page.WaitForLoadStateAsync();
        var title = await page.TitleAsync();
        title.Should().Contain("Session");
    }

    [Fact]
    public async Task SessionsPage_ShowsSessionsTable_WhenSessionsExist()
    {
        var page = await _fixture.Browser.NewPageAsync();
        await page.GotoAsync($"{_fixture.BaseUrl}/sessions");
        await page.WaitForSelectorAsync("#sessions-table", new Microsoft.Playwright.PageWaitForSelectorOptions { Timeout = 15000 });
        (await page.IsVisibleAsync("#sessions-table")).Should().BeTrue();
    }
}
