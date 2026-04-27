using Anthropic.SDK;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.DocsAgent;

public class DocsAgent : BaseAgent
{
    public DocsAgent(AnthropicClient client, ILogger<DocsAgent> logger) : base(client, logger) { }

    public override string Name => "Technical Writer";
    public override ArtifactType OutputType => ArtifactType.Documentation;

    protected override string SystemPrompt => """
        You are a technical writer who produces clear, comprehensive developer documentation.
        Given all project artifacts, produce complete documentation in markdown:

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

        Write for developers who are new to the project. Be complete, accurate, and clear.
        """;
}
