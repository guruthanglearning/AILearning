# Multi-Agent Engineering Team with Claude AI

> A blueprint for building an AI-powered software engineering team where each agent owns a distinct phase of the SDLC.

---

## Table of Contents

- [Is It Doable?](#is-it-doable)
- [Concept Overview](#concept-overview)
- [Agent Roster](#agent-roster)
- [Architecture](#architecture)
- [Orchestration Patterns](#orchestration-patterns)
- [Recommended Frameworks](#recommended-frameworks)
- [Implementation Blueprint](#implementation-blueprint)
- [Agent Communication Protocol](#agent-communication-protocol)
- [Example Workflow](#example-workflow)
- [Code Skeleton](#code-skeleton)
- [Tooling Each Agent Needs](#tooling-each-agent-needs)
- [Limitations & Guardrails](#limitations--guardrails)
- [Roadmap to Build This](#roadmap-to-build-this)

---

## Is It Doable?

**Yes — and it's one of the most practical uses of multi-agent AI today.**

The Anthropic Claude API natively supports multi-agent orchestration via the `Agent` tool pattern. You build a central **Orchestrator** that delegates tasks to specialized **Subagents**, each scoped to one engineering discipline. Each subagent can call real tools (file system, GitHub, Docker, test runners, linters, APIs) and return results back to the orchestrator.

Key enablers:
- **Claude's tool use** — agents call shell commands, APIs, and file editors
- **Claude's large context window** — agents share rich context without losing track
- **Anthropic Agent SDK** — official primitives for building orchestrator + subagent graphs
- **Frameworks** (CrewAI, LangGraph, AutoGen) — higher-level abstractions if needed

---

## Concept Overview

```
User Request
     │
     ▼
┌────────────────────┐
│   ORCHESTRATOR     │  ← "Engineering Manager"
│   (Master Agent)   │    Decomposes tasks, routes to agents,
│                    │    collects results, resolves conflicts
└────────┬───────────┘
         │ delegates to
         ▼
┌────────────────────────────────────────────────────────────┐
│                   SPECIALIST AGENTS                        │
│                                                            │
│  [PM]  →  [Architect]  →  [Developer]  →  [Reviewer]      │
│                                                            │
│  [QA/Tester]  →  [DevOps]  →  [Security]  →  [Docs]       │
└────────────────────────────────────────────────────────────┘
```

---

## Agent Roster

### 1. Product Manager Agent (PM)
**Responsibility:** Translate user intent into structured requirements.

| Attribute     | Detail |
|---------------|--------|
| Input         | Raw user request (natural language) |
| Output        | User stories, acceptance criteria, scope document |
| Tools         | None (pure reasoning) or Jira/Linear API |
| Prompt Style  | "You are a senior product manager. Extract functional and non-functional requirements..." |

---

### 2. Architect Agent
**Responsibility:** Design the system — tech stack, component breakdown, data flow, API contracts.

| Attribute     | Detail |
|---------------|--------|
| Input         | Requirements from PM Agent |
| Output        | Architecture Decision Record (ADR), component diagram (text/mermaid), API schema |
| Tools         | Web search (for best practices), file writer |
| Prompt Style  | "You are a principal software architect. Design a scalable system for the following requirements..." |

---

### 3. Developer Agent
**Responsibility:** Write production-quality code based on the architecture.

| Attribute     | Detail |
|---------------|--------|
| Input         | ADR, API schema, user stories |
| Output        | Source code files |
| Tools         | File system (read/write), code linter, shell (pip install, npm install) |
| Prompt Style  | "You are a senior software engineer. Implement the following component strictly following the architecture..." |

---

### 4. Code Reviewer Agent
**Responsibility:** Review generated code for correctness, style, security, and maintainability.

| Attribute     | Detail |
|---------------|--------|
| Input         | Source code from Developer Agent |
| Output        | Review comments, revised code (or approval) |
| Tools         | File reader, linter (pylint, eslint), static analysis |
| Prompt Style  | "You are a senior code reviewer. Review the following code for bugs, security issues, and style violations..." |

---

### 5. QA / Testing Agent
**Responsibility:** Write and execute tests. Report coverage and failures.

| Attribute     | Detail |
|---------------|--------|
| Input         | Source code, API schema, acceptance criteria |
| Output        | Unit tests, integration tests, test report |
| Tools         | Shell (pytest, jest, go test), file system, coverage tools |
| Prompt Style  | "You are a QA engineer. Write comprehensive tests for the following code targeting 80%+ coverage..." |

---

### 6. DevOps Agent
**Responsibility:** Package, containerize, and define deployment pipelines.

| Attribute     | Detail |
|---------------|--------|
| Input         | Source code, test results |
| Output        | Dockerfile, docker-compose.yml, CI/CD YAML (GitHub Actions), deployment scripts |
| Tools         | Shell (docker build, docker push), file system, GitHub API |
| Prompt Style  | "You are a DevOps engineer. Create a production-ready Docker and CI/CD setup for this application..." |

---

### 7. Security Agent
**Responsibility:** Audit code and infrastructure for vulnerabilities.

| Attribute     | Detail |
|---------------|--------|
| Input         | Source code, Dockerfile, dependencies |
| Output        | Security report, recommended fixes |
| Tools         | Shell (bandit, semgrep, npm audit, trivy), file reader |
| Prompt Style  | "You are an application security engineer. Audit this code for OWASP Top 10 vulnerabilities..." |

---

### 8. Documentation Agent
**Responsibility:** Generate developer docs, README, and API reference.

| Attribute     | Detail |
|---------------|--------|
| Input         | Source code, architecture, API schema |
| Output        | README.md, API docs (OpenAPI/Swagger), inline docstrings |
| Tools         | File system (read/write), docstring generators |
| Prompt Style  | "You are a technical writer. Generate comprehensive documentation for the following codebase..." |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        ORCHESTRATOR                              │
│                                                                  │
│  1. Parse user intent                                            │
│  2. Build task graph (which agents run in what order)            │
│  3. Dispatch tasks to subagents                                  │
│  4. Collect artifacts (code, docs, test reports)                 │
│  5. Resolve conflicts (e.g. reviewer rejects → back to dev)      │
│  6. Deliver final output to user                                 │
└──────────────────────┬───────────────────────────────────────────┘
                       │  Claude API calls with tool_use
         ┌─────────────┼─────────────────────────────┐
         ▼             ▼             ▼                ▼
    [PM Agent]  [Architect]   [Developer]      [Reviewer]
         │             │             │                │
    requirements   ADR + schema   source code    review notes
         └─────────────┴─────────────┴────────────────┘
                                │
              ┌─────────────────┼──────────────────┐
              ▼                 ▼                  ▼
         [QA Agent]       [DevOps Agent]    [Security Agent]
              │                 │                  │
          test suite      Dockerfile + CI      security report
              └─────────────────┴──────────────────┘
                                │
                         [Docs Agent]
                                │
                          README + API docs
                                │
                         FINAL DELIVERABLE
```

---

## Orchestration Patterns

### Pattern 1: Sequential Pipeline (Simplest)
Each agent completes before the next starts. Output of agent N is input of agent N+1.

```
PM → Architect → Developer → Reviewer → QA → DevOps → Security → Docs
```

**Best for:** Greenfield projects, well-defined requirements.

---

### Pattern 2: Parallel with Merge (Faster)
Agents that don't depend on each other run in parallel.

```
PM ──► Architect ──► Developer ─────────────────┐
                                                 │
                        ├──► Reviewer ───────────┤
                        │                        ▼
                        ├──► QA ─────────► Orchestrator (merge)
                        │                        │
                        └──► Security ────────────┘
                                                 │
                                          DevOps + Docs
```

**Best for:** Large tasks, time efficiency.

---

### Pattern 3: Feedback Loop (Most Robust)
Agents can reject and loop back. Reviewer rejects → Developer fixes → Reviewer re-reviews.

```
Developer ──► Reviewer ──► [APPROVED] ──► QA
                │
           [REJECTED]
                │
           Developer (revision)
```

**Best for:** Production-grade output, strict quality gates.

---

## Recommended Frameworks

| Framework      | Language | Best For                              | Notes |
|----------------|----------|---------------------------------------|-------|
| **Anthropic Agent SDK** | Python | Native Claude multi-agent graphs | Official, most integrated |
| **CrewAI**     | Python   | Quick agent role setup, built-in crew | High-level, opinionated |
| **LangGraph**  | Python   | Complex stateful agent graphs         | Graph-based, fine control |
| **AutoGen**    | Python   | Conversational multi-agent dialogue   | Microsoft, great for code gen |
| **Custom**     | Any      | Full control, no framework overhead   | Best for learning the internals |

**Recommendation for this project:** Start with **CrewAI** (fastest to prototype) then migrate to **Anthropic Agent SDK** or **LangGraph** for production control.

---

## Implementation Blueprint

### Project Structure

```
engineering_team/
├── orchestrator.py          # Master agent — task graph + routing
├── agents/
│   ├── base_agent.py        # Shared agent interface
│   ├── pm_agent.py          # Product Manager
│   ├── architect_agent.py   # Architect
│   ├── developer_agent.py   # Developer
│   ├── reviewer_agent.py    # Code Reviewer
│   ├── qa_agent.py          # QA / Testing
│   ├── devops_agent.py      # DevOps
│   ├── security_agent.py    # Security
│   └── docs_agent.py        # Documentation
├── tools/
│   ├── file_tools.py        # Read/write files
│   ├── shell_tools.py       # Run shell commands
│   ├── github_tools.py      # GitHub API calls
│   └── search_tools.py      # Web search
├── memory/
│   ├── shared_context.py    # Artifacts shared across agents
│   └── conversation_store.py
├── config.py                # Model IDs, API keys, limits
└── main.py                  # Entry point
```

---

## Agent Communication Protocol

Agents communicate through a **shared artifact store** — not directly with each other. The Orchestrator controls the flow.

```python
# Artifact types passed between agents
class Artifact:
    type: str           # "requirements", "architecture", "code", "tests", "report"
    content: str        # The actual content
    author: str         # Which agent produced it
    status: str         # "draft", "approved", "rejected"
    revision: int       # How many times it's been revised
    feedback: str       # Rejection reason (if status == "rejected")
```

---

## Example Workflow

**User Request:** `"Build a REST API for a TODO app with authentication"`

```
1. ORCHESTRATOR receives request
   └── Routes to PM Agent

2. PM AGENT outputs:
   - User Story: "As a user, I want to create, read, update, delete todos"
   - Auth: JWT-based login/register
   - Acceptance Criteria: endpoints + error codes defined

3. ARCHITECT AGENT outputs:
   - Stack: FastAPI + PostgreSQL + JWT
   - Endpoints: POST /auth/register, POST /auth/login, GET/POST/PUT/DELETE /todos
   - DB Schema: users(id, email, hashed_password), todos(id, user_id, title, done)

4. DEVELOPER AGENT outputs:
   - main.py, models.py, routes/auth.py, routes/todos.py, db.py
   - requirements.txt

5. REVIEWER AGENT outputs:
   - "SQL injection risk in raw query at routes/todos.py:34 — use ORM"
   - Status: REJECTED → back to Developer

6. DEVELOPER AGENT (revision 2) fixes issue → re-submits

7. REVIEWER AGENT: APPROVED

8. QA AGENT outputs:
   - test_auth.py, test_todos.py
   - Runs pytest → 23 tests passed, 87% coverage

9. SECURITY AGENT outputs:
   - Bandit scan: no high-severity issues
   - Recommends: add rate limiting to /auth endpoints

10. DEVOPS AGENT outputs:
    - Dockerfile, docker-compose.yml
    - .github/workflows/ci.yml (lint + test + build on PR)

11. DOCS AGENT outputs:
    - README.md with setup + usage
    - openapi.json auto-generated

12. ORCHESTRATOR delivers final package to user
```

---

## Code Skeleton

### `config.py`
```python
import os

ANTHROPIC_MODEL = "claude-opus-4-6"          # Most capable for complex reasoning
ANTHROPIC_MODEL_FAST = "claude-haiku-4-5-20251001"  # For simple/fast agents
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

MAX_REVIEW_LOOPS = 3     # Max times reviewer can reject before escalating
MAX_TOKENS = 8192
```

---

### `agents/base_agent.py`
```python
import anthropic
from config import ANTHROPIC_MODEL, ANTHROPIC_API_KEY

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

class BaseAgent:
    def __init__(self, role: str, system_prompt: str, tools: list = None):
        self.role = role
        self.system_prompt = system_prompt
        self.tools = tools or []

    def run(self, task: str, context: dict = None) -> str:
        messages = []
        if context:
            messages.append({
                "role": "user",
                "content": f"Context:\n{context}\n\nTask:\n{task}"
            })
        else:
            messages.append({"role": "user", "content": task})

        response = client.messages.create(
            model=ANTHROPIC_MODEL,
            max_tokens=8192,
            system=self.system_prompt,
            tools=self.tools,
            messages=messages
        )
        return response.content[0].text
```

---

### `agents/pm_agent.py`
```python
from agents.base_agent import BaseAgent

class PMAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Product Manager",
            system_prompt="""You are a senior product manager at a software company.
Given a user request, produce:
1. A list of clear user stories (As a <user>, I want <goal>, So that <reason>)
2. Functional requirements (numbered list)
3. Non-functional requirements (performance, security, scalability)
4. Acceptance criteria for each story
5. Out of scope items

Be specific and unambiguous. Output in structured markdown."""
        )
```

---

### `agents/architect_agent.py`
```python
from agents.base_agent import BaseAgent

class ArchitectAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            role="Software Architect",
            system_prompt="""You are a principal software architect.
Given product requirements, produce:
1. Technology stack recommendation with justification
2. High-level component diagram (text/mermaid format)
3. API contract (endpoints, request/response schemas)
4. Database schema
5. Key architectural decisions and trade-offs (ADR format)
6. Non-functional considerations (caching, auth, rate limiting)

Be precise. Output in structured markdown."""
        )
```

---

### `orchestrator.py`
```python
from agents.pm_agent import PMAgent
from agents.architect_agent import ArchitectAgent
from agents.developer_agent import DeveloperAgent
from agents.reviewer_agent import ReviewerAgent
from agents.qa_agent import QAAgent
from agents.devops_agent import DevOpsAgent
from agents.security_agent import SecurityAgent
from agents.docs_agent import DocsAgent
from config import MAX_REVIEW_LOOPS

class EngineeringTeamOrchestrator:
    def __init__(self):
        self.pm = PMAgent()
        self.architect = ArchitectAgent()
        self.developer = DeveloperAgent()
        self.reviewer = ReviewerAgent()
        self.qa = QAAgent()
        self.devops = DevOpsAgent()
        self.security = SecurityAgent()
        self.docs = DocsAgent()

    def run(self, user_request: str) -> dict:
        artifacts = {}

        print("=== PM Agent: Gathering Requirements ===")
        artifacts["requirements"] = self.pm.run(user_request)

        print("=== Architect Agent: Designing System ===")
        artifacts["architecture"] = self.architect.run(
            "Design the system",
            context=artifacts["requirements"]
        )

        print("=== Developer Agent: Writing Code ===")
        artifacts["code"] = self.developer.run(
            "Implement the system",
            context={**artifacts}
        )

        # Feedback loop: review until approved or max loops reached
        for attempt in range(MAX_REVIEW_LOOPS):
            print(f"=== Reviewer Agent: Review attempt {attempt + 1} ===")
            review = self.reviewer.run("Review the code", context=artifacts["code"])
            artifacts["review"] = review

            if "APPROVED" in review.upper():
                print("Code approved.")
                break
            else:
                print("Code rejected. Sending back to Developer...")
                artifacts["code"] = self.developer.run(
                    f"Fix the following issues:\n{review}",
                    context=artifacts["code"]
                )

        print("=== QA Agent: Writing and Running Tests ===")
        artifacts["tests"] = self.qa.run("Write tests", context=artifacts)

        print("=== Security Agent: Security Audit ===")
        artifacts["security_report"] = self.security.run("Audit", context=artifacts["code"])

        print("=== DevOps Agent: Creating Deployment Files ===")
        artifacts["deployment"] = self.devops.run("Create deployment config", context=artifacts)

        print("=== Docs Agent: Generating Documentation ===")
        artifacts["docs"] = self.docs.run("Write documentation", context=artifacts)

        return artifacts


if __name__ == "__main__":
    team = EngineeringTeamOrchestrator()
    result = team.run("Build a REST API for a TODO app with JWT authentication")

    for artifact_name, content in result.items():
        print(f"\n{'='*60}")
        print(f"ARTIFACT: {artifact_name.upper()}")
        print('='*60)
        print(content[:500] + "..." if len(content) > 500 else content)
```

---

## Tooling Each Agent Needs

| Agent         | Tools Required |
|---------------|----------------|
| PM            | None (reasoning only) — optionally Jira/Linear API |
| Architect     | Web search (best practices lookup), file writer |
| Developer     | File read/write, shell (pip/npm), code linter |
| Reviewer      | File reader, pylint/eslint, static analysis (bandit, semgrep) |
| QA            | Shell (pytest/jest), file read/write, coverage reporter |
| DevOps        | Shell (docker build/push), file writer, GitHub Actions API |
| Security      | Shell (bandit, trivy, semgrep, npm audit), file reader |
| Docs          | File read/write, docstring extractor |

### Shared Tool Interface
```python
# tools/shell_tools.py
import subprocess

def run_command(cmd: str, cwd: str = ".") -> dict:
    result = subprocess.run(
        cmd, shell=True, cwd=cwd,
        capture_output=True, text=True, timeout=60
    )
    return {
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode
    }
```

---

## Limitations & Guardrails

### Known Limitations

| Limitation | Mitigation |
|------------|------------|
| Agents hallucinate file paths | Always validate paths before writing |
| Code may not execute without real runtime | Run in sandbox (Docker container) |
| Context grows large in long sessions | Summarize artifacts before passing to next agent |
| Circular loops if reviewer always rejects | Enforce `MAX_REVIEW_LOOPS` cap |
| Agents may duplicate work | Orchestrator must deduplicate artifact keys |

### Guardrails to Implement
- **Sandboxed execution** — run all shell commands inside Docker, never on host
- **Token budget** — cap each agent's response to avoid runaway costs
- **Human-in-the-loop** — pause before DevOps agent pushes to real infrastructure
- **Output validation** — parse structured outputs (JSON schema validation) before passing downstream
- **Secret scanning** — before writing any file, scan for hardcoded API keys

---

## Roadmap to Build This

### Phase 1 — Prototype (Week 1-2)
- [ ] Set up `BaseAgent` class with Claude API
- [ ] Implement PM + Architect + Developer agents (text only, no tools)
- [ ] Build basic orchestrator with sequential pipeline
- [ ] Test with simple requests ("build a calculator CLI")

### Phase 2 — Add Tools (Week 3-4)
- [ ] Add file read/write tools to Developer + Docs agents
- [ ] Add shell execution tool (sandboxed via Docker)
- [ ] Add QA agent that actually runs `pytest`
- [ ] Implement feedback loop (Reviewer → Developer)

### Phase 3 — Full Pipeline (Week 5-6)
- [ ] Add Security + DevOps agents
- [ ] Add parallel agent execution (asyncio)
- [ ] Add shared artifact store with versioning
- [ ] Implement human-in-the-loop pause before deployment

### Phase 4 — Production Hardening (Week 7-8)
- [ ] Add cost tracking per agent per request
- [ ] Add logging and observability (agent decisions + tool calls)
- [ ] Add retry logic and error recovery
- [ ] Build simple UI (Streamlit) to visualize agent workflow progress

---

## Further Reading

- [Anthropic Multi-Agent Documentation](https://docs.anthropic.com/en/docs/agents-and-tools/agents-overview)
- [CrewAI Documentation](https://docs.crewai.com/)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [AutoGen by Microsoft](https://microsoft.github.io/autogen/)
- [Claude Model IDs Reference](https://docs.anthropic.com/en/docs/about-claude/models/overview)

---

## Summary

| Agent         | Phase        | Key Output              |
|---------------|--------------|-------------------------|
| PM            | Planning     | User stories + requirements |
| Architect     | Design       | ADR + API schema        |
| Developer     | Build        | Source code             |
| Reviewer      | Quality Gate | Approval / Rejection    |
| QA            | Validation   | Test suite + report     |
| Security      | Audit        | Vulnerability report    |
| DevOps        | Deployment   | Dockerfile + CI/CD      |
| Docs          | Documentation| README + API docs       |

**This is entirely buildable with the Claude API today.** The core pattern is: one orchestrator, N specialist subagents, a shared artifact store, and real tools for file I/O and shell execution. Start with the Phase 1 prototype and grow from there.

---

*Last Updated: March 2026*
