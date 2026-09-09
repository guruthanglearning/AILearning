# AILearning — Claude Instructions

## Browser

Always open the all the project UI in AILearning folder  (and any other local web app in this workspace) in **Microsoft Edge** (`msedge`). Never use Chrome or any other browser. Edge is at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.

## Permissions Policy

### Local coding actions — no permission needed
Proceed without asking for confirmation on any of the following within `D:\Study\AILearning`:
- Reading, editing, creating, or deleting files and directories
- Running tests, linters, formatters, build tools, or dev servers
- Executing git commands (commit, diff, log, status, branch, merge)
- Installing packages into the shared virtual environment
- Restarting backend or frontend processes
- Running bash/PowerShell/Python scripts that operate entirely locally

### Always ask permission before
- **Accessing the internet** — any outbound HTTP/HTTPS request to an external host (outside localhost / 127.0.0.1), web searches, or API calls to third-party services not already configured in the project
- **Pushing to remote repositories** — `git push` or any action that writes to a remote
- **Anything destructive or irreversible** — force-deleting branches, dropping databases, wiping data that cannot be recovered
- **Any action that could be harmful** — security exploits, credential exfiltration, mass data operations on production systems, or anything that seems dangerous or outside normal development work

### Privacy & PII
- Never log, print, store, commit, or transmit any personally identifiable information (PII) — names, emails, phone numbers, passwords, API keys, tokens, or financial account details
- If a file or output appears to contain PII, stop and flag it to the user before proceeding
- API keys and secrets must never be committed to git; verify `.gitignore` covers them before any commit

## Pull Request & Code Review Workflow

Once a change is ready and pushing has been authorized (per the Permissions Policy above), the default flow for **every project** in this workspace is branch → PR → Codex review → merge — not a direct push to `main`. This applies to **any** file change, code or documentation (`*.md` files — README, Interview_Explanation guides, etc. included), not just application code.

1. Push to a feature branch (never directly to `main`) and open a PR.
2. Request a review from the **Codex CLI** (`codex exec`, installed and ChatGPT-authenticated locally on this machine — not a GitHub App; none is installed on these repos). Run it non-interactively (e.g. `-s workspace-write -c approval_policy="never"`) so it can inspect the diff and report findings without blocking on approval prompts. For a docs-only PR this means a factual-accuracy review — checking claims, commands, and counts against the real code/tests — not a code-quality review.
3. Address every finding Codex reports: fix it (or explain why no change is needed), and reply on the corresponding PR comment thread — pushing a fix commit alone is not sufficient, the thread itself needs a reply so it's visible that the finding was addressed.
4. Ask Codex to re-review; repeat step 3 until it confirms the PR is good to merge.
5. Merge, then deploy/validate per that project's own process (Docker, Kubernetes, a local dev server — whatever applies to that project), and report the outcome.

Skip this cycle only when the user explicitly says to push a specific change straight to `main`. A subproject's own `CLAUDE.md` being silent on PR process, or only gating `git push` behind confirmation, is not an exception — this workflow applies workspace-wide regardless of what an individual project's instructions do or don't say about it.

---

## Bash Command Safety

Never construct bash commands that contain a newline followed by `#` inside a quoted argument. This triggers Claude Code's path-validation warning: *"Newline followed by # inside a quoted argument can hide arguments from path validation"*.

**Avoid:**
```bash
python -c "
import foo  # comment
bar()
"
```

**Use instead** — no inline comments inside quoted multi-line strings:
```bash
python -c "
import foo
bar()
"
```

Or write to a temp script file and run it, rather than embedding multi-line logic with comments directly in a quoted shell argument.
