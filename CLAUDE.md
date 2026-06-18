# AILearning — Claude Instructions

## Browser

Always open the StockRecommendationPlatform UI (and any other local web app in this workspace) in **Microsoft Edge** (`msedge`). Never use Chrome or any other browser. Edge is at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`.

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
