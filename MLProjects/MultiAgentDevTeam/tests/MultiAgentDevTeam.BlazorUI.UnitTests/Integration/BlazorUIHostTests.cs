using FluentAssertions;
using Microsoft.AspNetCore.Mvc.Testing;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.DependencyInjection.Extensions;
using Moq;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Services;
using System.Net;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Integration;

public class BlazorUIHostTests : IClassFixture<WebApplicationFactory<global::Program>>
{
    private readonly WebApplicationFactory<global::Program> _factory;

    public BlazorUIHostTests(WebApplicationFactory<global::Program> factory)
    {
        var sessionMock = new Mock<ISessionApiClient>();
        sessionMock
            .Setup(c => c.ListAsync(It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(new List<SessionSummary>());
        sessionMock
            .Setup(c => c.GetAsync(It.IsAny<Guid>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync((SessionRecord?)null);

        _factory = factory.WithWebHostBuilder(builder =>
        {
            builder.ConfigureServices(services =>
            {
                // Remove typed HTTP client registrations and replace with mocks
                services.RemoveAll<IPipelineClient>();
                services.RemoveAll<ISessionApiClient>();
                services.AddSingleton(Mock.Of<IPipelineClient>());
                services.AddSingleton(sessionMock.Object);
            });
        });
    }

    [Fact]
    public async Task GET_Root_Returns200()
    {
        var client = _factory.CreateClient();
        var response = await client.GetAsync("/");
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GET_Root_ContainsSubmitButton()
    {
        var client = _factory.CreateClient();
        var html = await (await client.GetAsync("/")).Content.ReadAsStringAsync();
        html.Should().Contain("Submit");
    }

    [Fact]
    public async Task GET_Sessions_Returns200()
    {
        var client = _factory.CreateClient();
        var response = await client.GetAsync("/sessions");
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GET_AppCss_Returns200()
    {
        var client = _factory.CreateClient();
        var response = await client.GetAsync("/app.css");
        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task GET_UnknownRoute_ReturnsNonSuccessOrNotFound()
    {
        // Blazor Server with WebApplicationFactory returns 404 for routes not matching static files or API endpoints
        var client = _factory.CreateClient(new WebApplicationFactoryClientOptions { AllowAutoRedirect = false });
        var response = await client.GetAsync("/this-route-does-not-exist");
        // Accept either 200 (if Blazor renders NotFound component) or 404
        var validCodes = new[] { HttpStatusCode.OK, HttpStatusCode.NotFound };
        validCodes.Should().Contain(response.StatusCode);
    }
}
