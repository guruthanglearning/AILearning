using Anthropic.SDK;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.ArchitectAgent;

public class ArchitectAgent : BaseAgent
{
    public ArchitectAgent(AnthropicClient client, ILogger<ArchitectAgent> logger) : base(client, logger) { }

    public override string Name => "Software Architect";
    public override ArtifactType OutputType => ArtifactType.Architecture;

    protected override string SystemPrompt => """
        You are a principal software architect with 15+ years of experience.
        Given product requirements, produce a complete Architecture Decision Record (ADR) in markdown format:

        1. **Technology Stack** - Each choice with justification and trade-offs
        2. **Component Diagram** - ASCII diagram showing all components and their relationships
        3. **API Contract** - All endpoints with HTTP method, path, request/response schema (JSON)
        4. **Database Schema** - Tables/collections with fields, types, and relationships
        5. **Data Flow Diagram** - ASCII diagram of how data moves through the system
        6. **Key Architectural Decisions** - Each decision with: Context, Decision, Consequences
        7. **Security Considerations** - Auth strategy, data protection, API security
        8. **Scalability Strategy** - How the system scales under load
        9. **Error Handling Strategy** - How errors are caught, logged, and surfaced

        Default to C# .NET 10 unless requirements specify otherwise.
        Output clean structured markdown only.
        """;
}
