using System.Net;
using System.Text;

namespace MultiAgentDevTeam.BlazorUI.UnitTests.Helpers;

public class SseMessageHandler : HttpMessageHandler
{
    private readonly string _sseBody;
    private readonly HttpStatusCode _statusCode;

    public SseMessageHandler(IEnumerable<string> messages, HttpStatusCode statusCode = HttpStatusCode.OK)
    {
        _statusCode = statusCode;
        var sb = new StringBuilder();
        foreach (var msg in messages)
        {
            var escaped = msg.Replace("\"", "\\\"");
            sb.AppendLine($"data: {{\"message\": \"{escaped}\"}}");
            sb.AppendLine();
        }
        _sseBody = sb.ToString();
    }

    public SseMessageHandler(string rawBody, HttpStatusCode statusCode)
    {
        _statusCode = statusCode;
        _sseBody = rawBody;
    }

    protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var response = new HttpResponseMessage(_statusCode)
        {
            Content = new StringContent(_sseBody, Encoding.UTF8, "text/event-stream")
        };
        return Task.FromResult(response);
    }
}
