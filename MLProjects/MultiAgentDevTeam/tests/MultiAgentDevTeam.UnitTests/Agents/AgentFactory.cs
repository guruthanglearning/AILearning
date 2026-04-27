using Anthropic.SDK;
using Microsoft.Extensions.Logging.Abstractions;
using MultiAgentDevTeam.Shared.Interfaces;

namespace MultiAgentDevTeam.UnitTests.Agents;

/// <summary>
/// Factory for creating agent instances with a null Anthropic client for metadata-only tests.
/// </summary>
internal static class AgentFactory
{
    public static IAgent CreateWithNullClient(Type agentType)
    {
        // All agents share the same constructor pattern: (AnthropicClient, ILogger<T>)
        // We pass a real AnthropicClient with a dummy key — it won't be called in metadata tests
        var client = new AnthropicClient("test-key-not-used");

        var loggerType = typeof(NullLogger<>).MakeGenericType(agentType);
        var logger = Activator.CreateInstance(loggerType)!;

        return (IAgent)Activator.CreateInstance(agentType, client, logger)!;
    }
}
