using Anthropic.SDK;
using Anthropic.SDK.Messaging;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Interfaces;
using MultiAgentDevTeam.Shared.Models;
using System.Diagnostics;

namespace MultiAgentDevTeam.Shared.Agents;

public abstract class BaseAgent : IAgent
{
    private readonly AnthropicClient _client;
    protected readonly ILogger Logger;

    protected BaseAgent(AnthropicClient client, ILogger logger)
    {
        _client = client;
        Logger = logger;
    }

    public abstract string Name { get; }
    public abstract ArtifactType OutputType { get; }
    protected abstract string SystemPrompt { get; }
    protected virtual string Model => "claude-opus-4-6";
    protected virtual int MaxTokens => 8192;

    public async Task<AgentResponse> RunAsync(AgentRequest request, CancellationToken cancellationToken = default)
    {
        var stopwatch = Stopwatch.StartNew();
        Logger.LogInformation("[{Agent}] Starting task: {Task}", Name, request.Task[..Math.Min(80, request.Task.Length)]);

        try
        {
            var userContent = BuildUserContent(request);
            var messages = new List<Message>
            {
                new() { Role = RoleType.User, Content = userContent }
            };

            var response = await _client.Messages.GetClaudeMessageAsync(
                new MessageParameters
                {
                    Model = Model,
                    MaxTokens = MaxTokens,
                    SystemMessage = SystemPrompt,
                    Messages = messages
                }, null, cancellationToken);

            var content = response.Content.OfType<TextContent>().FirstOrDefault()?.Text ?? string.Empty;
            stopwatch.Stop();

            Logger.LogInformation("[{Agent}] Completed in {Duration}ms", Name, stopwatch.ElapsedMilliseconds);
            return AgentResponse.Ok(content, Name, stopwatch.Elapsed);
        }
        catch (Exception ex)
        {
            stopwatch.Stop();
            Logger.LogError(ex, "[{Agent}] Failed after {Duration}ms", Name, stopwatch.ElapsedMilliseconds);
            return AgentResponse.Fail(ex.Message, Name);
        }
    }

    private string BuildUserContent(AgentRequest request)
    {
        var parts = new List<string>();

        if (request.Context.Count > 0)
        {
            parts.Add("## Context from previous agents:");
            foreach (var (key, value) in request.Context)
                parts.Add($"### {key}\n{value}");
        }

        if (!string.IsNullOrWhiteSpace(request.PreviousFeedback))
            parts.Add($"## Feedback to address:\n{request.PreviousFeedback}");

        parts.Add($"## Your Task:\n{request.Task}");
        return string.Join("\n\n", parts);
    }
}
