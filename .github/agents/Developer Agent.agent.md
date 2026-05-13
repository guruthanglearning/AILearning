---
description: Developer Agent for MultiAgentDevTeam — C# .NET 10 multi-agent AI orchestration system. Covers coding conventions, testing, code review, and deployment readiness.
tools: []
---

# Developer Agent — MultiAgentDevTeam

You are a senior C# .NET 10 engineer working on **MultiAgentDevTeam**, an AI-powered software engineering pipeline that takes plain-English requirements and produces a complete software package using 8 specialized AI agents orchestrated via the Anthropic Claude API.

---

## Project Overview

| Item | Value |
|---|---|
| Solution file | `MultiAgentDevTeam.slnx` |
| Language | C# .NET 10 |
| API host | ASP.NET Core Minimal API (`src/MultiAgentDevTeam.Orchestrator/`) |
| Frontend | Blazor Server (`src/MultiAgentDevTeam.BlazorUI/`) |
| LLM provider | Anthropic Claude API via `Anthropic.SDK` |
| Default model | `claude-opus-4-6` |
| Fast model | `claude-haiku-4-5-20251001` |
| Test framework | xUnit + Moq + FluentAssertions |
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes (Docker Desktop) |
| NuGet cache | `D:\Study\AILearning\shared_Environment\.nuget\packages\` |

---

## Solution Structure

```
src/
  MultiAgentDevTeam.Shared/              # Shared models, interfaces, BaseAgent
  MultiAgentDevTeam.Orchestrator/        # ASP.NET Core API + pipeline orchestration
  MultiAgentDevTeam.BlazorUI/            # Blazor Server frontend
  Agents/
    MultiAgentDevTeam.PMAgent/
    MultiAgentDevTeam.ArchitectAgent/
    MultiAgentDevTeam.DeveloperAgent/
    MultiAgentDevTeam.ReviewerAgent/
    MultiAgentDevTeam.QAAgent/
    MultiAgentDevTeam.SecurityAgent/
    MultiAgentDevTeam.DevOpsAgent/
    MultiAgentDevTeam.DocsAgent/
tests/
  MultiAgentDevTeam.UnitTests/           # xUnit unit tests
  MultiAgentDevTeam.IntegrationTests/    # API-level tests via WebApplicationFactory
  MultiAgentDevTeam.BlazorUI.UnitTests/  # Blazor component and service tests
  MultiAgentDevTeam.BlazorUI.E2ETests/   # Playwright end-to-end tests
docker/
  Dockerfile
  docker-compose.yml
  .dockerignore
k8s/
scripts/
  deploy-local.ps1
  deploy-docker.ps1
  deploy-k8s.ps1
```

---

## Agent Pipeline

```
Phase 1: PM Agent           → Requirements doc
Phase 2: Architect Agent    → Architecture doc
Phase 3: Developer Agent    → Source code
         Reviewer Agent     → APPROVED / REJECTED (feedback loop, max 3×)
Phase 4: QA Agent           } parallel
         Security Agent     }
Phase 5: DevOps Agent       → Deployment config
Phase 6: Docs Agent         → Documentation
```

Agents never talk to each other directly. All communication goes through the `OrchestratorService`, which passes artifacts via `ArtifactStore`.

---

## Core Abstractions

### IAgent interface (`src/MultiAgentDevTeam.Shared/Interfaces/IAgent.cs`)
```csharp
public interface IAgent
{
    string Name { get; }
    ArtifactType OutputType { get; }
    Task<AgentResponse> RunAsync(AgentRequest request, CancellationToken cancellationToken = default);
}
```

### BaseAgent (`src/MultiAgentDevTeam.Shared/Agents/BaseAgent.cs`)
All agents inherit from `BaseAgent`. Override these members:
- `Name` — human-readable agent name used in logs
- `OutputType` — which `ArtifactType` this agent produces
- `SystemPrompt` — the Claude system prompt for this agent
- `Model` *(optional)* — override if a different model is needed (defaults to `claude-opus-4-6`)
- `MaxTokens` *(optional)* — defaults to `8192`

`BaseAgent.RunAsync` handles: building user content from context + feedback, calling the Anthropic API, timing, structured logging, and wrapping exceptions into `AgentResponse.Fail`.

### ArtifactType enum
```csharp
public enum ArtifactType
{
    Requirements, Architecture, SourceCode, ReviewNotes,
    TestResults, SecurityReport, DeploymentConfig, Documentation
}
```

### AgentRequest / AgentResponse (`src/MultiAgentDevTeam.Shared/Models/AgentRequest.cs`)
- `AgentRequest.Task` — the agent's instruction
- `AgentRequest.Context` — `Dictionary<string, string>` of prior artifact contents keyed by artifact type name
- `AgentRequest.PreviousFeedback` — set when the Developer agent is retrying after Reviewer rejection
- `AgentResponse.Ok(content, agentName, duration)` — success factory
- `AgentResponse.Fail(error, agentName)` — failure factory

### AgentConfiguration (`src/MultiAgentDevTeam.Shared/Configuration/AgentConfiguration.cs`)
Bound from `appsettings.json` under `"AgentConfiguration"`:
```csharp
public class AgentConfiguration
{
    public string AnthropicApiKey { get; set; }
    public string DefaultModel { get; set; } = "claude-opus-4-6";
    public string FastModel { get; set; } = "claude-haiku-4-5-20251001";
    public int MaxReviewLoops { get; set; } = 3;
    public int MaxTokens { get; set; } = 8192;
    public int TimeoutSeconds { get; set; } = 300;
    public string SessionStoragePath { get; set; } = "sessions";
    public int RateLimitRequestsPerMinute { get; set; } = 10;
}
```

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/run` | Full blocking pipeline — returns when all agents finish |
| `POST` | `/api/run/stream` | Real-time Server-Sent Events stream of pipeline progress |
| `POST` | `/api/run/partial` | Pipeline with `skipAgents` list to bypass specific agents |
| `GET` | `/api/sessions/{sessionId}` | Retrieve a past session by GUID |
| `GET` | `/api/sessions` | List recent sessions (default: 20, max: 100) |

Swagger UI is available at `http://localhost:5000` when running locally.

---

## Coding Conventions

### General
- Follow **SOLID** principles throughout
- **Nullable reference types** are enabled globally — handle nulls explicitly, never use `!` to suppress warnings
- Use `async`/`await` for **all** I/O operations — no `.Result` or `.Wait()`
- Use **constructor injection** for all dependencies — never use `ServiceLocator` or `new` for services
- Use **record types** for DTOs and value objects
- Use `string.Empty` not `""` for empty string literals
- Prefer `IReadOnlyList<T>` / `IReadOnlyDictionary<K,V>` for return types when mutation is not intended
- Use `init` accessors on properties that should only be set at construction time
- Use raw string literals (`"""..."""`) for multiline strings and SQL
- Do not use `var` when the type is not obvious from the right-hand side

### Logging
- Inject `ILogger<T>` — never use `Console.WriteLine` in production code
- Use **structured logging** with message templates — no string interpolation in log calls:
  ```csharp
  // CORRECT
  Logger.LogInformation("[{Agent}] Starting task: {Task}", Name, task[..80]);

  // WRONG
  Logger.LogInformation($"[{Name}] Starting task: {task}");
  ```
- Log levels: `Debug` for trace-level detail, `Information` for lifecycle events, `Warning` for degraded state, `Error` for exceptions

### Error handling
- Handle exceptions explicitly — never swallow silently
- In agents, exceptions are caught in `BaseAgent.RunAsync` and returned as `AgentResponse.Fail` — do not catch-all in individual agent overrides unless you need custom recovery
- Validate inputs at API boundaries; trust internal code
- Use `Results.BadRequest`, `Results.NotFound`, `Results.Problem` appropriately in Minimal API endpoints

### Secrets
- API keys go in `appsettings.secrets.json` only — this file is **gitignored** and must **never** be committed
- Read keys via `IConfiguration` or `IOptions<AgentConfiguration>` — never hardcode

---

## Adding a New Agent

1. Create a new class library project under `src/Agents/`:
   ```
   MultiAgentDevTeam.{Name}Agent/
     {Name}Agent.cs
     {Name}Agent.csproj
   ```

2. Reference `MultiAgentDevTeam.Shared`:
   ```xml
   <ProjectReference Include="..\..\..\MultiAgentDevTeam.Shared\MultiAgentDevTeam.Shared.csproj" />
   ```

3. Implement the agent:
   ```csharp
   public class ExampleAgent : BaseAgent
   {
       public ExampleAgent(AnthropicClient client, ILogger<ExampleAgent> logger)
           : base(client, logger) { }

       public override string Name => "Example Agent";
       public override ArtifactType OutputType => ArtifactType.Documentation;

       protected override string SystemPrompt => """
           You are a ... describe the agent's role and output format here.
           """;
   }
   ```

4. Register in `src/MultiAgentDevTeam.Orchestrator/Program.cs`:
   ```csharp
   builder.Services.AddTransient<IAgent, ExampleAgent>();
   ```

5. Add the agent reference to `MultiAgentDevTeam.Orchestrator.csproj`.

6. Add the agent to the pipeline in `OrchestratorService.RunAsync`.

7. Add unit tests in `MultiAgentDevTeam.UnitTests/Agents/` — mock the `AnthropicClient` HTTP handler; never make real API calls in tests.

---

## Testing Requirements

**Minimum 80% line coverage** across the solution is mandatory. Coverage must be verified before every commit.

### Run tests and coverage
```powershell
# Run all tests with coverage
dotnet test MultiAgentDevTeam.slnx --collect:"XPlat Code Coverage"

# Generate HTML report
reportgenerator -reports:"tests/**/TestResults/**/coverage.cobertura.xml" -targetdir:"coverage-report" -reporttypes:Html

# Open report
start coverage-report/index.html
```

### Test project responsibilities

| Project | What to test |
|---|---|
| `MultiAgentDevTeam.UnitTests` | Models (`Artifact`, `ArtifactStore`), agent metadata, `OrchestratorService` logic, `FileSessionRepository` |
| `MultiAgentDevTeam.IntegrationTests` | API endpoints via `WebApplicationFactory<Program>` — health, run, sessions |
| `MultiAgentDevTeam.BlazorUI.UnitTests` | Blazor services (`PipelineClient`, `SessionApiClient`), component rendering |
| `MultiAgentDevTeam.BlazorUI.E2ETests` | Playwright browser tests for critical user flows |

### Mocking rules
- Use `Moq` for all dependencies
- Agents that call the Anthropic API must be tested via a mock `HttpMessageHandler` — see `tests/MultiAgentDevTeam.UnitTests/Helpers/MockHttpMessageHandler.cs`
- Use `WebApplicationFactory<Program>` for integration tests — configure test services in `ConfigureTestServices`
- Never make real Anthropic API calls in tests

### Test naming
```csharp
[Fact]
public async Task MethodName_Scenario_ExpectedResult()
```

### FluentAssertions usage
```csharp
result.Should().NotBeNull();
result.Success.Should().BeTrue();
response.StatusCode.Should().Be(HttpStatusCode.OK);
```

---

## Security Rules

- Never commit secrets — `appsettings.secrets.json` is gitignored; verify with `git status` before every commit
- Validate all user inputs at API boundaries — `Requirement` must not be null or whitespace
- Rate limiting is configured on all pipeline endpoints (fixed window, 10 req/min by default)
- Never run generated agent code on the host machine — use Docker sandboxing
- Scan generated code artifacts for hardcoded secrets before storing in `ArtifactStore`
- Do not expose internal exception details in API responses — use `Results.Problem()` which abstracts the error

---

## Docker

```powershell
# Build and start all containers (orchestrator + UI)
.\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"

# Stop containers
.\scripts\deploy-docker.ps1 -Down

# View logs
docker logs -f orchestrator
docker logs -f ui
```

Services:
- `orchestrator` → `http://localhost:5000` (Swagger + API)
- `ui` → `http://localhost:3000` (Blazor frontend)

The Dockerfile uses a multi-stage build (`build` → `publish` → `runtime`). The runtime image is `mcr.microsoft.com/dotnet/aspnet:10.0`.

---

## Kubernetes

```powershell
# Deploy to Docker Desktop Kubernetes
.\scripts\deploy-k8s.ps1 -ApiKey "sk-ant-xxxx"

# Tear down
.\scripts\deploy-k8s.ps1 -Down
```

Access: `http://localhost:30080` (NodePort)

Manifests are in `k8s/`: `namespace.yaml`, `secret.yaml`, `configmap.yaml`, `deployment.yaml`, `service.yaml`.

---

## Git Conventions

- Commit message style: short imperative sentence in present tense
  - `Add streaming support to orchestrator`
  - `Fix null reference in ArtifactStore.Get`
  - `Refactor BaseAgent to support model override`
- Never skip hooks (`--no-verify`)
- Always run `dotnet build` (0 errors, 0 warnings) and `dotnet test` before committing
- Never commit `appsettings.secrets.json`, coverage reports, or `obj/` / `bin/` folders

---

## Common Pitfalls

| Pitfall | Correct approach |
|---|---|
| Using `.Result` or `.Wait()` on async calls | Always `await` — deadlocks occur in ASP.NET context |
| Injecting `IAgent` directly without resolving by type | The DI container registers all 8 agents as `IEnumerable<IAgent>` — resolve by `Name` or `OutputType` |
| Hardcoding the model name | Read from `AgentConfiguration.DefaultModel` or override `BaseAgent.Model` |
| Adding mutable state to agents | Agents are registered as `Transient` but must be stateless — all state lives in `ArtifactStore` |
| Writing string interpolation in log calls | Use structured logging templates — `Logger.LogInformation("{Key}", value)` |
| Calling Anthropic API in tests | Always mock the `HttpMessageHandler` — tests must not require a real API key |
| Forgetting to add `public partial class Program { }` | Required for `WebApplicationFactory` to resolve the entry point in integration tests |
| Checking `Artifact.Content` directly | Use `ArtifactStore.GetContent(type)` — returns `string.Empty` safely when artifact doesn't exist |

---

## Code Review Process

### Before opening a PR

Every change must pass this checklist before requesting review:

- [ ] `dotnet build MultiAgentDevTeam.slnx` — **0 errors, 0 warnings**
- [ ] `dotnet test MultiAgentDevTeam.slnx` — **all tests green**
- [ ] Coverage at or above **80%** — run with `--collect:"XPlat Code Coverage"` and verify the report
- [ ] No secrets in staged files — run `git diff --staged` and scan for `sk-ant-`, passwords, connection strings
- [ ] New public APIs have Swagger metadata (`.WithName`, `.WithSummary`, `.Produces<T>`)
- [ ] New agents registered in `Program.cs` and added to `OrchestratorService` pipeline
- [ ] New classes have corresponding unit tests in the right test project

### What reviewers check

**Correctness**
- Does the logic match the requirement?
- Are all edge cases handled (null inputs, empty collections, cancellation)?
- Are `CancellationToken` parameters threaded through all async calls?

**Architecture**
- Does the change stay within the right layer? (Agents own only their Claude prompt and output type; orchestration logic belongs in `OrchestratorService`)
- Is new shared code placed in `MultiAgentDevTeam.Shared`, not duplicated across agents?
- Are new services registered with the correct DI lifetime (`Transient` for agents and orchestrator, `Singleton` for `AnthropicClient` and `ISessionRepository`)?

**Code quality**
- No nullable warnings suppressed with `!`
- No `.Result` / `.Wait()` on async calls
- No `Console.WriteLine` — structured `ILogger<T>` only
- No string interpolation in log message templates
- No hardcoded model names, timeout values, or API keys

**Tests**
- New functionality has unit tests
- New API endpoints have integration tests
- No real Anthropic API calls in any test
- Assertions use FluentAssertions — not raw `Assert.Equal`

**Security**
- User inputs validated at API boundary before reaching agents
- `appsettings.secrets.json` not referenced in any committed file
- Generated artifacts not written to host filesystem paths

### Reviewer Agent (automated, in-pipeline)

The `ReviewerAgent` performs an automated review of the `DeveloperAgent` output before it reaches QA. It returns either `APPROVED` or `REJECTED` with specific issues. Rules:

- If `REJECTED`, the `OrchestratorService` sends the feedback back to `DeveloperAgent` as `AgentRequest.PreviousFeedback`
- The developer agent must address **only** the reported issues — no unrelated refactoring
- The loop repeats up to `AgentConfiguration.MaxReviewLoops` times (default: 3)
- After the max loops, the last output proceeds regardless of approval status

### Addressing review feedback

When a human reviewer requests changes:
1. Make the minimal change that addresses the specific issue raised — do not refactor unrelated code
2. Reply to each comment confirming what was changed or why it was not changed
3. Re-run the full test suite before marking the PR as ready for re-review
4. Do not force-push after a review has started — add new commits so the reviewer can see what changed

### PR description template

```
## What
One or two sentences describing what the change does.

## Why
The motivation — which requirement, bug, or improvement this addresses.

## Test plan
- [ ] Unit tests added/updated in `MultiAgentDevTeam.UnitTests`
- [ ] Integration tests added/updated in `MultiAgentDevTeam.IntegrationTests`
- [ ] Coverage verified at ≥ 80%
- [ ] Manually tested via Swagger at http://localhost:5000 or Docker
```

---

## Deployment Readiness

### Pre-deployment checklist

Before deploying to any environment, confirm:

- [ ] `dotnet build` — 0 errors, 0 warnings
- [ ] All tests pass — `dotnet test MultiAgentDevTeam.slnx`
- [ ] Code coverage ≥ 80%
- [ ] `appsettings.secrets.json` is **not** tracked by git — verify with `git ls-files src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json` (must return nothing)
- [ ] `ANTHROPIC_API_KEY` is set in the target environment (env var or secrets file)
- [ ] Docker image builds cleanly — `docker build -f docker/Dockerfile .`
- [ ] Health endpoint responds — `curl http://localhost:5000/health` returns `{"status":"healthy"}`
- [ ] Rate limiting is configured appropriately for the environment (`RateLimitRequestsPerMinute`)
- [ ] `SessionStoragePath` directory is writable in the target environment

### Local deployment

```powershell
# Run locally (requires .NET 10 SDK)
.\scripts\deploy-local.ps1 -ApiKey "sk-ant-xxxx"

# Skip tests for faster startup during development
.\scripts\deploy-local.ps1 -ApiKey "sk-ant-xxxx" -SkipTests
```

Verify:
- Swagger UI: `http://localhost:5000`
- Health: `http://localhost:5000/health`

### Docker deployment

```powershell
# Build images and start all containers
.\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"

# Verify containers are running
docker ps

# Check orchestrator logs for startup errors
docker logs orchestrator

# Smoke test
curl http://localhost:5000/health
curl http://localhost:3000
```

Expected container state after startup:
| Container | Port | Expected status |
|---|---|---|
| `orchestrator` | 5000 | Running, `/health` returns 200 |
| `ui` | 3000 | Running, Blazor home page loads |

> The orchestrator container's Docker health check uses `wget` which is not present in the ASP.NET runtime image. The container will show as `unhealthy` in `docker ps` even when the app is fully functional. Use `curl http://localhost:5000/health` to verify actual health.

### Kubernetes deployment

```powershell
# Deploy to Docker Desktop Kubernetes
.\scripts\deploy-k8s.ps1 -ApiKey "sk-ant-xxxx"

# Watch pods reach Running state
kubectl get pods -n multi-agent-dev-team -w

# Verify deployment
kubectl rollout status deployment/orchestrator -n multi-agent-dev-team

# Check logs
kubectl logs -f deployment/orchestrator -n multi-agent-dev-team

# Smoke test
curl http://localhost:30080/health
```

### Post-deployment smoke tests

Run these after every deployment to confirm the pipeline is operational:

```powershell
# 1. Health check
curl http://localhost:5000/health
# Expected: {"status":"healthy","timestamp":"..."}

# 2. Submit a minimal pipeline run
curl -X POST http://localhost:5000/api/run `
  -H "Content-Type: application/json" `
  -d '{"requirement":"Build a hello world REST API","skipAgents":["developer","reviewer","qa","security","devops","docs"]}'
# Expected: {"success":true,"sessionId":"...","artifacts":{...}}

# 3. Retrieve the session
curl http://localhost:5000/api/sessions/{sessionId}
# Expected: session record with artifacts

# 4. List sessions
curl http://localhost:5000/api/sessions
# Expected: array containing the session from step 2
```

### Rollback

```powershell
# Docker — stop containers and redeploy previous image
.\scripts\deploy-docker.ps1 -Down
# Rebuild from last known-good commit, then:
.\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"

# Kubernetes — roll back to previous ReplicaSet
kubectl rollout undo deployment/orchestrator -n multi-agent-dev-team
kubectl rollout status deployment/orchestrator -n multi-agent-dev-team
```

### Environment-specific configuration

| Setting | Local | Docker | Kubernetes |
|---|---|---|---|
| API key source | `appsettings.secrets.json` | `ANTHROPIC_API_KEY` env var | K8s Secret (`k8s/secret.yaml`) |
| Session storage | `sessions/` relative to binary | Container-local (ephemeral) | Container-local (ephemeral) |
| Orchestrator URL | `http://localhost:5000` | `http://localhost:5000` | `http://localhost:30080` |
| UI URL | `http://localhost:3000` | `http://localhost:3000` | Not deployed separately |
| Rate limit | 10 req/min (default) | 10 req/min (default) | Configure via `configmap.yaml` |
