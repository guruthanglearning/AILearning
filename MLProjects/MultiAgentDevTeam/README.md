# Multi-Agent Dev Team

An AI-powered software engineering team built in **C# .NET 10**, orchestrated via the **Anthropic Claude API**. Submit a plain-English requirement and receive a complete software package — requirements, architecture, source code, tests, security report, deployment config, and documentation — all produced by a team of specialised AI agents.

---

## Table of Contents

- [Purpose](#purpose)
- [Architecture](#architecture)
- [Agent Roles](#agent-roles)
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
│           RESPONSE → all artifacts returned to user            │
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
                            DevOps + Docs
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
| `AgentConfiguration__DefaultModel` | No | Claude model for agents (default: `claude-opus-4-6`) |
| `AgentConfiguration__FastModel` | No | Fast model for light tasks (default: `claude-haiku-4-5-20251001`) |
| `AgentConfiguration__MaxReviewLoops` | No | Max Developer→Reviewer cycles (default: `3`) |
| `AgentConfiguration__MaxTokens` | No | Max tokens per agent response (default: `8192`) |
| `AgentConfiguration__TimeoutSeconds` | No | Agent timeout in seconds (default: `300`) |

---

## How to Run

### Option 1 — Local (dotnet run)

```powershell
# From the project root
.\scripts\deploy-local.ps1 -ApiKey "sk-ant-xxxx"

# Skip tests for faster startup
.\scripts\deploy-local.ps1 -ApiKey "sk-ant-xxxx" -SkipTests
```

Access:
- Swagger UI: http://localhost:5000
- Health: http://localhost:5000/health

---

### Option 2 — Docker

```powershell
# Build images and start containers
.\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"

# Stop and remove containers
.\scripts\deploy-docker.ps1 -Down
```

Or using docker compose directly:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-xxxx"
docker compose -f docker/docker-compose.yml up -d
```

Access:
- UI: http://localhost:3000
- Swagger UI: http://localhost:5000
- Logs: `docker logs -f orchestrator`

---

### Option 3 — Kubernetes (Docker Desktop)

```powershell
# Full deploy (builds image + deploys to K8s)
.\scripts\deploy-k8s.ps1 -ApiKey "sk-ant-xxxx"

# Skip image rebuild (use existing image)
.\scripts\deploy-k8s.ps1 -ApiKey "sk-ant-xxxx" -SkipBuild

# Tear everything down
.\scripts\deploy-k8s.ps1 -Down
```

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
   .\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"
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
   .\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"
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

Start with the override:
```powershell
$env:ANTHROPIC_API_KEY = "sk-ant-xxxx"
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
| `skipAgents` | string[] | Agents to skip: `pm`, `architect`, `developer`, `reviewer`, `qa`, `security`, `devops`, `docs` |
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
    "Documentation": "# README\n..."
  },
  "agentLog": [
    "🤖 Product Manager started",
    "✅ Product Manager completed in 8.2s",
    "..."
  ],
  "totalDuration": "00:03:42"
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
│       └── MultiAgentDevTeam.DocsAgent/
│
├── tests/
│   ├── MultiAgentDevTeam.UnitTests/       # Artifact, Agent metadata, Orchestrator logic
│   └── MultiAgentDevTeam.IntegrationTests/# API endpoint tests via WebApplicationFactory
│
├── k8s/
│   ├── namespace.yaml
│   ├── secret.yaml                        # K8s secret template
│   ├── configmap.yaml
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
│   └── deploy-k8s.ps1                     # Kubernetes (Docker Desktop)
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
| Agents can hallucinate file paths | Validate paths before writing |
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
