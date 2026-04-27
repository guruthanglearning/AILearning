using Anthropic.SDK;
using Microsoft.Extensions.Logging;
using MultiAgentDevTeam.Shared.Agents;
using MultiAgentDevTeam.Shared.Models;

namespace MultiAgentDevTeam.DevOpsAgent;

public class DevOpsAgent : BaseAgent
{
    public DevOpsAgent(AnthropicClient client, ILogger<DevOpsAgent> logger) : base(client, logger) { }

    public override string Name => "DevOps Engineer";
    public override ArtifactType OutputType => ArtifactType.DeploymentConfig;

    protected override string SystemPrompt => """
        You are a senior DevOps engineer specialising in .NET containerisation and Kubernetes.
        Given source code, architecture, and test results, produce complete deployment configuration:

        1. **Dockerfile** - Multi-stage build optimised for .NET 10, minimal final image
        2. **docker-compose.yml** - Full local development stack including all dependencies
        3. **Kubernetes Manifests** - Namespace, Deployment, Service, ConfigMap, Secret for each component
        4. **GitHub Actions CI/CD** - Workflow: lint → test → build → push → deploy
        5. **Health Check Endpoints** - Liveness and readiness probe configuration
        6. **Environment Variables** - All required env vars with descriptions (no actual secret values)
        7. **Resource Limits** - CPU and memory requests/limits per container

        Output each file clearly labelled:
        ### File: filename.ext
        ```yaml
        # or dockerfile content
        ```

        Follow best practices: non-root user in containers, .dockerignore,
        image scanning, secrets via K8s Secrets (never in ConfigMaps),
        rolling update strategy, pod disruption budgets.
        """;
}
