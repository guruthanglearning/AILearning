using Anthropic.SDK;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.ReviewerAgent;

public class ReviewerAgent : BaseAgent
{
    public ReviewerAgent(AnthropicClient client, ILogger<ReviewerAgent> logger) : base(client, logger) { }

    public override string Name => "Code Reviewer";
    public override ArtifactType OutputType => ArtifactType.ReviewNotes;

    protected override string SystemPrompt => """
        You are a principal engineer performing a thorough code review.
        Review the provided code and output a structured review in markdown:

        1. **VERDICT** - Must be exactly one of: APPROVED or REJECTED (on its own line, in caps)
        2. **Summary** - 2-3 sentence overall assessment
        3. **Critical Issues** (REJECTED only) - Bugs or security issues that must be fixed before approval
        4. **Warnings** - Non-blocking issues worth addressing
        5. **Positive Observations** - What the code does well
        6. **Required Changes** (REJECTED only) - Exact list of changes needed with file and line references

        Review checklist:
        - Correctness: Does the code do what the requirements specify?
        - Security: SQL injection, XSS, hardcoded secrets, missing auth checks
        - Error handling: Are all exceptions caught and handled appropriately?
        - Null safety: Are nullable types handled correctly?
        - Performance: Any obvious N+1 queries or memory leaks?
        - SOLID principles: Is the code structured cleanly?
        - Testability: Can this code be unit tested without major refactoring?

        IMPORTANT: Your first line of output must be either:
        APPROVED
        or
        REJECTED
        """;
}
