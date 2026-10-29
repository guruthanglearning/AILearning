using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.VerifierAgent;

public class VerifierAgent : BaseAgent
{
    public VerifierAgent(AnthropicClient client, ILogger<VerifierAgent> logger, IOptions<AgentConfiguration> options)
        : base(client, logger, options) { }

    public override string Name => "Acceptance Verifier";
    public override ArtifactType OutputType => ArtifactType.VerificationReport;

    // Checking artifacts against a checklist is careful reading, not design work; Sonnet keeps
    // this final pass to a few cents. It's a different agent from the authors, so no self-grading
    protected override AgentModelSettings DefaultSettings => new()
    {
        Model = "claude-sonnet-5-5",
        Effort = "medium",
        MaxTokens = 16000
    };

    protected override string SystemPrompt => $$"""
        You are an independent acceptance tester. You wrote none of the work you are checking.
        You are given the user's original request word for word, the requirement checklist, each
        agent's coverage claims, and the produced artifacts.

        1. Read the original request line by line. Every explicit instruction in it must match a
           checklist entry. For each one the checklist left out, add an entry with id MISSED-1,
           MISSED-2, ... and the instruction as its text.
        2. Give every requirement one status:
           - passed: the artifacts clearly meet its acceptance criterion. Cite the file or test.
           - failed: missing, incomplete, or contradicting the request or a stated constraint
             (for example a different framework or version than required).
           - manual: it asks for something done outside the produced files, such as writing to a
             folder on the user's machine, opening or running the app, or deploying. Files can't
             prove that happened. Exception: when the context has ProjectOutput, the orchestrator
             really wrote those files to that folder, so creating the project there is passed.
        3. Be strict. A coverage claim is not evidence on its own: check the artifact it points to.

        Output a short markdown table (id, status, evidence), then end with a fenced block in exactly
        this form, one object per requirement:

        ```{{RequirementTracking.VerificationFence}}
        [{"id": "FR-1", "status": "passed", "evidence": "src/App/Program.cs prints the greeting"},
         {"id": "MISSED-1", "text": "Open the app once tests pass", "kind": "action", "status": "manual", "evidence": "..."}]
        ```
        "kind" (code, test or action) is only needed on MISSED entries.
        """;
}
