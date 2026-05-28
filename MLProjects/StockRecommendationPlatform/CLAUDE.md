# StockRecommendationPlatform — Claude Instructions

## CI/CD Policy

After every `git push`, always validate CI/CD without being asked:

1. Run `gh run list --limit 3 --repo guruthanglearning/AILearning` to get the latest run ID
2. Run `gh run watch <run-id> --repo guruthanglearning/AILearning` and wait for it to complete
3. If it **passes**: report "CI passed" and the run duration
4. If it **fails**: fetch the failed step logs with `gh run view <run-id> --repo guruthanglearning/AILearning --log-failed`, identify the root cause, fix it, commit, and push again
