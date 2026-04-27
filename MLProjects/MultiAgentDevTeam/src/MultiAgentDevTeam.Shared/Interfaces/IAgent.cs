using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.Shared.Interfaces;

public interface IAgent
{
    string Name { get; }
    ArtifactType OutputType { get; }
    Task<AgentResponse> RunAsync(AgentRequest request, CancellationToken cancellationToken = default);
}
