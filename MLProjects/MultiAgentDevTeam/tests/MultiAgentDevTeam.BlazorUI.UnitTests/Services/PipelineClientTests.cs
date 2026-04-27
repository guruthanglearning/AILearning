using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Services;
using MultiAgentDevTeam.BlazorUI.UnitTests.Helpers;
using System.Net;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Services;

public class PipelineClientTests
{
    private static PipelineClient CreateClient(SseMessageHandler handler)
    {
        var http = new HttpClient(handler) { BaseAddress = new Uri("http://localhost:5000") };
        return new PipelineClient(http, NullLogger<PipelineClient>.Instance);
    }

    [Fact]
    public async Task StreamAsync_ParsesSSEMessages_ReturnsAllMessages()
    {
        // Arrange
        var messages = new[] { "🤖 PM started", "✅ PM completed", "🤖 Architect started" };
        var client = CreateClient(new SseMessageHandler(messages));
        var request = new PipelineRequest { Requirement = "Build something" };

        // Act
        var received = new List<string>();
        await foreach (var msg in client.StreamAsync(request))
            received.Add(msg);

        // Assert
        received.Should().BeEquivalentTo(messages);
    }

    [Fact]
    public async Task StreamAsync_IgnoresNonDataLines_OnlyReturnsDataLines()
    {
        // Arrange — mix of comment lines and data lines
        var rawBody = ": keep-alive\n\ndata: {\"message\": \"hello\"}\n\n: another comment\n\ndata: {\"message\": \"world\"}\n\n";
        var client = CreateClient(new SseMessageHandler(rawBody, HttpStatusCode.OK));
        var request = new PipelineRequest { Requirement = "Build something" };

        // Act
        var received = new List<string>();
        await foreach (var msg in client.StreamAsync(request))
            received.Add(msg);

        // Assert
        received.Should().BeEquivalentTo(["hello", "world"]);
    }

    [Fact]
    public async Task StreamAsync_IgnoresMalformedJson_ContinuesWithValidLines()
    {
        // Arrange
        var rawBody = "data: {\"message\": \"valid\"}\n\ndata: NOT_JSON\n\ndata: {\"message\": \"also valid\"}\n\n";
        var client = CreateClient(new SseMessageHandler(rawBody, HttpStatusCode.OK));
        var request = new PipelineRequest { Requirement = "Build something" };

        // Act
        var received = new List<string>();
        await foreach (var msg in client.StreamAsync(request))
            received.Add(msg);

        // Assert — only valid JSON lines are returned
        received.Should().BeEquivalentTo(["valid", "also valid"]);
    }

    [Fact]
    public async Task StreamAsync_NonSuccessStatus_ThrowsHttpRequestException()
    {
        // Arrange
        var client = CreateClient(new SseMessageHandler([], HttpStatusCode.InternalServerError));
        var request = new PipelineRequest { Requirement = "Build something" };

        // Act
        var act = async () =>
        {
            await foreach (var _ in client.StreamAsync(request)) { }
        };

        // Assert
        await act.Should().ThrowAsync<HttpRequestException>();
    }

    [Fact]
    public async Task StreamAsync_CancellationToken_StopsStream()
    {
        // Arrange — return many messages but cancel after first
        var messages = Enumerable.Range(1, 100).Select(i => $"message {i}");
        var client = CreateClient(new SseMessageHandler(messages));
        var request = new PipelineRequest { Requirement = "Build something" };
        var cts = new CancellationTokenSource();

        // Act
        var received = new List<string>();
        await foreach (var msg in client.StreamAsync(request, cts.Token))
        {
            received.Add(msg);
            cts.Cancel(); // cancel after first message
        }

        // Assert — much fewer than 100 messages received
        received.Count.Should().BeLessThan(100);
    }

    [Fact]
    public async Task StreamAsync_EmptyStream_ReturnsNoMessages()
    {
        // Arrange
        var client = CreateClient(new SseMessageHandler([]));
        var request = new PipelineRequest { Requirement = "Build something" };

        // Act
        var received = new List<string>();
        await foreach (var msg in client.StreamAsync(request))
            received.Add(msg);

        // Assert
        received.Should().BeEmpty();
    }

    [Fact]
    public async Task StreamAsync_EventWithoutMessageField_IsSkipped()
    {
        // Arrange
        var rawBody = "data: {\"other\": \"field\"}\n\ndata: {\"message\": \"valid\"}\n\n";
        var client = CreateClient(new SseMessageHandler(rawBody, HttpStatusCode.OK));
        var request = new PipelineRequest { Requirement = "Build something" };

        // Act
        var received = new List<string>();
        await foreach (var msg in client.StreamAsync(request))
            received.Add(msg);

        // Assert
        received.Should().BeEquivalentTo(["valid"]);
    }
}
