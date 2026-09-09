# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A hybrid log-classification system that routes log messages to one of three classifiers based on their source system, then serves classification over a FastAPI endpoint. See `README.md` for the full model-selection rationale and `Interview_Explanation.md` for an interview-style walkthrough.

## Commands

```powershell
D:/Study/AILearning/shared_Environment/Scripts/pip.exe install -r requirement.txt

D:/Study/AILearning/shared_Environment/Scripts/python.exe classify.py   # runs classify_csv() on Datasets/Logs.csv -> Datasets/Result.csv
D:/Study/AILearning/shared_Environment/Scripts/python.exe -m uvicorn server:app --reload   # FastAPI server; POST a CSV to /classify (server.py only defines `app`, it has no uvicorn.run() entry point)
```

There is no test suite or linter configured. `Training/Training.ipynb` is the notebook used to retrain the BERT-embeddings + Logistic Regression model that gets saved to `Model/log_classifier_model.joblib`.

## Architecture

Classification is a **source-based routing decision**, not a model ensemble — each log goes to exactly one classifier, chosen in `classify_logs()` in `classify.py`:

1. `source == "LegacyCRM"` → `processor_llm.classify_with_LLM()` (Groq API, `llama-3.3-70b-versatile`). Legacy logs are unstructured/business-specific, so they always skip straight to the LLM.
2. Everything else tries `processor_regex.classify_with_regex()` first (8 hardcoded patterns for logins, backups, uploads, account creation, etc.) — this is the fast path for the ~5 "modern" source systems (ModernCRM, BillingSystem, AnalyticsEngine, ModernHR, ThirdPartyAPI).
3. If regex returns `None` (no pattern matched), it falls back to `processor_bert.classify_with_BERT()`: embeds the message with `all-MiniLM-L6-v2` (Sentence-BERT) and runs the saved Logistic Regression classifier; predictions with max probability < 0.5 are returned as `"Unknown"`.

`classify.py` re-declares `classify_with_regex` locally rather than importing the one from `processor_regex.py` — if you edit the regex patterns, check both places or you'll only change one code path (the imported one is currently unused, dead-code-shadowed by the local definition).

Batch entry points (`classify_csv`, `classify`, and the FastAPI `/classify` route in `server.py`) all expect a `sources` + `log_message` column pair and funnel through `classify_logs()` per row — there's no batching optimization (e.g. no batched BERT embedding call).

`processor_bert.py` and `processor_llm.py` load their models/clients at import time (`SentenceTransformer(...)`, `joblib.load(...)`, `Groq()`), so importing `classify.py` triggers a BERT model load and Groq client init even if you only need the regex path.

`GROQ_API_KEY` is required in `.env` for `processor_llm.py` (loaded via `python-dotenv`).

## Known issue

`.env` in this directory (holding a real `GROQ_API_KEY`) was previously committed to git before being untracked and gitignored. The old commits still contain that key value in history, so it must be treated as compromised — rotate the Groq key rather than reusing it, and never add new secrets to a tracked file.
