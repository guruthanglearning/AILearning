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
}
