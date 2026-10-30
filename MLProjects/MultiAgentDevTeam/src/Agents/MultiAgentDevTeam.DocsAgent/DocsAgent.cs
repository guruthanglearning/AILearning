using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.DocsAgent;

public class DocsAgent : BaseAgent
{
    public DocsAgent(AnthropicClient client, ILogger<DocsAgent> logger, IOptions<AgentConfiguration> options)
        : base(client, logger, options) { }

    public override string Name => "Technical Writer";
    public override ArtifactType OutputType => ArtifactType.Documentation;

    // Summarising finished artifacts into docs needs little reasoning; Haiku is ~40x cheaper than Opus
    protected override AgentModelSettings DefaultSettings => new()
    {
        Model = "claude-haiku-5-5",
        Effort = "medium",
        MaxTokens = 32000
    };

    // A requested README or guide is delivered here, so Docs claims it like the code agents do
    protected override bool ReportsRequirementCoverage => true;

    protected override string SystemPrompt => """
        You are a technical writer who produces clear, accurate developer documentation.
        Given all project artifacts, produce documentation in markdown. For a small project a single
        concise README.md is enough; only write API_REFERENCE.md when the project exposes an API, and
        ARCHITECTURE.md when it has more than one component. Leave out README sections that don't apply.

        1. **README.md** - Include:
           - Project title and one-line description
           - Architecture diagram (ASCII)
           - Prerequisites and installation steps
           - Configuration (env vars table)
           - How to run locally
           - How to run with Docker
           - How to deploy to Kubernetes
           - API reference (all endpoints, request/response examples)
           - Running tests
           - Project structure tree
           - Contributing guide

        2. **API_REFERENCE.md** - Detailed API documentation:
           - Each endpoint with full curl examples
           - Request/response schemas
           - Error codes and their meanings
           - Authentication guide

        3. **ARCHITECTURE.md** - System design document:
           - Component overview
           - Data flow explanation
           - Key design decisions and rationale
           - Technology choices

        Write for developers who are new to the project. Be accurate and clear.
        """;
}
