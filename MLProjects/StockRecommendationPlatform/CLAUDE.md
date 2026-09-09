# StockRecommendationPlatform — Claude Instructions

## Pull Request & Code Review Workflow

Follows the workspace-wide policy in the root `D:\Study\AILearning\CLAUDE.md` (Pull Request & Code Review Workflow section): every change — code or documentation (`*.md`) — goes to a feature branch, opens a PR, gets reviewed by the Codex CLI (`codex exec`, non-interactive), has every finding addressed with a reply on its comment thread, gets re-reviewed, and only then merges. Do not push directly to `main`. See PRs #1–#5 on this repo for the established pattern (model additions, cost-comparison feature, saved-report lookups, the Interview_Explanation.md doc).

## CI/CD Policy

After every `git push`, always validate CI/CD without being asked:

1. Run `gh run list --limit 3 --repo guruthanglearning/AILearning` to get the latest run ID
2. Run `gh run watch <run-id> --repo guruthanglearning/AILearning` and wait for it to complete
3. If it **passes**: report "CI passed" and the run duration
4. If it **fails**: fetch the failed step logs with `gh run view <run-id> --repo guruthanglearning/AILearning --log-failed`, identify the root cause, fix it, commit, and push again
