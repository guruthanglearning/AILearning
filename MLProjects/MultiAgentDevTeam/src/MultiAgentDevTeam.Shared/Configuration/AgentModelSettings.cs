namespace MultiAgentDevTeam.Shared.Configuration;

/// <summary>
/// Model, effort and output budget for one agent. Each agent declares its defaults;
/// <c>AgentConfiguration:Agents:{key}</c> overrides any of them without a code change.
/// </summary>
public record AgentModelSettings
{
    public required string Model { get; init; }

    /// <summary>How hard the model thinks: low, medium, high, xhigh or max.</summary>
    public string Effort { get; init; } = "medium";

    /// <summary>Backstop on output (thinking included); the model is never billed for unused headroom.</summary>
    public int MaxTokens { get; init; } = 32000;

    /// <summary>
    /// Marks the context block for prompt caching. Cache writes bill at 1.25x input, so this
    /// only pays off for agents re-run with the same context, like the Developer review loop.
    /// </summary>
    public bool CacheContext { get; init; }
}

/// <summary>Configuration override for an agent's <see cref="AgentModelSettings"/>; unset fields keep the agent's default.</summary>
public class AgentModelOverride
{
    public string? Model { get; set; }
    public string? Effort { get; set; }
    public int? MaxTokens { get; set; }
    public bool? CacheContext { get; set; }

    public AgentModelSettings ApplyTo(AgentModelSettings defaults) => defaults with
    {
        Model = string.IsNullOrWhiteSpace(Model) ? defaults.Model : Model,
        Effort = string.IsNullOrWhiteSpace(Effort) ? defaults.Effort : Effort,
        MaxTokens = MaxTokens is > 0 ? MaxTokens.Value : defaults.MaxTokens,
        CacheContext = CacheContext ?? defaults.CacheContext
    };
}
