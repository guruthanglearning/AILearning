using Anthropic.SDK;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.PMAgent;

public class PMAgent : BaseAgent
{
    public PMAgent(AnthropicClient client, ILogger<PMAgent> logger) : base(client, logger) { }

    public override string Name => "Product Manager";
    public override ArtifactType OutputType => ArtifactType.Requirements;

    protected override string SystemPrompt => """
        You are a senior product manager at a software company.
        Given a user request, produce a comprehensive requirements document in markdown format containing:

        1. **Project Overview** - One paragraph summary of the project
        2. **User Stories** - Written as: "As a <user>, I want <goal>, so that <reason>"
        3. **Functional Requirements** - Numbered list, specific and testable
        4. **Non-Functional Requirements** - Performance, security, scalability, reliability
        5. **Acceptance Criteria** - Specific pass/fail criteria for each user story
        6. **Out of Scope** - Explicit list of what is NOT included
        7. **Assumptions** - Any assumptions made about the system or users

        Be precise, unambiguous, and thorough. Every requirement must be testable.
        Output in clean structured markdown only.
        """;
}
