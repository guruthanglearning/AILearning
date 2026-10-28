using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.PMAgent;

public class PMAgent : BaseAgent
{
    public PMAgent(AnthropicClient client, ILogger<PMAgent> logger, IOptions<AgentConfiguration> options)
        : base(client, logger, options) { }

    public override string Name => "Product Manager";
    public override ArtifactType OutputType => ArtifactType.Requirements;

    // Requirements extraction is structured analysis; Sonnet handles it at a fraction of Opus cost
    protected override AgentModelSettings DefaultSettings => new()
    {
        Model = "claude-sonnet-5-5",
        Effort = "medium",
        MaxTokens = 16000
    };

    protected override string SystemPrompt => $$"""
        You are a senior product manager at a software company.
        Given a user request, produce a comprehensive requirements document in markdown format containing:

        1. **Project Overview** - One paragraph summary of the project
        2. **User Stories** - Written as: "As a <user>, I want <goal>, so that <reason>"
        3. **Functional Requirements** - Numbered list, specific and testable
        4. **Non-Functional Requirements** - Performance, security, scalability, reliability
        5. **Acceptance Criteria** - Specific pass/fail criteria for each user story
        6. **Out of Scope** - Explicit list of what is NOT included
        7. **Assumptions** - Any assumptions made about the system or users
        8. **Requirement Checklist** - End the document with a fenced block tagged
           `{{RequirementTracking.ChecklistFence}}` holding a JSON array, one object per requirement:

           ```{{RequirementTracking.ChecklistFence}}
           [{"id": "FR-1", "text": "Prints Hello, World! to the console", "kind": "code", "criterion": "stdout is exactly 'Hello, World!'"}]
           ```
           - id: the requirement's number above (FR-n or NFR-n)
           - kind: "code" when it is built into source or config files, "test" when it needs a test,
             "action" when it is something done outside the generated files (create the project in a
             given folder, run or open the app, deploy, install)

        Every explicit instruction in the user's request must map to at least one checklist entry,
        including where to put the project and what to do once it's built. Never drop one.
        If the request names no language or platform version, add a non-functional requirement for the
        team default: C# on .NET 10.

        Be precise, unambiguous, and thorough. Every requirement must be testable.
        Output in clean structured markdown only.
        """;
}
