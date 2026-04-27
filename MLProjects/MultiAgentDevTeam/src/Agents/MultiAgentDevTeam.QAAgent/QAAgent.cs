using Anthropic.SDK;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.QAAgent;

public class QAAgent : BaseAgent
{
    public QAAgent(AnthropicClient client, ILogger<QAAgent> logger) : base(client, logger) { }

    public override string Name => "QA Engineer";
    public override ArtifactType OutputType => ArtifactType.TestResults;

    protected override string SystemPrompt => """
        You are a senior QA engineer who writes comprehensive xUnit test suites for C# .NET 10.
        Given source code and requirements, produce complete test code targeting 80%+ coverage:

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

        Output each test file as:
        ### File: tests/path/to/TestFile.cs
        ```csharp
        // full test file content
        ```

        End with a **Coverage Summary** table showing estimated coverage per class.
        """;
}
