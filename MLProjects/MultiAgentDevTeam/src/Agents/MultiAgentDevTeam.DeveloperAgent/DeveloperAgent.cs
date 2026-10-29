using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.DeveloperAgent;

public class DeveloperAgent : BaseAgent
{
    public DeveloperAgent(AnthropicClient client, ILogger<DeveloperAgent> logger, IOptions<AgentConfiguration> options)
        : base(client, logger, options) { }

    public override string Name => "Software Developer";
    public override ArtifactType OutputType => ArtifactType.SourceCode;

    // Code correctness decides how many review loops a run pays for; re-runs reuse cached context
    protected override AgentModelSettings DefaultSettings => new()
    {
        Model = "claude-opus-5-5",
        Effort = "high",
        MaxTokens = 64000,
        CacheContext = true
    };

    protected override bool ReportsRequirementCoverage => true;

    protected override string SystemPrompt => """
        You are a senior software engineer who writes clean, production-quality C# .NET 10 code.
        Given requirements and architecture, produce complete, working source code:

        1. **Project Structure** - Show the full folder/file tree first
        2. **Source Files** - Each file clearly labeled with its path, complete implementation
        3. **Key Implementation Notes** - Explain critical design choices

        Code standards you MUST follow:
        - Use nullable reference types (enable)
        - Use async/await for all I/O operations
        - Follow SOLID principles
        - Use dependency injection via constructor
        - Add XML doc comments on all public members
        - Use record types for DTOs/value objects
        - Handle all exceptions explicitly — never swallow exceptions silently
        - Never hardcode secrets — always use configuration/environment variables
        - Validate all inputs at system boundaries
        - Give each project its own folder (e.g. src/App/, tests/App.Tests/) and never put one project's
          folder inside another's, or the outer project's default globbing compiles the inner one's files

        If given feedback/rejection notes, fix ONLY the reported issues. Do not refactor unrelated code.

        Output each file as:
        ### File: path/to/File.cs
        ```csharp
        // full file content
        ```
        Use paths relative to the project root, never absolute paths. If a file itself contains
        ``` fences (a README, for example), wrap it in a ```` fence instead.
        """;
}
