using Anthropic;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Interfaces;

namespace MultiAgentDevTeam.UnitTests.Agents;

/// <summary>
/// Creates agent instances the way DI does: (AnthropicClient, ILogger&lt;T&gt;, IOptions&lt;AgentConfiguration&gt;).
/// </summary>
internal static class AgentFactory
{
    /// <summary>For metadata-only tests: the client is never called.</summary>
    public static IAgent CreateWithNullClient(Type agentType) =>
        Create(agentType, new AnthropicClient { ApiKey = "test-key-not-used" });

    /// <summary>Routes every API call through <paramref name="handler"/>, with SDK retries off.</summary>
    public static IAgent Create(Type agentType, HttpMessageHandler handler, AgentConfiguration? config = null) =>
        Create(agentType, new AnthropicClient
        {
            ApiKey = "test-key-not-used",
            HttpClient = new HttpClient(handler),
            MaxRetries = 0
        }, config);

    private static IAgent Create(Type agentType, AnthropicClient client, AgentConfiguration? config = null)
    {
        var logger = Activator.CreateInstance(typeof(NullLogger<>).MakeGenericType(agentType))!;
        var options = Options.Create(config ?? new AgentConfiguration());
        return (IAgent)Activator.CreateInstance(agentType, client, logger, options)!;
    }
}
