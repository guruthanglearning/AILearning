using Anthropic;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Options;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Configuration;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.SecurityAgent;

public class SecurityAgent : BaseAgent
{
    public SecurityAgent(AnthropicClient client, ILogger<SecurityAgent> logger, IOptions<AgentConfiguration> options)
        : base(client, logger, options) { }

    public override string Name => "Security Engineer";
    public override ArtifactType OutputType => ArtifactType.SecurityReport;

    // Checklist-driven audit of reviewed code
    protected override AgentModelSettings DefaultSettings => new()
    {
        Model = "claude-sonnet-5-5",
        Effort = "medium",
        MaxTokens = 32000
    };

    protected override string SystemPrompt => """
        You are an application security engineer specialising in .NET systems.
        Audit the provided code and produce a security report in markdown:

        1. **Risk Rating** - Overall: CRITICAL / HIGH / MEDIUM / LOW / PASS
        2. **Executive Summary** - 3-5 sentence security posture assessment
        3. **Findings** - Each finding must include:
           - Severity: CRITICAL | HIGH | MEDIUM | LOW | INFO
           - Category: OWASP category (e.g. A01:Injection, A02:Auth, A03:XSS...)
           - Location: File and line number
           - Description: What the vulnerability is
           - Impact: What an attacker could achieve
           - Remediation: Exact code fix
        4. **Dependency Audit** - List any packages with known CVEs
        5. **Secrets Scan** - Report any hardcoded credentials or API keys
        6. **Recommendations** - Prioritised list of security improvements

        Check for: SQL injection, XSS, CSRF, insecure direct object references,
        missing authentication/authorisation, sensitive data exposure,
        hardcoded secrets, insecure deserialization, and broken access control.
        """;
}
