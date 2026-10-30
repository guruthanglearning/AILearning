# Multi-Agent Dev Team

An AI-powered software engineering team built in **C# .NET 10**, orchestrated via the **Anthropic Claude API**. Submit a plain-English requirement and receive a complete software package — requirements, architecture, source code, tests, security report, deployment config, and documentation — all produced by a team of specialised AI agents.

---

## Table of Contents

- [Purpose](#purpose)
- [Architecture](#architecture)
- [Agent Roles](#agent-roles)
- [Requirement Tracking](#requirement-tracking)
- [Project Output](#project-output)
- [Orchestration Patterns](#orchestration-patterns)
- [Prerequisites](#prerequisites)
- [Configuration](#configuration)
- [How to Run](#how-to-run)
  - [Local (dotnet run)](#option-1--local-dotnet-run)
  - [Docker](#option-2--docker)
  - [Kubernetes](#option-3--kubernetes-docker-desktop)
- [Debugging](#debugging)
  - [Visual Studio 2022](#visual-studio-2022)
  - [VS Code](#vs-code)
- [API Reference](#api-reference)
- [Running Tests](#running-tests)
- [Project Structure](#project-structure)
- [Limitations & Guardrails](#limitations--guardrails)

---

## Purpose

This project demonstrates a **multi-agent system** where each AI agent owns one phase of the Software Development Lifecycle (SDLC). A central **Orchestrator** coordinates the agents, passes artifacts between them, and enforces quality gates (review feedback loops, test pass gates).

The Anthropic Claude API natively supports multi-agent orchestration via the tool-use pattern. A central Orchestrator delegates tasks to specialised subagents, each scoped to one engineering discipline. Claude's large context window allows agents to share rich context without losing track across phases.

**Use cases:**
- Rapidly prototype a working codebase from a plain English description
- Learn how multi-agent orchestration patterns work in practice
- Explore how feedback loops and parallel agent execution are implemented

---

## Architecture

```
USER (HTTP POST /api/run)
         │
         ▼
┌────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATOR API                          │
│                   (ASP.NET Core Minimal API)                   │
│                                                                │
│  Phase 1: PM Agent ──────────────────► requirements.md         │
│                │                                               │
│  Phase 2: Architect Agent ───────────► architecture.md         │
│                │                                               │
│  Phase 3: ┌───────────────────────────────────────┐            │
│           │      FEEDBACK LOOP (max 3 rounds)     │            │
│           │  Developer Agent ──► source code      │            │
│           │        ▲                  │           │            │
│           │        │            Reviewer Agent    │            │
│           │   REJECTED                │           │            │
│           │        └──── NO ──── APPROVED?        │            │
│           └─────────────────── YES ──┘            │            │
│                │                                               │
│  Phase 4: ┌───────────┬─────────────┐  (parallel)              │
│           QA Agent  Security Agent                             │
│           └───────────┴─────────────┘                          │
│                │                                               │
│  Phase 5: DevOps Agent ──────────────► Dockerfile + CI/CD      │
│                │                                               │
│  Phase 6: Docs Agent ────────────────► README + API docs       │
│                │                                               │
│  Phase 7: Verifier Agent ────────────► per-requirement verdict │
│                │                                               │
│           RESPONSE → artifacts + requirement checklist         │
└────────────────────────────────────────────────────────────────┘
```

### Communication Model

```
Agents NEVER talk to each other directly.

Agent A ──X──► Agent B            ← Does NOT happen

Agent A ──► Orchestrator ──► Agent B   ← How it works

Shared Artifact Store (in-memory per request session):
  requirements   ← written by PM Agent
  architecture   ← written by Architect Agent
  source_code    ← written by Developer Agent
  review_notes   ← written by Reviewer Agent
  test_results   ← written by QA Agent
  security_report← written by Security Agent
  deployment     ← written by DevOps Agent
  documentation  ← written by Docs Agent
  verification   ← written by Verifier Agent
```

---

## Agent Roles

| Agent | Phase | Output | Key Behaviour |
|---|---|---|---|
| **Product Manager** | 1 | Requirements doc | Extracts user stories, acceptance criteria, NFRs |
| **Architect** | 2 | Architecture ADR | Tech stack, API schema, DB schema, component diagram |
| **Developer** | 3 | Source code | Writes complete C# .NET 10 implementation |
| **Reviewer** | 3 (loop) | Review notes | Approves or rejects with specific issues; triggers retry |
| **QA Engineer** | 4 (parallel) | Test suite | xUnit unit + integration tests targeting 80%+ coverage |
| **Security Engineer** | 4 (parallel) | Security report | OWASP Top 10 audit, CVE scan, secrets detection |
| **DevOps Engineer** | 5 | Deployment config | Dockerfile, docker-compose, K8s manifests, GitHub Actions |
| **Technical Writer** | 6 | Documentation | README, API reference, architecture doc |
| **Acceptance Verifier** | 7 | Verification report | Checks every requirement against the original request and the artifacts |

---

## Requirement Tracking

Every run checks that each instruction in the request was actually carried out, instead of trusting a single approve/reject verdict.

1. **Checklist.** The PM ends the requirements with a `requirements-checklist` JSON block: one entry per requirement with an id (`FR-1`, `NFR-1`), text, acceptance criterion and kind:
   - `code`: built into the source or config files
   - `test`: needs a test
   - `action`: done outside the generated files, such as writing to a folder, running the app or deploying
   If the request names no platform, the PM adds the team default (C# on .NET 10) as a requirement.
2. **Coverage claims.** Developer, QA, DevOps and Docs end their output with a `## Requirement Coverage` section that maps each id to the file or test that satisfies it, or `N/A` with a reason.
3. **Coverage gate.** If the Developer leaves a `code` requirement unclaimed, the orchestrator sends it straight back with the missing items, before paying for a review. This uses the same retry budget as review rejections.
4. **Verifier.** The Acceptance Verifier (Sonnet) reads the original request word for word, the checklist, the claims and the artifacts. It marks each requirement `passed`, `failed` or `manual`, and adds a `MISSED-n` entry for any instruction the checklist dropped.
5. **Result.** The run log ends with one line per requirement, and the response and saved session carry `requirements` plus `requirementsMet`. Both UIs show the results as a table.

| Status | Meaning |
|---|---|
| ✅ Passed | Claimed by an agent and confirmed by the Verifier |
| ❌ Failed | No agent claimed it, or the Verifier found it missing or wrong |
| 🖐️ Manual | An `action`: generated files can't prove it happened, so you perform and confirm it. Creating the project in the requested folder is the exception: it passes once the files are written (see [Project Output](#project-output)) |
| ❔ Unverified | Claimed, but the Verifier was skipped |

A run with failed requirements still returns `success: true`, because the artifacts were produced; check `requirementsMet` (`false` if any requirement failed, `null` if none were tracked).

---

## Project Output

After the Docs phase the orchestrator writes the generated project to disk, so you get a codebase you can open, build and run, not just text.

- **Where:** the first Windows folder path in the request, such as `D:\Temp\MyApp` (quote it if it contains spaces). If the request names none, a new folder under `ProjectOutput:DefaultRoot` (`C:\Temp` by default), named after the request plus the session id, such as `C:\Temp\todo-rest-api-authentication-1a2b3c4d`.
- **What:** every `### File: path` block from the Developer, QA and DevOps output, at its relative path (a later agent wins if two write the same file), plus `docs/` with the requirements, architecture, documentation, review notes and security report.
- **Never overwrites:** if the folder already has files, the project goes into a new subfolder inside it, and every file is created new, so an existing one is never replaced. File paths that are absolute or use `..` are skipped, and a requested folder that uses `..` is refused.
- **Result:** the run log shows `📁 Wrote N files to <folder>`, and a requirement to create the project in the requested folder passes with that as evidence. Building and running the project stay manual steps.

| Setting | Default | Purpose |
|---|---|---|
| `ProjectOutput:Enabled` | `true` | Turn writing off entirely |
| `ProjectOutput:DefaultRoot` | `C:\Temp` | Parent folder when the request names no location |
| `ProjectOutput:HostDrivesPath` | empty | Set in containers to where the host's drives are mounted |

Docker and Kubernetes reach your Windows drives through Docker Desktop's `/run/desktop/mnt/host`, mounted at `/host` (`HostDrivesPath=/host`), so `D:\Temp\MyApp` is written to `/host/d/Temp/MyApp`. This needs Docker Desktop on Windows.

---

## Orchestration Patterns

### Pattern 1 — Sequential Pipeline
Each agent completes before the next starts. Output of agent N becomes the input of agent N+1.

```
PM → Architect → Developer → Reviewer → QA → DevOps → Security → Docs
```

Best for: greenfield projects with well-defined requirements.

---

### Pattern 2 — Parallel Execution
Agents that don't depend on each other run concurrently (QA and Security in Phase 4).

```
Developer ──► Reviewer ──► [APPROVED]
                                │
                    ┌───────────┴───────────┐
                 QA Agent           Security Agent   ← run in parallel
                    └───────────┬───────────┘
                       DevOps → Docs → Verifier
```

Best for: large tasks where time efficiency matters.

---

### Pattern 3 — Feedback Loop
The Reviewer can reject code and send it back to the Developer, up to `MaxReviewLoops` times.

```
Developer ──► Reviewer ──► [APPROVED] ──► QA
                  │
             [REJECTED]
                  │
            Developer (revision)
```

Best for: production-grade output with strict quality gates. This is the default behaviour in this project.

---

## Prerequisites

| Tool | Version | Purpose |
|---|---|---|
| .NET SDK | 10.0+ | Build and run |
| Docker Desktop | Latest | Docker + Kubernetes |
| kubectl | Any | Kubernetes CLI |
| Anthropic API Key | — | Claude API access |

Enable Kubernetes in Docker Desktop:
```
Docker Desktop → Settings → Kubernetes → Enable Kubernetes → Apply & Restart
```

---

## Configuration

All configuration is via environment variables or `appsettings.json`.

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | **Yes** | Your Anthropic API key |
| `AgentConfiguration__MaxReviewLoops` | No | Max Developer→Reviewer cycles (default: `3`) |
| `AgentConfiguration__TimeoutSeconds` | No | Timeout for each Anthropic API call, in seconds (default: `1800`; responses are streamed and can be long) |
| `AgentConfiguration__MaxRetries` | No | SDK retries on 429 / 5xx, honouring `retry-after` (default: `4`) |
| `AgentConfiguration__Agents__{Agent}__Model` | No | Override one agent's model, e.g. `AgentConfiguration__Agents__Docs__Model=claude-sonnet-5-5` |
| `AgentConfiguration__Agents__{Agent}__Effort` | No | Override one agent's effort: `low`, `medium`, `high`, `xhigh` or `max` |
| `AgentConfiguration__Agents__{Agent}__MaxTokens` | No | Override one agent's output budget (thinking included) |
| `AgentConfiguration__Agents__{Agent}__CacheContext` | No | Mark the agent's context for prompt caching (`true`/`false`) |

`{Agent}` is one of `PM`, `Architect`, `Developer`, `Reviewer`, `QA`, `Security`, `DevOps`, `Docs`, `Verifier`.

### Models per agent

Each agent runs on the cheapest model that does its job well. Opus is kept for the steps whose mistakes cost a whole review loop.

| Agent | Model | Effort | Max tokens | Why |
|---|---|---|---|---|
| PM | `claude-sonnet-5-5` | medium | 16,000 | Requirements extraction is structured analysis |
| Architect | `claude-opus-5-5` | high | 32,000 | Design decisions shape every later agent |
| Developer | `claude-opus-5-5` | high | 64,000 | Code quality decides how many review loops a run pays for; context is prompt-cached across loops |
| Reviewer | `claude-opus-5-5` | high | 32,000 | The quality gate: a missed bug or a false rejection both cost a loop |
| QA | `claude-sonnet-5-5` | medium | 64,000 | High-volume test writing against existing code |
| Security | `claude-sonnet-5-5` | medium | 32,000 | Checklist-driven audit of reviewed code |
| DevOps | `claude-sonnet-5-5` | low | 32,000 | Dockerfiles and CI workflows are well-trodden templates |
| Docs | `claude-haiku-5-5` | medium | 32,000 | Summarising finished artifacts needs little reasoning |
| Verifier | `claude-sonnet-5-5` | medium | 16,000 | Careful reading against a checklist, not design work; a separate agent so nobody grades their own work |

### Cost controls

- **Usage and cost per run:** every agent call logs its input, output and cache tokens with an estimated cost; the run log ends with `💰 Estimated API cost: ...`, and the totals are saved with the session (`usage`, `estimatedCostUsd`). Prices live in `ModelPricing` and are list prices, so treat the figure as an estimate.
- **Output sized to the request:** every agent is told to scale its output to the request, so a small app gets a few tests and one README instead of an enterprise-sized package.
- **Prompt caching:** the Developer's context (requirements + architecture) is cached, so review-loop re-runs read it at a fraction of the input price. Other agents run once per pipeline, where a cache write (1.25× input) would cost more than it saves.
- **Smaller context:** DevOps receives the list of test files rather than their full source.
- **Refusals:** requests use server-side fallback, so a request one model declines for policy reasons can be completed by a fallback model. If no model completes it, the API returns `422` with title "Model declined the request".

---

## How to Run

### API key setup

The Anthropic API key is never committed. Each person uses their own key, and runs are billed to their own Anthropic account. The deploy scripts find it automatically, in this order:

| # | Source | Typical use |
|---|---|---|
| 1 | `-ApiKey` parameter | One-off override (the script warns that it ends up in your shell history) |
| 2 | `$env:ANTHROPIC_API_KEY` | CI pipelines, or a key set for the current shell |
| 3 | `src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json` | Your local key, set up once (gitignored) |
| 4 | A masked prompt | Interactive terminals when nothing above is set; offers to save the key to the file in step 3 |

The key is never printed: the script only reports where it came from, e.g. `API key: from appsettings.secrets.json (sk-ant-... (108 chars))`.

**First time after cloning**, pick one:
```powershell
# Option A: a local secrets file (recommended; the scripts then find it every time)
Copy-Item src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.example.json `
          src/MultiAgentDevTeam.Orchestrator/appsettings.secrets.json
# ...then replace REPLACE_WITH_YOUR_ANTHROPIC_API_KEY in the copy with your key

# Option B: just run a deploy script and paste the key when prompted
.\scripts\deploy-docker.ps1
```

**GitHub Actions / CI:** store the key as a repository secret and expose it as `ANTHROPIC_API_KEY` in the job's `env`. The scripts never prompt in a non-interactive run; they fail with a message listing the options above.

**Kubernetes:** `deploy-k8s.ps1` creates the `agent-secrets` Secret from your key (piped to `kubectl` on stdin, so the key never appears on a command line) and restarts the pods so a changed key takes effect. If no key is found but the Secret already exists in the cluster, it is reused.

**React UI packages:** `node_modules` isn't committed. `deploy-local.ps1` runs `npm ci` on first use, and the UI Docker image installs its own packages.

### Option 1 — Local (dotnet run)

```powershell
# From the project root
.\scripts\deploy-local.ps1

# Skip tests for faster startup
.\scripts\deploy-local.ps1 -SkipTests
```

Access:
- Swagger UI: http://localhost:5000
- Health: http://localhost:5000/health

---

### Option 2 — Docker

```powershell
# Build images and start containers
.\scripts\deploy-docker.ps1

# Stop and remove containers
.\scripts\deploy-docker.ps1 -Down
```

Or using docker compose directly: copy `docker/.env.example` to `docker/.env` (gitignored), add your key, then:
```powershell
docker compose -f docker/docker-compose.yml up -d
```

Access:
- UI: http://localhost:3000
- Swagger UI: http://localhost:5000
- Logs: `docker logs -f orchestrator`

Saved sessions live in the `docker_sessions` volume, so they survive rebuilds and `-Down`. To delete them: `docker volume rm docker_sessions`.

---

### Option 3 — Kubernetes (Docker Desktop)

```powershell
# Full deploy (builds image + deploys to K8s)
.\scripts\deploy-k8s.ps1

# Skip image rebuild (use existing image)
.\scripts\deploy-k8s.ps1 -SkipBuild

# Tear everything down
.\scripts\deploy-k8s.ps1 -Down
```

Saved sessions live in the `sessions` PersistentVolumeClaim (`k8s/pvc.yaml`), so they survive pod restarts and redeploys. `-Down` deletes the namespace and the sessions with it.

Access:
- Swagger UI: http://localhost:30080
- Health: http://localhost:30080/health

Useful kubectl commands:
```bash
# Watch pods start up
kubectl get pods -n multi-agent-dev-team -w

# View logs
kubectl logs -f deployment/orchestrator -n multi-agent-dev-team

# Scale replicas
kubectl scale deployment/orchestrator --replicas=2 -n multi-agent-dev-team
```

---

## Debugging

The application must be running (via Docker or locally) before attaching a debugger.

> **Note on symbols:** The production `Dockerfile` builds in **Release** mode, which strips debug symbols (PDB files). You will be able to attach and pause execution, but breakpoints on your source lines will not bind. For full source-level debugging, see the [Debug build note](#debug-build-note) below.

---

### Visual Studio 2022

1. Start the application in Docker:
   ```powershell
   .\scripts\deploy-docker.ps1
   ```

2. In Visual Studio, open the solution (`MultiAgentDevTeam.slnx`).

3. Go to **Debug → Attach to Process** (or press `Ctrl+Alt+P`).

4. In the **Connection type** dropdown, select **Docker (Linux Container)**.

5. Click **Find** and select the `orchestrator` container.

6. In the process list, select the `dotnet` process.

7. Ensure **Code type** is set to **Managed (.NET Core)** and click **Attach**.

Visual Studio automatically installs `vsdbg` (the .NET debugger) into the container on the first attach — no manual setup required.

---

### VS Code

**Prerequisites:** Install these extensions:
- [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)
- [C# Dev Kit](https://marketplace.visualstudio.com/items?itemName=ms-dotnettools.csdevkit)

**Steps:**

1. Start the application in Docker:
   ```powershell
   .\scripts\deploy-docker.ps1
   ```

2. Open the **Docker** panel in the VS Code sidebar (whale icon).

3. Expand **Containers** and find the `orchestrator` container.

4. Right-click the container → **Attach Visual Studio Code**.
   A new VS Code window opens connected to the container's file system.

5. In that remote window, open the **Run and Debug** panel (`Ctrl+Shift+D`).

6. Add the following configuration to `.vscode/launch.json` in the project root:

   ```json
   {
     "version": "0.2.0",
     "configurations": [
       {
         "name": "Attach to Docker (orchestrator)",
         "type": "coreclr",
         "request": "attach",
         "processId": "${command:pickProcess}",
         "justMyCode": true
       }
     ]
   }
   ```

7. Press **F5**, select the `dotnet` process from the picker, and the debugger attaches.

---

### Debug Build Note

To enable full source-level breakpoints, build the container in Debug configuration.
Add a `docker/docker-compose.debug.yml` override:

```yaml
services:
  orchestrator:
    build:
      args:
        - BUILD_CONFIGURATION=Debug
    environment:
      - DOTNET_USE_POLLING_FILE_WATCHER=1
    ports:
      - "4024:4024"   # vsdbg remote debugger port
```

Start with the override (the key comes from `docker/.env` or `$env:ANTHROPIC_API_KEY`):
```powershell
docker compose -f docker/docker-compose.yml -f docker/docker-compose.debug.yml up -d
```

Then attach from VS 2022 or VS Code as described above — breakpoints in your source files will now bind correctly.

---

## API Reference

### `GET /health`
Returns service health status.

```bash
curl http://localhost:5000/health
```

Response:
```json
{ "status": "healthy", "timestamp": "2026-03-09T10:00:00Z" }
```

---

### `POST /api/run`
Submit a requirement to the full engineering team pipeline.

```bash
curl -X POST http://localhost:5000/api/run \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Build a REST API for a TODO app with JWT authentication using C# .NET 10 and SQL Server",
    "skipAgents": [],
    "maxReviewLoops": 3
  }'
```

Request body:

| Field | Type | Description |
|---|---|---|
| `requirement` | string (required) | Plain English description of what to build |
| `skipAgents` | string[] | Agents to skip: `pm`, `architect`, `developer`, `reviewer`, `qa`, `security`, `devops`, `docs`, `verifier` |
| `maxReviewLoops` | int | Max Developer→Reviewer retry cycles (default: 3) |

Response:
```json
{
  "success": true,
  "sessionId": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "artifacts": {
    "Requirements": "# Requirements\n...",
    "Architecture": "# Architecture\n...",
    "SourceCode": "### File: ...",
    "ReviewNotes": "APPROVED\n...",
    "TestResults": "### File: tests/...",
    "SecurityReport": "# Security Report\n...",
    "DeploymentConfig": "### File: Dockerfile\n...",
    "Documentation": "# README\n...",
    "VerificationReport": "| id | status |\n..."
  },
  "agentLog": [
    "🤖 Product Manager started",
    "✅ Product Manager completed in 8.2s",
    "..."
  ],
  "totalDuration": "00:03:42",
  "requirements": [
    {
      "id": "FR-1",
      "text": "Print Hello, World! to the console",
      "kind": "Code",
      "status": "Passed",
      "coveredBy": ["Software Developer"],
      "evidence": "src/HelloWorld/Program.cs writes the greeting",
      "source": "Product Manager"
    }
  ],
  "requirementsMet": true
}
```

---

### `POST /api/run/partial`
Same as `/api/run` but designed for skipping specific agents.

```bash
# Generate only requirements + architecture (skip everything else)
curl -X POST http://localhost:5000/api/run/partial \
  -H "Content-Type: application/json" \
  -d '{
    "requirement": "Build a payment processing service",
    "skipAgents": ["developer", "reviewer", "qa", "security", "devops", "docs"]
  }'
```

---

## Running Tests

```powershell
# Run all tests with coverage
dotnet test --collect:"XPlat Code Coverage" --results-directory TestResults

# Run only unit tests
dotnet test tests/MultiAgentDevTeam.UnitTests --collect:"XPlat Code Coverage"

# Run only integration tests
dotnet test tests/MultiAgentDevTeam.IntegrationTests

# Run with verbose output
dotnet test -v normal
```

Coverage report is generated in `TestResults/` as Cobertura XML.

---

## Project Structure

```
MultiAgentDevTeam/
├── src/
│   ├── MultiAgentDevTeam.Shared/          # Shared models, interfaces, BaseAgent
│   │   ├── Agents/BaseAgent.cs            # Abstract agent — calls Claude API
│   │   ├── Configuration/AgentConfig.cs   # Configuration model
│   │   ├── Interfaces/IAgent.cs           # Agent contract
│   │   └── Models/                        # Artifact, ArtifactStore, Request/Response
│   │
│   ├── MultiAgentDevTeam.Orchestrator/    # ASP.NET Core API + pipeline
│   │   ├── Services/OrchestratorService.cs# Full pipeline with feedback loops
│   │   ├── Program.cs                     # DI, routing, Swagger
│   │   └── appsettings.json
│   │
│   └── Agents/
│       ├── MultiAgentDevTeam.PMAgent/     # Product Manager
│       ├── MultiAgentDevTeam.ArchitectAgent/
│       ├── MultiAgentDevTeam.DeveloperAgent/
│       ├── MultiAgentDevTeam.ReviewerAgent/
│       ├── MultiAgentDevTeam.QAAgent/
│       ├── MultiAgentDevTeam.SecurityAgent/
│       ├── MultiAgentDevTeam.DevOpsAgent/
│       ├── MultiAgentDevTeam.DocsAgent/
│       └── MultiAgentDevTeam.VerifierAgent/ # Acceptance Verifier
│
├── tests/
│   ├── MultiAgentDevTeam.UnitTests/       # Artifact, Agent metadata, Orchestrator logic
│   └── MultiAgentDevTeam.IntegrationTests/# API endpoint tests via WebApplicationFactory
│
├── k8s/
│   ├── namespace.yaml
│   ├── secret.yaml.example                # Example only; deploy-k8s.ps1 creates the real Secret
│   ├── configmap.yaml
│   ├── pvc.yaml                           # Volume for saved sessions
│   ├── deployment.yaml                    # Orchestrator deployment
│   └── service.yaml                       # NodePort (localhost:30080)
│
├── docker/
│   ├── Dockerfile                         # Multi-stage .NET build
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── scripts/
│   ├── deploy-local.ps1                   # dotnet run locally
│   ├── deploy-docker.ps1                  # Docker Compose
│   ├── deploy-k8s.ps1                     # Kubernetes (Docker Desktop)
│   └── Resolve-AnthropicApiKey.ps1        # Finds the API key for all three scripts
│
├── NuGet.Config                           # Packages stored in shared_Environment
├── MultiAgentDevTeam.slnx
└── README.md
```

---

## Limitations & Guardrails

### Known Limitations

| Limitation | Mitigation |
|------------|------------|
| Agents can hallucinate file paths | `ProjectWriter` skips absolute and `..` paths and never writes into a folder that already has files |
| Generated code may not execute without a real runtime | Run in a sandbox (Docker container) |
| Context grows large in long sessions | Summarise artifacts before passing to next agent |
| Circular loops if reviewer always rejects | `MaxReviewLoops` cap enforced by Orchestrator |
| Agents may duplicate work | Orchestrator deduplicates artifact keys via `ArtifactStore` |

### Guardrails to Consider When Extending

- **Sandboxed execution** — run all shell commands inside Docker, never on the host machine
- **Token budget** — cap each agent's response to avoid runaway API costs
- **Human-in-the-loop** — pause before DevOps agent pushes to real infrastructure
- **Output validation** — parse and validate structured agent outputs before passing downstream
- **Secret scanning** — scan generated files for hardcoded API keys before storing

---

## NuGet Package Cache

All NuGet packages are stored in the shared environment to avoid duplication:
```
D:\Study\AILearning\shared_Environment\.nuget\packages\
```

This is configured in `NuGet.Config` at the solution root.

---

*Last Updated: April 2026*
