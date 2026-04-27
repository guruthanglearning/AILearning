using System.Runtime.CompilerServices;
using System.Text.Json;
using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Services;

public class PipelineClient : IPipelineClient
{
    private readonly HttpClient _http;
    private readonly ILogger<PipelineClient> _logger;

    public PipelineClient(HttpClient http, ILogger<PipelineClient> logger)
    {
        _http = http;
        _logger = logger;
    }

    public async IAsyncEnumerable<string> StreamAsync(
        PipelineRequest request,
        [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        using var httpRequest = new HttpRequestMessage(HttpMethod.Post, "/api/run/stream")
        {
            Content = JsonContent.Create(request)
        };

        HttpResponseMessage response;
        try
        {
            response = await _http.SendAsync(httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);
            response.EnsureSuccessStatusCode();
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "Failed to connect to pipeline API");
            throw;
        }

        using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
        using var reader = new StreamReader(stream);

        while (!cancellationToken.IsCancellationRequested)
        {
            var line = await reader.ReadLineAsync(cancellationToken);
            if (line is null) break;
            if (!line.StartsWith("data:", StringComparison.Ordinal)) continue;

            var json = line["data:".Length..].Trim();
            if (string.IsNullOrWhiteSpace(json)) continue;

            string? message = null;
            try
            {
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.TryGetProperty("message", out var msgProp))
                    message = msgProp.GetString();
            }
            catch (JsonException ex)
            {
                _logger.LogWarning(ex, "Failed to parse SSE event: {Json}", json);
                continue;
            }

            if (message is not null)
                yield return message;
        }
    }
}
