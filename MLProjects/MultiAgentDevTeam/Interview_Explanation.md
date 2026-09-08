# Multi-Agent Dev Team - Interview Explanation Guide

## 📋 Quick Project Summary

**Project**: AI-Powered Software Engineering Team (Multi-Agent Orchestration)
**Core Idea**: Submit a plain-English requirement, get back a complete software package — requirements, architecture, source code, tests, security report, deployment config, and docs
**Architecture**: 8 specialised Claude-backed agents, one per SDLC phase, coordinated by a central Orchestrator with a Developer↔Reviewer feedback loop
**Tech Stack**: C# .NET 10, ASP.NET Core Minimal APIs, Anthropic Claude API (`Anthropic.SDK`), Blazor Server UI, Docker, Kubernetes
**Scale**: 167 passing unit/integration tests (xUnit + Moq + FluentAssertions + bUnit) plus a Playwright E2E suite, across 4 test projects

---

## 🎯 Opening Statement (30 seconds)

*"I built a multi-agent AI system in C# .NET 10 that automates the software development lifecycle. You submit a plain-English requirement over HTTP, and 8 specialised Claude-backed agents — Product Manager, Architect, Developer, Reviewer, QA, Security, DevOps, and Technical Writer — run in sequence, with a Developer-Reviewer feedback loop that can send code back for revision up to 3 times, and QA/Security running in parallel once code is approved. Progress streams to a Blazor UI in real time over Server-Sent Events, every run is persisted so you can browse session history, and the whole thing deploys to Docker or Kubernetes."*

---

## 🤖 The Architecture: 8 Agents, 1 Orchestrator, 1 Rule

### The One Rule: Agents Never Talk to Each Other

```
Agent A ──X──► Agent B            ← Does NOT happen

Agent A ──► Orchestrator ──► Agent B   ← How it actually works
```

Every agent is stateless and only ever sees what the Orchestrator hands it in an `AgentRequest`. All cross-agent communication goes through a shared **`ArtifactStore`** keyed by `ArtifactType` (Requirements, Architecture, SourceCode, ReviewNotes, TestResults, SecurityReport, DeploymentConfig, Documentation). This is a deliberate constraint, not an accident — it means every agent's input is fully reproducible and inspectable from the store, which is what makes the whole pipeline testable and debuggable.

### The 8 Agents

| Agent | Phase | Output | Real Behaviour |
|---|---|---|---|
| **Product Manager** | 1 | Requirements | Extracts user stories, acceptance criteria, NFRs from the raw request |
| **Architect** | 2 | Architecture ADR | Tech stack, API schema, DB schema, component diagram |
| **Developer** | 3 | Source code | Full C# .NET 10 implementation, each file labeled `### File: path/to/File.cs` |
| **Reviewer** | 3 (loop) | Review notes | First line of output must be exactly `APPROVED` or `REJECTED` — this is the entire gate mechanism |
| **QA Engineer** | 4 (parallel) | Test suite | xUnit unit + integration tests targeting 80%+ coverage |
| **Security Engineer** | 4 (parallel) | Security report | OWASP Top 10 audit, hardcoded-secret detection |
| **DevOps Engineer** | 5 | Deployment config | Dockerfile, docker-compose, K8s manifests, CI/CD |
| **Technical Writer** | 6 | Documentation | README, API reference, architecture doc |

Every agent inherits from a single **`BaseAgent`** abstract class (`MultiAgentDevTeam.Shared`) that owns all the Claude API plumbing — building the `MessageParameters`, calling `AnthropicClient.Messages.GetClaudeMessageAsync`, timing the call, and wrapping success/failure into a uniform `AgentResponse`. A concrete agent only supplies three things: its `Name`, its `OutputType`, and its `SystemPrompt`. This is the same discipline as the 7-agent design in my StockRecommendationPlatform project, applied to a compiled, strongly-typed language instead of Python.

### Structured Output Without Tool Calling

Unlike a tool-schema approach, agents here communicate structure through **prompt convention**, not a JSON schema: the Reviewer's system prompt mandates *"Your first line of output must be either APPROVED or REJECTED"*, and the Orchestrator gates the feedback loop with a plain `reviewContent.StartsWith("APPROVED", StringComparison.OrdinalIgnoreCase)` check. It's a smaller surface area than tool calling, and it works well here because every agent's *only* consumer is either the next agent's prompt context or the end user — nothing needs to bind the output into a typed object at the C# layer.

---

## 🔄 Complete Workflow Example

### Real Pipeline Run: `POST /api/run/stream`

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: PM Agent                                             │
│   Task: "Extract complete requirements from: <user text>"     │
│   Output → ArtifactStore[Requirements]                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Architect Agent                                      │
│   Context: Requirements                                       │
│   Output → ArtifactStore[Architecture]                        │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Developer ⇄ Reviewer feedback loop (max 3 attempts)  │
├─────────────────────────────────────────────────────────────┤
│  Attempt 1: Developer writes code → Reviewer: "REJECTED       │
│             — missing null checks on line 42"                 │
│  Attempt 2: Developer revises (PreviousFeedback = review text)│
│             → Reviewer: "APPROVED — clean, well-tested"       │
│  Loop exits early on APPROVED; otherwise proceeds with the    │
│  last version after MaxReviewLoops is reached                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 4: QA Agent + Security Agent — Task.WhenAll (parallel)  │
│  QA:       80%+ coverage test suite                            │
│  Security: OWASP Top 10 audit                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 5: DevOps Agent → Dockerfile, docker-compose, K8s, CI/CD│
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 6: Docs Agent → README, API reference, architecture doc │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Every step's progress message ("🤖 X started", "✅ X          │
│ completed in Ns") is written to an unbounded System.Threading │
│ .Channels.Channel<string> and streamed to the client as SSE   │
│ (`data: {"message": "..."}\n\n`) in real time — the Blazor    │
│ Home page's progress log updates live, not after completion.  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ Final: session persisted to sessions/<guid>.json via          │
│ ISessionRepository — regardless of success or failure — so    │
│ the Sessions page can list it and SessionDetail can replay it │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Technical Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    BLAZOR SERVER UI (:3000)                     │
│  Home (live SSE streaming submit) · Sessions (history list)     │
│  SessionDetail (replay a past run's artifacts)                  │
└────────────────────────────────┬─────────────────────────────────┘
                                 │ HTTP / SSE
                                 ▼
┌────────────────────────────────────────────────────────────────┐
│              ORCHESTRATOR API (ASP.NET Core, :5000)              │
│  Fixed-window rate limiter (10 req/min default, per endpoint)   │
│                                                                  │
│  POST /api/run           – full pipeline, blocking               │
│  POST /api/run/stream    – full pipeline, SSE progress            │
│  POST /api/run/partial   – run with specific agents skipped       │
│  GET  /api/sessions       – list recent sessions                  │
│  GET  /api/sessions/{id}  – retrieve one session's full record    │
│  GET  /health              – liveness/readiness                   │
│                                                                  │
│  OrchestratorService: PM → Architect → [Developer ⇄ Reviewer]   │
│                        → [QA ‖ Security] → DevOps → Docs         │
│  ArtifactStore (in-memory, per-run) · FileSessionRepository     │
│  (JSON files under sessions/, survives restarts)                 │
└────────────────────────────────┬─────────────────────────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │   Anthropic Claude API   │
                    │   claude-opus-4-6 (def.) │
                    │   claude-haiku-4-5 (fast)│
                    └─────────────────────────┘
```

### Technology Stack

| Layer | Technology |
|---|---|
| Language / runtime | C# .NET 10 |
| API framework | ASP.NET Core Minimal APIs, Swagger/OpenAPI |
| LLM client | `Anthropic.SDK` (`AnthropicClient.Messages.GetClaudeMessageAsync`) |
| Frontend | Blazor Server (interactive, no separate JS SPA) |
| Streaming | `IAsyncEnumerable<string>` over `System.Threading.Channels.Channel<string>` → SSE |
| Session persistence | `ISessionRepository` → `FileSessionRepository` (JSON files, pluggable for a real DB later) |
| Rate limiting | ASP.NET Core `RateLimiter` middleware, fixed-window, config-driven |
| Testing | xUnit, Moq, FluentAssertions (unit + integration), bUnit + Playwright (Blazor UI unit + E2E) |
| Containers | Docker (multi-stage build), Docker Compose |
| Orchestration | Kubernetes manifests — namespace, secret, configmap, Deployment, Service (Docker Desktop K8s) |
| Package cache | NuGet packages centralized in the workspace's `shared_Environment` |

---

## 🎯 Why This Architecture?

```
┌────────────────────────────────────────────────────────────┐
│ Design Goal → Technical Solution                            │
├────────────────────────────────────────────────────────────┤
│ 🧩 SEPARATION OF CONCERNS                                    │
│    → One agent per SDLC discipline; agents never call each  │
│      other directly, only through the Orchestrator + shared │
│      ArtifactStore — every input is reproducible             │
│                                                               │
│ 🛡️ QUALITY GATE, NOT JUST GENERATION                         │
│    → Developer↔Reviewer feedback loop (max 3 rounds) means   │
│      code isn't accepted just because it was generated —     │
│      it has to pass a structured review first                │
│                                                               │
│ ⚡ TIME EFFICIENCY WHERE IT'S SAFE                            │
│    → QA and Security have no dependency on each other, so    │
│      they run via Task.WhenAll instead of sequentially        │
│                                                               │
│ 👀 OBSERVABILITY DURING A SLOW PROCESS                        │
│    → A full pipeline run can take minutes; SSE streaming      │
│      means the user watches real progress, not a spinner      │
│                                                               │
│ 🔁 REPRODUCIBILITY                                            │
│    → Every session (success or failure) is persisted to disk  │
│      with its full artifact set — nothing is lost if the      │
│      pipeline throws midway                                   │
└────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Challenges & Solutions

### Challenge 1: Preventing Infinite Review Loops
**Problem**: A Reviewer that never approves would loop forever.
**Solution**: `MaxReviewLoops` (default 3, configurable per-request or via `AgentConfiguration`) hard-caps the Developer↔Reviewer cycle. On the final attempt, if still rejected, the Orchestrator logs a warning and proceeds with the last generated version instead of failing the whole pipeline — a deliberate choice that a "good enough, flagged" result beats no result at all for a prototyping tool.

### Challenge 2: Streaming Progress from a Multi-Minute Pipeline
**Problem**: A full 8-agent run can take minutes; a blocking HTTP call with no feedback is a bad UX, but the pipeline logic shouldn't be duplicated for a streaming vs. non-streaming path.
**Solution**: `ExecutePipelineAsync` is the single source of truth and always writes progress messages to a `Channel<string>`. `RunAsync` (blocking) just drains that channel without exposing it; `StreamAsync` (SSE) forwards each message to the caller as it arrives via `IAsyncEnumerable<string>`. One pipeline implementation, two consumption modes — no logic duplication.

### Challenge 3: Windows Smart App Control Blocking Freshly-Built DLLs
**Problem**: Windows 11's Smart App Control blocks newly compiled, unsigned DLLs from running — breaks `dotnet test`/`dotnet run` after every clean build, with a cryptic `0x800711C7` error.
**Solution**: A pre-flight check (`(Get-ItemProperty 'HKLM:\...\CI\Policy').VerifiedAndReputablePolicyState`) plus a documented, mandatory `Unblock-File` sweep over the build output before every test/run — codified directly in the project's Claude instructions so the workflow doesn't silently break on this machine. Not something a purely cloud-CI project would ever hit, but a real Windows-dev-box gotcha.

### Challenge 4: Making Sure Tests Never Hit the Real Claude API
**Problem**: Every agent inherits `BaseAgent`, which owns a live `AnthropicClient` — naive tests would burn real API calls and money, and be flaky on network issues.
**Solution**: `BaseAgentTests` and `AgentTests` mock the HTTP layer directly (`MockHttpMessageHandler`) rather than mocking `AnthropicClient` itself, so the real SDK serialization/deserialization path is still exercised — just against a fake HTTP response. Integration tests use `WebApplicationFactory` with the DI container's `AnthropicClient` registration swapped for a test double, so `/api/run` and `/api/run/stream` are tested end-to-end at the API layer without ever leaving the process.

### Challenge 5: Debugging a Container Without Losing Breakpoints
**Problem**: The production Dockerfile builds in Release mode, which strips PDB symbols — attaching a debugger works, but breakpoints on source lines silently don't bind.
**Solution**: A documented `docker-compose.debug.yml` override that rebuilds with `BUILD_CONFIGURATION=Debug` and exposes the `vsdbg` port, so both Visual Studio's "Attach to Process → Docker (Linux Container)" flow and VS Code's remote-attach flow get full source-level breakpoints when needed, without permanently shipping a debug image.

---

## 🔍 Common Interview Questions & Answers

### Q1: Why C# / .NET instead of Python for a multi-agent LLM system?

**Answer**: "Most multi-agent demos are Python, so I deliberately built this one in C# .NET 10 to show the pattern isn't language-specific — it's an orchestration and interface-design problem. Strong typing actually helps here: `IAgent`, `ArtifactType`, and `AgentRequest`/`AgentResponse` give me compile-time guarantees that every agent implements the same contract, and ASP.NET Core's DI container makes registering 8 agents as `IEnumerable<IAgent>` and resolving them by `OutputType` trivial."

### Q2: How do agents avoid stepping on each other or losing context?

**Answer**: "Two mechanisms. First, agents never call each other directly — everything routes through the Orchestrator, which is the only thing that knows the phase order. Second, all cross-agent context flows through a per-run `ArtifactStore` keyed by `ArtifactType`, so when the Developer agent runs, its context is explicitly built as 'give it the Requirements and Architecture artifacts' — not 'give it everything so far.' That keeps prompts focused and keeps the data flow auditable — I can log exactly what each agent saw."

### Q3: What happens if the Reviewer keeps rejecting the code?

**Answer**: "The loop is capped at `MaxReviewLoops` — 3 by default, configurable per-request. Each rejection's feedback text becomes the next attempt's `PreviousFeedback`, so the Developer agent sees exactly what was flagged and revises against it rather than starting from scratch. If it's still rejected after the max attempts, the Orchestrator logs a warning and proceeds with the last version rather than failing the entire pipeline — for a prototyping tool, a flagged 'best effort' result is more useful than nothing."

### Q4: Why JSON files for session storage instead of a database?

**Answer**: "It's a deliberate, honest scoping choice — `ISessionRepository` is an interface, and `FileSessionRepository` is one implementation. For a project whose main value is demonstrating the orchestration pattern, a database adds operational weight (a container, a connection string, migrations) without teaching anything new about multi-agent design. Because it's behind an interface, swapping in an EF Core/Postgres-backed implementation later is a drop-in change — nothing above the repository layer would need to know."

### Q5: How do you test agents without burning real API calls?

**Answer**: "I mock at the HTTP layer, not the SDK layer — a custom `MockHttpMessageHandler` intercepts the request `AnthropicClient` would send and returns a canned response. That way the SDK's own request-building and response-parsing code still runs for real in tests, and I'm only faking the network boundary. For the API layer, `WebApplicationFactory` spins up the whole ASP.NET Core pipeline in-process with that same test double wired into DI, so `/api/run/stream`'s SSE behavior is verified end-to-end without a real Claude call or a real running server."

### Q6: Why do QA and Security run in parallel but Developer and Reviewer don't?

**Answer**: "It comes down to data dependencies. QA and Security both only need the approved source code — neither depends on the other's output, so `Task.WhenAll` runs them concurrently and that phase takes as long as the slower of the two instead of both combined. Developer and Reviewer are inherently sequential: the Reviewer needs the Developer's actual code to review, and the Developer needs the Reviewer's feedback to revise — there's no way to parallelize a dependency chain like that."

### Q7: What's the biggest limitation of this system today?

**Answer**: "Two things I'd flag honestly. First, agents can still hallucinate file paths or produce code that doesn't compile — there's no sandboxed execution step that actually builds and runs what the Developer agent produces before handing it to QA. Second, the `ArtifactStore` is in-memory per request; if the process crashes mid-pipeline, that run's in-flight state is gone (though the *completed* artifacts up to that point are still safely captured because sessions persist incrementally through `PersistSessionAsync` in a `finally` block). Both are addressable — sandboxed execution via a disposable container, and a proper checkpoint-per-phase persistence model — but they're not built yet."

### Q8: How would you extend this to support other LLM providers, not just Claude?

**Answer**: "`BaseAgent` currently owns a concrete `AnthropicClient` from the DI container. I'd extract an `ILlmClient` abstraction with a single `CompleteAsync(system, messages, model, maxTokens)` method, implement it for Anthropic and for whatever other provider, and inject that instead. Every concrete agent (`PMAgent`, `DeveloperAgent`, etc.) wouldn't change at all — they only know about `SystemPrompt` and `Model`, not the transport. That's exactly the value of `BaseAgent` centralizing the API-calling logic in one place instead of duplicating it across 8 agents."

---

## 🚀 Deployment

### Local
```powershell
.\scripts\deploy-local.ps1 -ApiKey "sk-ant-xxxx"
# Swagger UI → http://localhost:5000
```

### Docker
```powershell
.\scripts\deploy-docker.ps1 -ApiKey "sk-ant-xxxx"
# UI → http://localhost:3000, Swagger → http://localhost:5000
```

### Kubernetes (Docker Desktop)
```powershell
.\scripts\deploy-k8s.ps1 -ApiKey "sk-ant-xxxx"
kubectl get pods -n multi-agent-dev-team -w
# Swagger → http://localhost:30080/health
```

---

## 📚 Project Structure

```
MultiAgentDevTeam/
├── src/
│   ├── MultiAgentDevTeam.Shared/           # BaseAgent, IAgent, ArtifactStore, AgentConfiguration
│   ├── MultiAgentDevTeam.Orchestrator/     # Minimal API host, OrchestratorService, FileSessionRepository
│   ├── MultiAgentDevTeam.BlazorUI/         # Home (live streaming), Sessions, SessionDetail pages
│   └── Agents/                              # 8 agent projects, one per SDLC phase
├── tests/
│   ├── MultiAgentDevTeam.UnitTests/        # BaseAgent, ArtifactStore, OrchestratorService (mocked HTTP)
│   ├── MultiAgentDevTeam.IntegrationTests/ # WebApplicationFactory — /api/run, /api/run/stream, /api/sessions
│   ├── MultiAgentDevTeam.BlazorUI.UnitTests/ # bUnit component tests
│   └── MultiAgentDevTeam.BlazorUI.E2ETests/  # Playwright, full browser flow
├── k8s/                                      # namespace, secret, configmap, deployment, service
├── docker/                                   # Multi-stage Dockerfile + docker-compose
├── scripts/                                  # deploy-local / deploy-docker / deploy-k8s (+ unblock-dlls)
├── MultiAgentDevTeam.slnx
└── README.md
```

---

## 🎓 Skills Demonstrated

### Technical Skills
```
✅ Multi-agent LLM orchestration (Anthropic Claude API, structured prompting)
✅ ASP.NET Core Minimal APIs, SSE streaming (IAsyncEnumerable + Channels)
✅ Async/await, Task.WhenAll for safe parallelism
✅ Dependency injection design (IAgent, ISessionRepository abstractions)
✅ Blazor Server (interactive server-rendered UI, no separate SPA build)
✅ xUnit + Moq + FluentAssertions, bUnit, Playwright E2E
✅ Docker multi-stage builds, Kubernetes manifests
```

### Architectural Skills
```
✅ Interface-driven design enabling swappable implementations (session storage, LLM client)
✅ Feedback-loop / quality-gate pipeline design with a hard iteration cap
✅ Safe parallel execution identified by data-dependency analysis, not guesswork
✅ Testing strategy that mocks at the transport boundary, not the SDK boundary
```

### Soft Skills / Process
```
✅ Honest self-assessment of limitations (no sandboxed execution yet, in-memory
   per-run state) rather than overselling the prototype
✅ Documenting a real platform-specific gotcha (Windows Smart App Control) so it
   doesn't silently block future work
```

---

## 💼 Closing Statement

*"This project demonstrates that multi-agent orchestration is a general software-architecture pattern, not something tied to Python or any one LLM SDK — the same discipline of narrow-scoped agents, a central coordinator, and a shared artifact contract applies just as cleanly in a strongly-typed, compiled language with real interfaces and DI. It also shows I think about the full lifecycle of an AI feature: not just 'call the LLM and print the result,' but streaming UX for a slow process, persisted history, a quality gate with a hard iteration cap so it can't loop forever, and a test suite that never touches the real API.*

*I'm happy to go deeper into the feedback-loop design, the SSE streaming implementation, or how I'd harden this toward sandboxed code execution."*

---

## 📞 Follow-Up Topics

If the interviewer wants to go deeper, be ready to discuss:

- **Agent design**: why `BaseAgent` centralizes the Claude call and what each concrete agent actually varies (`SystemPrompt`, `Model`, `MaxTokens`)
- **Streaming**: how one `Channel<string>` backs both the blocking and SSE endpoints without duplicating pipeline logic
- **The feedback loop**: exact gate condition (`StartsWith("APPROVED")`), why prompt convention was chosen over a tool-call schema here
- **Testing strategy**: mocking at the HTTP boundary vs. the SDK boundary, and why that distinction matters for confidence in tests
- **Rate limiting**: fixed-window limiter, why it's config-driven via `IOptions<AgentConfiguration>` instead of hardcoded
- **Deployment**: Docker debug-symbol stripping, the `docker-compose.debug.yml` override for source-level breakpoints in a container
- **What's next**: sandboxed execution of generated code, swapping `FileSessionRepository` for a real database, multi-provider LLM abstraction

---

*Document Version: 1.0*
*Last Updated: September 8, 2026*
*Project: Multi-Agent Dev Team*
