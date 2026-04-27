# CLAUDE.md — MultiAgentDevTeam Project Instructions

## Permission Grant

Claude Code is granted **full autonomous permission** to work on this project — **no prompts required** for any action within the project folder (`D:\Study\AILearning\MLProjects\MultiAgentDevTeam\`).

### Allowed without asking (within project folder)

- Read, create, edit, and delete any file inside the project directory
- Run all `dotnet` commands: `build`, `test`, `run`, `tool`, `add`, `restore`, `publish`
- Run `reportgenerator` and open coverage reports (`start coverage-report*`)
- Run `git status`, `git diff`, `git log`, `git add`, `git commit`, `git branch`, `git checkout`, `git stash`
- Run PowerShell (`powershell` / `pwsh`) scripts including those in `/scripts`
- Run `mkdir`, `cp`, `mv`, `ls`, `cat`, `sleep` shell commands within the project
- Run Docker and Kubernetes commands for local deployment
- Run `npm`, `node` commands for frontend tooling
- Fix build warnings, errors, and failing tests without asking
- Refactor, implement, and improve code as directed
- Write to `C:\Users\gurut\.claude\` (memory and settings files)

### Always ask before (regardless of location)

- `git push` to any remote
- `git reset --hard` or any force-destructive git operation
- `rm -rf` or permanent file deletion
- Any action that **writes, modifies, or deletes files outside** `D:\Study\AILearning\MLProjects\MultiAgentDevTeam\` (except `C:\Users\gurut\.claude\`)
- Sending messages, posting to external services, or modifying shared infrastructure
- Any action affecting other users or shared systems

---

## Project Overview

**MultiAgentDevTeam** is a C# .NET 10 multi-agent AI system that takes plain-English software requirements and produces a complete software package using 8 specialized AI agents powered by the Anthropic Claude API.

**Solution file:** `MultiAgentDevTeam.slnx`

### Agent Pipeline

```
Phase 1: PM Agent           → Requirements doc
Phase 2: Architect Agent    → Architecture doc
Phase 3: Developer Agent    → Source code
         Reviewer Agent     → APPROVED / REJECTED (feedback loop, max 3x)
Phase 4: QA Agent           → Test suite         } parallel
         Security Agent     → Security report    }
Phase 5: DevOps Agent       → Deployment config
Phase 6: Docs Agent         → Documentation
```

### Key Directories

```
src/
  MultiAgentDevTeam.Orchestrator/   - ASP.NET Core API host + pipeline orchestration
  MultiAgentDevTeam.Shared/         - Shared models, interfaces, base agent, config
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
  MultiAgentDevTeam.UnitTests/
  MultiAgentDevTeam.IntegrationTests/
docker/
k8s/
scripts/
```

---

## Technology Stack

- **Language/Framework:** C# .NET 10 (ASP.NET Core minimal APIs)
- **LLM Provider:** Anthropic Claude API via `Anthropic.SDK`
- **Default Model:** `claude-opus-4-6`
- **Fast Model:** `claude-haiku-4-5-20251001`
- **Test Framework:** xUnit + Moq + FluentAssertions
- **Containerization:** Docker + Docker Compose
- **Orchestration:** Kubernetes (Docker Desktop)
- **NuGet Cache:** `D:\Study\AILearning\shared_Environment\.nuget\packages\`

---

## API Key Configuration

The Anthropic API key is stored in:
```
src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json
```
This file is **gitignored** and must never be committed.

Structure:
```json
{
  "AgentConfiguration": {
    "AnthropicApiKey": "sk-ant-..."
  }
}
```

Alternatively, set as environment variable:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-..."
```

---

## Coding Conventions

- Follow SOLID principles throughout
- C# nullable reference types enabled — handle nulls explicitly
- Use `async/await` for all I/O operations
- Logging via `ILogger<T>` — use structured logging (no string interpolation in log calls)
- All agents inherit from `BaseAgent` in `MultiAgentDevTeam.Shared`
- New agents must implement `IAgent` interface
- Keep system prompts detailed and role-specific

---

## Windows Smart App Control (SAC) — Pre-Flight Check

**Smart App Control (SAC)** is a Windows 11 security feature that blocks newly compiled DLLs that are not signed by Microsoft. It breaks `dotnet test` and `dotnet run` on any new project or after a clean build.

### How Claude must handle this

**Before every `dotnet build`, `dotnet test`, or `dotnet run`:**

1. **Check if SAC is active:**
```powershell
powershell -Command "(Get-ItemProperty 'HKLM:\SYSTEM\CurrentControlSet\Control\CI\Policy').VerifiedAndReputablePolicyState"
```
- Returns `1` → SAC is **ON** (enforcement mode) — run the unblock step below
- Returns `0` or `2` → SAC is **OFF** or evaluation mode — proceed normally

2. **If SAC is ON — unblock after every build:**
```powershell
pwsh scripts/unblock-dlls.ps1
```
Or inline:
```powershell
powershell -Command "Get-ChildItem 'D:\Study\AILearning\MLProjects\MultiAgentDevTeam' -Recurse -File -Include '*.dll','*.exe' | Unblock-File"
```

3. **Then run the build/test command as normal.**

### Recommended permanent fix (one-time, requires restart)

SAC is not designed for developer machines. Turn it off permanently:

```
Windows Security → App & browser control → Smart App Control settings → Off → Restart PC
```

After restart, run the unblock script once to clear any residual blocks:
```powershell
pwsh scripts/unblock-dlls.ps1
```

### Claude's automated workflow rule

> **MANDATORY:** If any `dotnet` command fails with `Application Control policy has blocked this file` or error code `0x800711C7`, Claude must immediately run `pwsh scripts/unblock-dlls.ps1` and retry the command — no need to ask the user.

---

## Build & Test Commands

```bash
# Build entire solution
dotnet build MultiAgentDevTeam.slnx

# Run all tests
dotnet test MultiAgentDevTeam.slnx

# Run only unit tests
dotnet test tests/MultiAgentDevTeam.UnitTests/

# Run only integration tests
dotnet test tests/MultiAgentDevTeam.IntegrationTests/

# Run the API locally
dotnet run --project src/MultiAgentDevTeam.Orchestrator/
```

---

## Test Results & Coverage Report

**No permission required** for any of the commands in this section — run them directly.

### Run tests + collect coverage + open report in browser (all-in-one)

```bash
dotnet test MultiAgentDevTeam.slnx --collect:"XPlat Code Coverage" && \
reportgenerator -reports:"tests/**/TestResults/**/coverage.cobertura.xml" -targetdir:"coverage-report" -reporttypes:Html && \
start coverage-report/index.html
```

### Step-by-step breakdown

```bash
# 1. Run unit tests with coverage
dotnet test tests/MultiAgentDevTeam.UnitTests/ --collect:"XPlat Code Coverage"

# 2. Run integration tests with coverage
dotnet test tests/MultiAgentDevTeam.IntegrationTests/ --collect:"XPlat Code Coverage"

# 3. Run all tests with coverage (combined)
dotnet test MultiAgentDevTeam.slnx --collect:"XPlat Code Coverage"

# 4. Generate HTML report from all coverage files
reportgenerator -reports:"tests/**/TestResults/**/coverage.cobertura.xml" -targetdir:"coverage-report" -reporttypes:Html

# 5. Open report in default browser (Windows)
start coverage-report/index.html
```

### Prerequisites

ReportGenerator must be installed (one-time):
```bash
dotnet tool install -g dotnet-reportgenerator-globaltool
```

### Coverage output location

```
coverage-report/index.html   ← open this in browser for visual report
tests/
  MultiAgentDevTeam.UnitTests/TestResults/**/coverage.cobertura.xml
  MultiAgentDevTeam.IntegrationTests/TestResults/**/coverage.cobertura.xml
```

---

## Workflow Rules for Claude

1. **Always build before committing** — run `dotnet build` and confirm 0 errors
2. **Run tests after any logic change** — confirm all tests pass before marking done
3. **Fix warnings too** — treat NU1510 and similar warnings as tasks to clean up
4. **Minimal changes** — only change what is needed for the task; no scope creep
5. **No secrets in code** — API keys go in `appsettings.secrets.json` only
6. **Commit message style:** short imperative sentence, e.g. `Add streaming support to orchestrator`
7. **Never skip test hooks or commit with --no-verify**
8. **Keep CLAUDE.md updated** if project structure changes significantly

## Code Coverage Rule — MANDATORY

**Every code change or addition MUST maintain a minimum of 80% line coverage across the solution.**

- Run coverage after every change: `dotnet test MultiAgentDevTeam.slnx --collect:"XPlat Code Coverage"`
- If coverage drops below 80%, write the missing tests before considering the task done
- New classes must have unit tests added in the same task — never defer test writing
- New API endpoints must have integration tests added in `MultiAgentDevTeam.IntegrationTests`
- New services/repositories must have unit tests added in `MultiAgentDevTeam.UnitTests`
- Logic in `BaseAgent`, `ArtifactStore`, and shared models must be tested without real API calls
- Use `Moq` for dependencies, `WebApplicationFactory` for API-level integration tests
- Agents that call Claude API must be tested via mocks — never make real API calls in tests

---

## Known Issues / Next Steps

- [ ] Fix redundant NuGet package warnings (NU1510) in Orchestrator and Shared projects
- [ ] Add persistent artifact storage (replace in-memory ArtifactStore with database)
- [ ] Add streaming/progress responses for long-running pipeline
- [ ] Add rate limiting middleware
- [ ] Support custom model selection per agent
- [ ] Support multi-language code generation (currently C# .NET 10 only)
