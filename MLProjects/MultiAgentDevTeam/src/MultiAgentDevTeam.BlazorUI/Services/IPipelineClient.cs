using MultiAgentDevTeam.BlazorUI.Models;

namespace MultiAgentDevTeam.BlazorUI.Services;

public interface IPipelineClient
{
    IAsyncEnumerable<string> StreamAsync(PipelineRequest request, CancellationToken cancellationToken = default);
}
