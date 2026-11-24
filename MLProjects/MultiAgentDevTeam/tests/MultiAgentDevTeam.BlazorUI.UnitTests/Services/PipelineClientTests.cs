using FluentAssertions;
using Microsoft.Extensions.Logging.Abstractions;
using MultiAgentDevTeam.BlazorUI.Models;
using MultiAgentDevTeam.BlazorUI.Services;
using MultiAgentDevTeam.BlazorUI.UnitTests.Helpers;
using System.Net;
using System.Net.Sockets;
using Xunit;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Services;

public class PipelineClientTests
{
    private static PipelineClient CreateClient(HttpMessageHandler handler)
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

        // Assert — still an HttpRequestException, with a message that names the API and status
        var thrown = await act.Should().ThrowAsync<HttpRequestException>();
        thrown.Which.StatusCode.Should().Be(HttpStatusCode.InternalServerError);
        thrown.Which.Message.Should().Contain("http://localhost:5000").And.Contain("500");
    }

    [Fact]
    public async Task StreamAsync_ApiNotRunning_ThrowsMessageNamingUrlAndHealthCheck()
    {
        // Arrange — the Orchestrator isn't listening on the configured port
        var refused = new HttpRequestException(
            "No connection could be made", new SocketException((int)SocketError.ConnectionRefused));
        var client = CreateClient(new ThrowingHandler(refused));

        // Act
        var act = async () =>
        {
            await foreach (var _ in client.StreamAsync(new PipelineRequest { Requirement = "x" })) { }
        };

        // Assert
        var thrown = await act.Should().ThrowAsync<HttpRequestException>();
        thrown.Which.Message.Should().Contain("Cannot connect to the Orchestrator API at http://localhost:5000")
            .And.Contain("http://localhost:5000/health");
        thrown.Which.InnerException.Should().BeSameAs(refused);
    }

    [Fact]
    public async Task StreamAsync_OtherNetworkError_ThrowsMessageWithOriginalReason()
    {
        // Arrange
        var client = CreateClient(new ThrowingHandler(new HttpRequestException("DNS lookup failed")));

        // Act
        var act = async () =>
        {
            await foreach (var _ in client.StreamAsync(new PipelineRequest { Requirement = "x" })) { }
        };

        // Assert
        (await act.Should().ThrowAsync<HttpRequestException>())
            .Which.Message.Should().Be("Unable to reach the Orchestrator API at http://localhost:5000: DNS lookup failed");
    }

    [Fact]
    public async Task StreamAsync_CancelledBeforeResponse_ThrowsOperationCanceled()
    {
        // Arrange — cancelling while connecting must not be reported as a connection error
        var client = CreateClient(new ThrowingHandler(new TaskCanceledException()));

        // Act
        var act = async () =>
        {
            await foreach (var _ in client.StreamAsync(new PipelineRequest { Requirement = "x" })) { }
        };

        // Assert
        await act.Should().ThrowAsync<OperationCanceledException>();
    }

    private sealed class ThrowingHandler(Exception exception) : HttpMessageHandler
    {
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
            => Task.FromException<HttpResponseMessage>(exception);
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
