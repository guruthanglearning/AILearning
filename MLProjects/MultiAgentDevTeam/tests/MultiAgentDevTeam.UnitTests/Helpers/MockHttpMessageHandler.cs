using System.Net;
using System.Text;

namespace MultiAgentDevTeam.UnitTests.Helpers;

/// <summary>
/// Intercepts outgoing HTTP calls so BaseAgent tests never hit a real Anthropic endpoint.
/// </summary>
public class MockHttpMessageHandler : HttpMessageHandler
{
    private readonly string _responseJson;
    private readonly HttpStatusCode _statusCode;

    public int CallCount { get; private set; }
    public HttpRequestMessage? LastRequest { get; private set; }

    public MockHttpMessageHandler(
        string responseContent = "Mock agent response",
        HttpStatusCode statusCode = HttpStatusCode.OK)
    {
        _statusCode = statusCode;
        _responseJson = BuildAnthropicResponse(responseContent);
    }

    private MockHttpMessageHandler(HttpStatusCode statusCode, string rawJson)
    {
        _statusCode = statusCode;
        _responseJson = rawJson;
    }

    public static MockHttpMessageHandler WithNoTextContent() =>
        new(HttpStatusCode.OK, BuildNoTextContentResponse());

    private static string BuildNoTextContentResponse() => $$"""
        {
          "id": "msg_test_{{Guid.NewGuid():N}}",
          "type": "message",
          "role": "assistant",
          "content": [],
          "model": "claude-opus-4-6",
          "stop_reason": "end_turn",
          "stop_sequence": null,
          "usage": { "input_tokens": 10, "output_tokens": 0 }
        }
        """;

    protected override Task<HttpResponseMessage> SendAsync(
        HttpRequestMessage request,
        CancellationToken cancellationToken)
    {
        CallCount++;
        LastRequest = request;

        var response = new HttpResponseMessage(_statusCode)
        {
            Content = new StringContent(_responseJson, Encoding.UTF8, "application/json")
        };

        return Task.FromResult(response);
    }

    /// <summary>
    /// Builds a minimal valid Anthropic Messages API response JSON.
    /// </summary>
    public static string BuildAnthropicResponse(string text) => $$"""
        {
          "id": "msg_test_{{Guid.NewGuid():N}}",
          "type": "message",
          "role": "assistant",
          "content": [{ "type": "text", "text": "{{EscapeJson(text)}}" }],
          "model": "claude-opus-4-6",
          "stop_reason": "end_turn",
          "stop_sequence": null,
          "usage": { "input_tokens": 10, "output_tokens": 5 }
        }
        """;

    private static string EscapeJson(string s) =>
        s.Replace("\\", "\\\\").Replace("\"", "\\\"").Replace("\n", "\\n");
}
