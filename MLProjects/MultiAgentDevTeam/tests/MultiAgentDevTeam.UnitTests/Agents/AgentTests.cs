using FluentAssertions;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Agents;

/// <summary>
/// Tests agent metadata contracts — name, output type, configuration.
/// Full Claude API calls are tested in integration tests.
/// </summary>
public class AgentMetadataTests
{
    [Theory]
    [InlineData(typeof(MultiAgentDevTeam.PMAgent.PMAgent),        "Product Manager",   ArtifactType.Requirements)]
    [InlineData(typeof(MultiAgentDevTeam.ArchitectAgent.ArchitectAgent), "Software Architect", ArtifactType.Architecture)]
    [InlineData(typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent), "Software Developer", ArtifactType.SourceCode)]
    [InlineData(typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent),   "Code Reviewer",      ArtifactType.ReviewNotes)]
    [InlineData(typeof(MultiAgentDevTeam.QAAgent.QAAgent),               "QA Engineer",        ArtifactType.TestResults)]
    [InlineData(typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent),    "Security Engineer",  ArtifactType.SecurityReport)]
    [InlineData(typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent),        "DevOps Engineer",    ArtifactType.DeploymentConfig)]
    [InlineData(typeof(MultiAgentDevTeam.DocsAgent.DocsAgent),            "Technical Writer",   ArtifactType.Documentation)]
    public void Agent_HasCorrectNameAndOutputType(Type agentType, string expectedName, ArtifactType expectedOutput)
    {
        // Arrange — create agent with null client (testing metadata only)
        var agent = AgentFactory.CreateWithNullClient(agentType);

        // Assert
        agent.Name.Should().Be(expectedName);
        agent.OutputType.Should().Be(expectedOutput);
    }

    [Fact]
    public void AllAgentOutputTypes_AreUnique()
    {
        // Arrange
        var agentTypes = new[]
        {
            typeof(MultiAgentDevTeam.PMAgent.PMAgent),
            typeof(MultiAgentDevTeam.ArchitectAgent.ArchitectAgent),
            typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent),
            typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent),
            typeof(MultiAgentDevTeam.QAAgent.QAAgent),
            typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent),
            typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent),
            typeof(MultiAgentDevTeam.DocsAgent.DocsAgent),
        };

        // Act
        var outputTypes = agentTypes.Select(t => AgentFactory.CreateWithNullClient(t).OutputType).ToList();

        // Assert
        outputTypes.Should().OnlyHaveUniqueItems("each agent must own exactly one artifact type");
    }

    [Fact]
    public void AllAgentNames_AreUnique()
    {
        // Arrange
        var agentTypes = new[]
        {
            typeof(MultiAgentDevTeam.PMAgent.PMAgent),
            typeof(MultiAgentDevTeam.ArchitectAgent.ArchitectAgent),
            typeof(MultiAgentDevTeam.DeveloperAgent.DeveloperAgent),
            typeof(MultiAgentDevTeam.ReviewerAgent.ReviewerAgent),
            typeof(MultiAgentDevTeam.QAAgent.QAAgent),
            typeof(MultiAgentDevTeam.SecurityAgent.SecurityAgent),
            typeof(MultiAgentDevTeam.DevOpsAgent.DevOpsAgent),
            typeof(MultiAgentDevTeam.DocsAgent.DocsAgent),
        };

        // Act
        var names = agentTypes.Select(t => AgentFactory.CreateWithNullClient(t).Name).ToList();

        // Assert
        names.Should().OnlyHaveUniqueItems("each agent must have a unique name");
    }
}
