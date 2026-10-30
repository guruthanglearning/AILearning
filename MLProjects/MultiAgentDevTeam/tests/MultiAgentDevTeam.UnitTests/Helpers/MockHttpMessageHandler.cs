using System.Net;
using System.Text;
using System.Text.Json;

namespace MultiAgentDevTeam.UnitTests.Helpers;

/// <summary>
/// Intercepts outgoing HTTP calls so BaseAgent tests never hit a real Anthropic endpoint.
/// Agents stream their responses, so successful replies are sent as server-sent events.
/// </summary>
public class MockHttpMessageHandler : HttpMessageHandler
{
    private readonly string _body;
    private readonly string _mediaType;
    private readonly HttpStatusCode _statusCode;

    public int CallCount { get; private set; }
    public HttpRequestMessage? LastRequest { get; private set; }

    /// <summary>The body of the last request, read before the SDK disposes it.</summary>
    public string? LastRequestBody { get; private set; }

    public MockHttpMessageHandler(
        string responseContent = "Mock agent response",
        HttpStatusCode statusCode = HttpStatusCode.OK)
    {
        _statusCode = statusCode;
        (_body, _mediaType) = statusCode == HttpStatusCode.OK
            ? (BuildStream(responseContent), "text/event-stream")
            : (BuildError(statusCode), "application/json");
    }

    private MockHttpMessageHandler(string sseBody)
    {
        _statusCode = HttpStatusCode.OK;
        _body = sseBody;
        _mediaType = "text/event-stream";
    }

    public static MockHttpMessageHandler WithStopReason(string text, string stopReason) =>
        new(BuildStream(text, stopReason: stopReason));

    public static MockHttpMessageHandler WithNoTextContent() =>
        new(BuildStream(text: null));

    public static MockHttpMessageHandler WithUsage(
        string model, long input, long output, long cacheWrite = 0, long cacheRead = 0) =>
        new(BuildStream("usage test", model: model, input: input, output: output, cacheWrite: cacheWrite, cacheRead: cacheRead));

    protected override async Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        CallCount++;
        LastRequest = request;
        if (request.Content is not null)
            LastRequestBody = await request.Content.ReadAsStringAsync(cancellationToken);

        return new HttpResponseMessage(_statusCode)
        {
            Content = new StringContent(_body, Encoding.UTF8, _mediaType)
        };
    }

    /// <summary>Builds the event sequence the Messages API streams for one reply.</summary>
    private static string BuildStream(
        string? text,
        string stopReason = "end_turn",
        string model = "claude-opus-5-5",
        long input = 10,
        long output = 5,
        long cacheWrite = 0,
        long cacheRead = 0)
    {
        var events = new List<(string Name, object Data)>
        {
            ("message_start", new
            {
                type = "message_start",
                message = new
                {
                    id = $"msg_test_{Guid.NewGuid():N}",
                    type = "message",
                    role = "assistant",
                    content = Array.Empty<object>(),
                    model,
                    stop_reason = (string?)null,
                    stop_sequence = (string?)null,
                    usage = new
                    {
                        input_tokens = input,
                        output_tokens = 1,
                        cache_creation_input_tokens = cacheWrite,
                        cache_read_input_tokens = cacheRead
                    }
                }
            })
        };

        if (text is not null)
        {
            events.Add(("content_block_start", new { type = "content_block_start", index = 0, content_block = new { type = "text", text = "" } }));
            events.Add(("content_block_delta", new { type = "content_block_delta", index = 0, delta = new { type = "text_delta", text } }));
            events.Add(("content_block_stop", new { type = "content_block_stop", index = 0 }));
        }

        events.Add(("message_delta", new
        {
            type = "message_delta",
            delta = new { stop_reason = stopReason, stop_sequence = (string?)null },
            usage = new
            {
                input_tokens = input,
                output_tokens = output,
                cache_creation_input_tokens = cacheWrite,
                cache_read_input_tokens = cacheRead
            }
        }));
        events.Add(("message_stop", new { type = "message_stop" }));

        var sb = new StringBuilder();
        foreach (var (name, data) in events)
            sb.Append($"event: {name}\ndata: {JsonSerializer.Serialize(data)}\n\n");
        return sb.ToString();
    }

    private static string BuildError(HttpStatusCode status) => JsonSerializer.Serialize(new
    {
        type = "error",
        error = new { type = "api_error", message = $"mock {(int)status} error" }
    });
}
