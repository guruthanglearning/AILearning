using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Playwright;
using Moq;
using MultiAgentDevTeam.BlazorUI.Components;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Services;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.E2ETests.Fixtures;

/// <summary>
/// Starts a real Kestrel-hosted Blazor Server app on a random port so Playwright
/// (a real browser) can connect to it.  WebApplicationFactory uses an in-process
/// TestServer that only works with its own HttpClient handler — Playwright cannot
/// reach it.  Starting the app directly on port 0 avoids that limitation.
/// </summary>
public class PlaywrightFixture : IAsyncLifetime
{
    private WebApplication? _app;

    public string BaseUrl { get; private set; } = string.Empty;
    public IPlaywright Playwright { get; private set; } = null!;
    public IBrowser Browser { get; private set; } = null!;

    public async Task InitializeAsync()
    {
        var pipelineMock = new Mock<IPipelineClient>();
        pipelineMock
            .Setup(c => c.StreamAsync(It.IsAny<PipelineRequest>(), It.IsAny<CancellationToken>()))
            .Returns(() => FakeStream()); // factory so each call gets a fresh enumerable

        var sessionMock = new Mock<ISessionApiClient>();
        sessionMock
            .Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>
            {
                new() { SessionId = Guid.NewGuid(), Requirement = "Build a TODO API", Success = true, ArtifactCount = 3, TotalDuration = "00:01:30" }
            });
        sessionMock
            .Setup(c => c.GetAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((SessionRecord?)null);

        // Build the BlazorUI app directly, mirroring BlazorUI/Program.cs, but:
        //   • listen on a real port (port 0 = OS-assigned) so Playwright can reach it
        //   • replace IPipelineClient / ISessionApiClient with mocks
        //
        // UseStaticWebAssets() is required so that /_framework/blazor.server.js is
        // served from the framework packages' embedded resources.  Without it the
        // script 404s, the Blazor SignalR circuit never starts, and interactive
        // components never respond to clicks.  Development environment is needed
        // because UseStaticWebAssets is a no-op in Production by convention.
        var builder = WebApplication.CreateBuilder(new WebApplicationOptions
        {
            ApplicationName = typeof(App).Assembly.GetName().Name,
            EnvironmentName = Environments.Development
        });

        builder.WebHost.UseStaticWebAssets();

        builder.Services.AddRazorComponents()
            .AddInteractiveServerComponents();

        builder.Services.AddSingleton(pipelineMock.Object);
        builder.Services.AddSingleton(sessionMock.Object);

        builder.Services.AddLogging(lb => lb.AddConsole().SetMinimumLevel(LogLevel.Warning));
        builder.WebHost.UseUrls("http://127.0.0.1:0");

        _app = builder.Build();

        if (!_app.Environment.IsDevelopment())
            _app.UseExceptionHandler("/Error");

        _app.UseStaticFiles();
        _app.UseAntiforgery();
        _app.MapRazorComponents<App>()
            .AddInteractiveServerRenderMode();

        await _app.StartAsync();
        BaseUrl = _app.Urls.First().TrimEnd('/');

        Playwright = await Microsoft.Playwright.Playwright.CreateAsync();
        Browser = await Playwright.Chromium.LaunchAsync(new BrowserTypeLaunchOptions { Headless = true });
    }

    public async Task DisposeAsync()
    {
        await Browser.DisposeAsync();
        Playwright.Dispose();
        if (_app is not null)
            await _app.DisposeAsync();
    }

    private static async IAsyncEnumerable<string> FakeStream()
    {
        yield return "🤖 PM started";
        await Task.Delay(10);
        yield return "✅ PM completed in 0.1s";
        await Task.Delay(10);
        yield return "🤖 Architect started";
        await Task.Delay(10);
        yield return "✅ Architect completed in 0.1s";
    }
}
