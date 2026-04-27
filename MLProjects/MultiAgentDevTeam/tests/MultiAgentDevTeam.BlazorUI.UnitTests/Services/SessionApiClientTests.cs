using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Services;
using System.Net;
using System.Net.Http.Json;
using System.Text;
using System.Text.Json;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Services;

public class SessionApiClientTests
{
    private class JsonHandler : HttpMessageHandler
    {
        private readonly object? _responseBody;
        private readonly HttpStatusCode _statusCode;

        public JsonHandler(object? responseBody, HttpStatusCode statusCode = HttpStatusCode.OK)
        {
            _responseBody = responseBody;
            _statusCode = statusCode;
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            var json = JsonSerializer.Serialize(_responseBody);
            var response = new HttpResponseMessage(_statusCode)
            {
                Content = new StringContent(json, Encoding.UTF8, "application/json")
            };
            return Task.FromResult(response);
        }
    }

    private static SessionApiClient CreateClient(HttpMessageHandler handler)
    {
        var http = new HttpClient(handler) { BaseAddress = new Uri("http://localhost:5000") };
        return new SessionApiClient(http, NullLogger<SessionApiClient>.Instance);
    }

    [Fact]
    public async Task ListAsync_ReturnsSessions()
    {
        // Arrange
        var sessions = new List<SessionSummary>
        {
            new() { SessionId = Guid.NewGuid(), Requirement = "Build API", Success = true, ArtifactCount = 5 }
        };
        var client = CreateClient(new JsonHandler(sessions));

        // Act
        var result = await client.ListAsync();

        // Assert
        result.Should().HaveCount(1);
        result[0].Requirement.Should().Be("Build API");
    }

    [Fact]
    public async Task ListAsync_OnError_ReturnsEmptyList()
    {
        // Arrange
        var client = CreateClient(new JsonHandler(null, HttpStatusCode.InternalServerError));

        // Act
        var result = await client.ListAsync();

        // Assert
        result.Should().BeEmpty();
    }

    [Fact]
    public async Task GetAsync_ExistingSession_ReturnsRecord()
    {
        // Arrange
        var id = Guid.NewGuid();
        var record = new SessionRecord { SessionId = id, Requirement = "Build TODO API", Success = true };
        var client = CreateClient(new JsonHandler(record));

        // Act
        var result = await client.GetAsync(id);

        // Assert
        result.Should().NotBeNull();
        result!.SessionId.Should().Be(id);
    }

    [Fact]
    public async Task GetAsync_NotFound_ReturnsNull()
    {
        // Arrange
        var client = CreateClient(new JsonHandler(null, HttpStatusCode.NotFound));

        // Act
        var result = await client.GetAsync(Guid.NewGuid());

        // Assert
        result.Should().BeNull();
    }

    [Fact]
    public async Task GetAsync_OnError_ReturnsNull()
    {
        // Arrange
        var client = CreateClient(new JsonHandler(null, HttpStatusCode.InternalServerError));

        // Act
        var result = await client.GetAsync(Guid.NewGuid());

        // Assert
        result.Should().BeNull();
    }
}
