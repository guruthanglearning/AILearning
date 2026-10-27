using FluentAssertions;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Models;

public class AgentRequestResponseTests
{
    [Fact]
    public void AgentResponse_Ok_SetsSuccessTrue()
    {
        // Arrange & Act
        var response = AgentResponse.Ok("content", "TestAgent", TimeSpan.FromSeconds(1));

        // Assert
        response.Success.Should().BeTrue();
        response.Content.Should().Be("content");
        response.AgentName.Should().Be("TestAgent");
        response.Duration.Should().Be(TimeSpan.FromSeconds(1));
        response.ErrorMessage.Should().BeNull();
    }

    [Fact]
    public void AgentResponse_Fail_SetsSuccessFalse()
    {
        // Arrange & Act
        var response = AgentResponse.Fail("API timeout", "TestAgent");

        // Assert
        response.Success.Should().BeFalse();
        response.ErrorMessage.Should().Be("API timeout");
        response.AgentName.Should().Be("TestAgent");
        response.Content.Should().BeEmpty();
    }

    [Fact]
    public void AgentRequest_DefaultContext_IsEmpty()
    {
        // Arrange & Act
        var request = new AgentRequest { Task = "Do something" };

        // Assert
        request.Context.Should().BeEmpty();
        request.PreviousFeedback.Should().BeNull();
    }

    [Fact]
    public void OrchestratorRequest_DefaultMaxReviewLoops_IsThree()
    {
        // Arrange & Act
        var request = new OrchestratorRequest { Requirement = "Build something" };

        // Assert
        request.MaxReviewLoops.Should().Be(3);
    }

    [Fact]
    public void OrchestratorRequest_DefaultSkipAgents_IsEmpty()
    {
        // Arrange & Act
        var request = new OrchestratorRequest { Requirement = "Build something" };

        // Assert
        request.SkipAgents.Should().BeEmpty();
    }

    [Fact]
    public void OrchestratorResponse_Success_ContainsSessionId()
    {
        // Arrange & Act
        var response = new OrchestratorResponse
        {
            Success = true,
            SessionId = Guid.NewGuid()
        };

        // Assert
        response.SessionId.Should().NotBe(Guid.Empty);
    }

    [Fact]
    public void AgentResponse_Fail_DefaultsToInternalFailureKind()
    {
        var response = AgentResponse.Fail("boom", "TestAgent");

        response.FailureKind.Should().Be(AgentFailureKind.Internal);
    }

    [Fact]
    public void AgentResponse_Fail_WithKind_SetsFailureKind()
    {
        var response = AgentResponse.Fail("invalid x-api-key", "TestAgent", AgentFailureKind.Authentication);

        response.FailureKind.Should().Be(AgentFailureKind.Authentication);
    }

    [Fact]
    public void AgentResponse_Ok_HasNoFailureKind()
    {
        var response = AgentResponse.Ok("content", "TestAgent", TimeSpan.FromSeconds(1));

        response.FailureKind.Should().Be(AgentFailureKind.None);
    }

    [Fact]
    public void AgentFailedException_CarriesAgentNameKindAndMessage()
    {
        var ex = new AgentFailedException("Product Manager", "invalid x-api-key", AgentFailureKind.Authentication);

        ex.AgentName.Should().Be("Product Manager");
        ex.Kind.Should().Be(AgentFailureKind.Authentication);
        ex.Message.Should().Be("Agent 'Product Manager' failed: invalid x-api-key");
    }

    [Fact]
    public void AgentFailureKind_SerializesAsString()
    {
        var json = System.Text.Json.JsonSerializer.Serialize(new OrchestratorResponse { FailureKind = AgentFailureKind.RateLimited });

        json.Should().Contain("\"FailureKind\":\"RateLimited\"");
    }
}
