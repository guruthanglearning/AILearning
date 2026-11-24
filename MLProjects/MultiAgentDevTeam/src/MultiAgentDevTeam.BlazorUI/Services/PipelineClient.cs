using System.Runtime.CompilerServices;
using System.Net.Sockets;
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
        catch (HttpRequestException ex)
        {
            _logger.LogError(ex, "Failed to connect to pipeline API at {BaseAddress}", _http.BaseAddress);
            throw new HttpRequestException(DescribeFailure(ex), ex, ex.StatusCode);
        }
        catch (Exception ex) when (ex is not OperationCanceledException)
        {
            _logger.LogError(ex, "Failed to connect to pipeline API at {BaseAddress}", _http.BaseAddress);
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

    // The Home page shows this message, so it names the URL the UI is configured to call
    // (OrchestratorApi:BaseUrl) and what to check.
    private string DescribeFailure(HttpRequestException ex)
    {
        var baseAddress = _http.BaseAddress?.ToString().TrimEnd('/') ?? "(OrchestratorApi:BaseUrl not set)";

        if (ex.StatusCode is { } status)
            return $"The Orchestrator API at {baseAddress} returned {(int)status} {status}.";

        if (ex.InnerException is SocketException { SocketErrorCode: SocketError.ConnectionRefused })
            return $"Cannot connect to the Orchestrator API at {baseAddress}. " +
                   $"Start MultiAgentDevTeam.Orchestrator and check that {baseAddress}/health responds.";

        return $"Unable to reach the Orchestrator API at {baseAddress}: {ex.Message}";
    }
}
