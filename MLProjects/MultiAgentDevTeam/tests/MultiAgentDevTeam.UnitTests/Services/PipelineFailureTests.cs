using FluentAssertions;
using Microsoft.AspNetCore.Http;
using MultiAgentDevTeam.Orchestrator.Services;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Services;

public class PipelineFailureTests
{
    [Theory]
    [InlineData(AgentFailureKind.Authentication, StatusCodes.Status502BadGateway)]
    [InlineData(AgentFailureKind.Upstream, StatusCodes.Status502BadGateway)]
    [InlineData(AgentFailureKind.RateLimited, StatusCodes.Status503ServiceUnavailable)]
    [InlineData(AgentFailureKind.Timeout, StatusCodes.Status504GatewayTimeout)]
    [InlineData(AgentFailureKind.Refused, StatusCodes.Status422UnprocessableEntity)]
    [InlineData(AgentFailureKind.Internal, StatusCodes.Status500InternalServerError)]
    [InlineData(AgentFailureKind.None, StatusCodes.Status500InternalServerError)]
    public void StatusCode_MapsEachKind(AgentFailureKind kind, int expected) =>
        PipelineFailure.StatusCode(kind).Should().Be(expected);

    [Fact]
    public void StatusCode_Authentication_IsNot401()
    {
        // The caller's credentials are fine; the service's own upstream key was rejected
        PipelineFailure.StatusCode(AgentFailureKind.Authentication).Should().NotBe(StatusCodes.Status401Unauthorized);
    }

    [Theory]
    [InlineData(AgentFailureKind.Authentication, "API key rejected")]
    [InlineData(AgentFailureKind.Upstream, "Anthropic API error")]
    [InlineData(AgentFailureKind.RateLimited, "rate limit")]
    [InlineData(AgentFailureKind.Timeout, "timed out")]
    [InlineData(AgentFailureKind.Refused, "declined")]
    [InlineData(AgentFailureKind.Internal, "Pipeline failed")]
    public void Title_DescribesEachKind(AgentFailureKind kind, string expected) =>
        PipelineFailure.Title(kind).Should().Contain(expected);

    [Theory]
    [InlineData(AgentFailureKind.Authentication, "AnthropicApiKey")]
    [InlineData(AgentFailureKind.Upstream, "transient")]
    [InlineData(AgentFailureKind.RateLimited, "rate limit")]
    [InlineData(AgentFailureKind.Timeout, "TimeoutSeconds")]
    [InlineData(AgentFailureKind.Refused, "Rephrase")]
    [InlineData(AgentFailureKind.Internal, "service logs")]
    public void Describe_GivesActionableGuidance(AgentFailureKind kind, string expected) =>
        PipelineFailure.Describe(kind).Should().Contain(expected);
}
