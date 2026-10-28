using Microsoft.AspNetCore.Http;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.Orchestrator.Services;

/// <summary>
/// Translates a pipeline failure category into an HTTP status and a user-facing explanation.
/// Problems with the upstream Anthropic API are reported as 502/503/504 so callers can tell
/// them apart from genuine bugs in this service (500).
/// </summary>
public static class PipelineFailure
{
    public static int StatusCode(AgentFailureKind kind) => kind switch
    {
        // Not 401: the caller's credentials are fine — it's this service's configured key that was rejected
        AgentFailureKind.Authentication => StatusCodes.Status502BadGateway,
        AgentFailureKind.Upstream       => StatusCodes.Status502BadGateway,
        AgentFailureKind.RateLimited    => StatusCodes.Status503ServiceUnavailable,
        AgentFailureKind.Timeout        => StatusCodes.Status504GatewayTimeout,
        // The request itself was declined, so retrying it unchanged won't help
        AgentFailureKind.Refused        => StatusCodes.Status422UnprocessableEntity,
        _                               => StatusCodes.Status500InternalServerError
    };

    public static string Title(AgentFailureKind kind) => kind switch
    {
        AgentFailureKind.Authentication => "Anthropic API key rejected",
        AgentFailureKind.Upstream       => "Anthropic API error",
        AgentFailureKind.RateLimited    => "Anthropic API rate limit reached",
        AgentFailureKind.Timeout        => "Anthropic API request timed out",
        AgentFailureKind.Refused        => "Model declined the request",
        _                               => "Pipeline failed"
    };

    public static string Describe(AgentFailureKind kind) => kind switch
    {
        AgentFailureKind.Authentication =>
            "The Anthropic API rejected the configured API key. Check AgentConfiguration:AnthropicApiKey " +
            "(appsettings.secrets.json) or the ANTHROPIC_API_KEY environment variable, then restart the service.",
        AgentFailureKind.Upstream =>
            "The Anthropic API returned an error. This is usually transient — try again shortly.",
        AgentFailureKind.RateLimited =>
            "The Anthropic API rate limit was reached. Wait a moment and try again.",
        AgentFailureKind.Timeout =>
            "An agent did not get a response from the Anthropic API in time. Try again, or raise AgentConfiguration:TimeoutSeconds.",
        AgentFailureKind.Refused =>
            "The model declined the request for policy reasons, and no fallback model completed it. Rephrase the requirement and try again.",
        _ =>
            "An unexpected error occurred while running the pipeline. See the service logs for details."
    };

    /// <summary>Builds the ProblemDetails result returned by the blocking pipeline endpoints.</summary>
    public static IResult ToProblem(OrchestratorResponse response) =>
        Results.Problem(
            detail: $"{Describe(response.FailureKind)} ({response.ErrorMessage})",
            statusCode: StatusCode(response.FailureKind),
            title: Title(response.FailureKind),
            extensions: new Dictionary<string, object?>
            {
                ["sessionId"] = response.SessionId,
                ["failureKind"] = response.FailureKind.ToString()
            });
}
