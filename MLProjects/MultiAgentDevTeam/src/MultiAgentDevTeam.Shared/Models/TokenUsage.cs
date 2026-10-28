namespace MultiAgentDevTeam.Shared.Models;

/// <summary>Tokens billed for one agent call, as reported by the API, plus an estimated cost.</summary>
public record TokenUsage
{
    public string AgentName { get; init; } = string.Empty;
    public string Model { get; init; } = string.Empty;
    public long InputTokens { get; init; }
    public long OutputTokens { get; init; }
    public long CacheCreationInputTokens { get; init; }
    public long CacheReadInputTokens { get; init; }

    /// <summary>Null when the model isn't in <see cref="ModelPricing"/>.</summary>
    public decimal? EstimatedCostUsd { get; init; }
}

/// <summary>
/// List prices in USD per million tokens, used only to estimate spend in logs.
/// Check https://www.anthropic.com/pricing before relying on these numbers.
/// </summary>
public static class ModelPricing
{
    private record Rates(decimal Input, decimal Output, decimal CacheRead);

    // Cache writes (5-minute TTL) bill at 1.25x the input rate
    private const decimal CacheWriteMultiplier = 1.25m;

    private static readonly Dictionary<string, Rates> ByModel = new(StringComparer.OrdinalIgnoreCase)
    {
        ["claude-fable-5-1"]  = new(10m, 50m, 0.25m),
        ["claude-opus-5-5"]   = new(4m, 20m, 0.20m),
        ["claude-opus-5"]     = new(5m, 25m, 0.50m),
        ["claude-opus-4-8"]   = new(5m, 25m, 0.50m),
        ["claude-opus-4-7"]   = new(5m, 25m, 0.50m),
        ["claude-opus-4-6"]   = new(5m, 25m, 0.50m),
        ["claude-sonnet-5-5"] = new(2m, 10m, 0.20m),
        ["claude-sonnet-5"]   = new(2m, 10m, 0.20m),
        ["claude-sonnet-4-6"] = new(3m, 15m, 0.30m),
        ["claude-haiku-5-5"]  = new(0.10m, 0.50m, 0.01m),
        ["claude-haiku-4-5"]  = new(1m, 5m, 0.10m),
    };

    // Haiku 5.5 bills prompts over 100K tokens at a higher rate
    private const long HaikuLongPromptThreshold = 100_000;
    private static readonly Rates HaikuLongPrompt = new(0.50m, 2.50m, 0.05m);

    public static decimal? EstimateCostUsd(string model, long input, long output, long cacheWrite, long cacheRead)
    {
        // Longest matching prefix, so "claude-opus-5-5" doesn't resolve to "claude-opus-5"
        var key = ByModel.Keys
            .Where(k => model.StartsWith(k, StringComparison.OrdinalIgnoreCase))
            .OrderByDescending(k => k.Length)
            .FirstOrDefault();
        if (key is null)
            return null;

        var rates = ByModel[key];
        if (key == "claude-haiku-5-5" && input + cacheWrite + cacheRead > HaikuLongPromptThreshold)
            rates = HaikuLongPrompt;

        var cost = input * rates.Input
                 + output * rates.Output
                 + cacheWrite * rates.Input * CacheWriteMultiplier
                 + cacheRead * rates.CacheRead;
        return Math.Round(cost / 1_000_000m, 4);
    }
}
