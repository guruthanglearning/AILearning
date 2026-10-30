using FluentAssertions;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;
using Xunit;

namespace MultiAgentDevTeam.UnitTests.Models;

public class ModelPricingTests
{
    [Theory]
    [InlineData("claude-opus-5-5", 4.00, 20.00)]
    [InlineData("claude-opus-4-6", 5.00, 25.00)]
    [InlineData("claude-sonnet-5-5", 2.00, 10.00)]
    public void EstimateCostUsd_PricesInputAndOutputPerMillion(string model, double inputRate, double outputRate) =>
        ModelPricing.EstimateCostUsd(model, 1_000_000, 1_000_000, 0, 0)
            .Should().Be((decimal)inputRate + (decimal)outputRate);

    [Fact]
    public void EstimateCostUsd_UsesLongestMatchingPrefix()
    {
        // "claude-opus-5-5" also starts with "claude-opus-5", which is priced higher
        ModelPricing.EstimateCostUsd("claude-opus-5-5", 1_000_000, 0, 0, 0).Should().Be(4m);
        ModelPricing.EstimateCostUsd("claude-opus-5", 1_000_000, 0, 0, 0).Should().Be(5m);
    }

    [Fact]
    public void EstimateCostUsd_CacheWritesCostQuarterMoreThanInput() =>
        ModelPricing.EstimateCostUsd("claude-sonnet-5-5", 0, 0, 1_000_000, 0).Should().Be(2.50m);

    [Fact]
    public void EstimateCostUsd_CacheReadsUseCacheRate() =>
        ModelPricing.EstimateCostUsd("claude-opus-5-5", 0, 0, 0, 1_000_000).Should().Be(0.20m);

    [Fact]
    public void EstimateCostUsd_HaikuShortPrompt_UsesBaseTier() =>
        // 100K-token prompt at $0.10/M plus 1M output at $0.50/M
        ModelPricing.EstimateCostUsd("claude-haiku-5-5", 100_000, 1_000_000, 0, 0).Should().Be(0.51m);

    [Fact]
    public void EstimateCostUsd_HaikuLongPrompt_UsesHigherTier() =>
        ModelPricing.EstimateCostUsd("claude-haiku-5-5", 200_000, 0, 0, 0).Should().Be(0.10m);

    [Fact]
    public void EstimateCostUsd_UnknownModel_ReturnsNull() =>
        ModelPricing.EstimateCostUsd("some-other-model", 1000, 1000, 0, 0).Should().BeNull();
}

public class AgentModelSettingsTests
{
    private static readonly AgentModelSettings Defaults = new()
    {
        Model = "claude-opus-5-5",
        Effort = "high",
        MaxTokens = 64000,
        CacheContext = true
    };

    [Fact]
    public void ResolveAgent_NoOverride_ReturnsDefaults() =>
        new AgentConfiguration().ResolveAgent("Developer", Defaults).Should().Be(Defaults);

    [Fact]
    public void ResolveAgent_PartialOverride_KeepsUnsetFields()
    {
        var config = new AgentConfiguration();
        config.Agents["Developer"] = new AgentModelOverride { Model = "claude-sonnet-5-5" };

        var resolved = config.ResolveAgent("Developer", Defaults);

        resolved.Should().Be(Defaults with { Model = "claude-sonnet-5-5" });
    }

    [Fact]
    public void ResolveAgent_FullOverride_ReplacesEveryField()
    {
        var config = new AgentConfiguration();
        config.Agents["Developer"] = new AgentModelOverride
        {
            Model = "claude-haiku-5-5", Effort = "low", MaxTokens = 1000, CacheContext = false
        };

        config.ResolveAgent("Developer", Defaults).Should().Be(new AgentModelSettings
        {
            Model = "claude-haiku-5-5", Effort = "low", MaxTokens = 1000, CacheContext = false
        });
    }

    [Fact]
    public void ResolveAgent_KeyIsCaseInsensitive()
    {
        var config = new AgentConfiguration();
        config.Agents["developer"] = new AgentModelOverride { Effort = "max" };

        config.ResolveAgent("Developer", Defaults).Effort.Should().Be("max");
    }

    [Theory]
    [InlineData("", 0)]
    [InlineData("  ", -5)]
    public void ApplyTo_BlankOrNonPositiveValues_KeepDefaults(string blank, int tokens)
    {
        var overrides = new AgentModelOverride { Model = blank, Effort = blank, MaxTokens = tokens };

        overrides.ApplyTo(Defaults).Should().Be(Defaults);
    }
}
