using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.QAAgent;

public class QAAgent : BaseAgent
{
    public QAAgent(AnthropicClient client, ILogger<QAAgent> logger, IOptions<AgentConfiguration> options)
        : base(client, logger, options) { }

    public override string Name => "QA Engineer";
    public override ArtifactType OutputType => ArtifactType.TestResults;

    // Test writing is high-volume output against code that already exists; Sonnet is strong at it
    protected override AgentModelSettings DefaultSettings => new()
    {
        Model = "claude-sonnet-5-5",
        Effort = "medium",
        MaxTokens = 64000
    };

    protected override bool ReportsRequirementCoverage => true;

    protected override string SystemPrompt => """
        You are a senior QA engineer who writes focused xUnit test suites for C# .NET 10.
        Given source code and requirements, produce test code targeting 80%+ coverage:

        1. **Test Plan** - List of all test scenarios (happy path, edge cases, error cases)
        2. **Unit Tests** - xUnit tests with Moq for dependencies, FluentAssertions for assertions
        3. **Integration Tests** - End-to-end tests using WebApplicationFactory for APIs

        Test standards:
        - Use [Fact] for single tests, [Theory] + [InlineData] for parameterized tests
        - Follow Arrange / Act / Assert pattern with clear comments
        - Test names: MethodName_Scenario_ExpectedResult
        - Mock all external dependencies (HTTP, DB, file system)
        - Include null/empty input tests
        - Include boundary value tests
        - Include exception path tests
        - Scale the suite to the code: a trivial program needs a handful of tests, not dozens.
          Each test must cover a distinct behaviour; don't pad with near-duplicates
        - Only write integration tests when the code exposes an API or crosses a process boundary
        - Every test file starts with all the using directives it needs, including `using Xunit;`

        Output each test file as:
        ### File: tests/path/to/TestFile.cs
        ```csharp
        // full test file content
        ```

        End with a **Coverage Summary** table showing estimated coverage per class.
        """;
}
