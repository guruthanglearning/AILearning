# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A learning sandbox for ML experimentation, not a production app. Two independent sub-projects live under `Learning/`:

- **`Learning/StockPredictionModels/`** — Python scripts that fetch stock data via `yfinance`, engineer 19 technical-indicator features, and train/compare 6 scikit-learn models (Random Forest, Logistic/Linear Regression, SVM/SVR) for direction and price prediction. Fully implemented and runnable.
- **`Learning/MLModelTraining_NanoGPT/`** — Scaffolding only (`.gitignore` + a VS Code task referencing `NanoGpt.Dashboard/NanoGpt.Dashboard.csproj`, a planned .NET dashboard). No source files exist yet — the `.csproj` the task points to has not been created.

## Commands (StockPredictionModels)

Use the shared virtual environment for this workspace, not a local venv (see repo-root instructions). All scripts live in `Learning/StockPredictionModels/`, not the `AIModels` root:

```powershell
cd D:\Study\AILearning\MLProjects\AIModels\Learning\StockPredictionModels

D:/Study/AILearning/shared_Environment/Scripts/pip.exe install -r requirements.txt

D:/Study/AILearning/shared_Environment/Scripts/python.exe simple_stock_predictor.py   # full pipeline: fetch AAPL data, engineer features, train & compare all 6 models
D:/Study/AILearning/shared_Environment/Scripts/python.exe interactive_tester.py       # interactive menu: single-stock analysis, compare stocks, feature-importance experiment, quick demo
D:/Study/AILearning/shared_Environment/Scripts/python.exe predict_direction.py        # interactive menu: single-symbol or batch UP/DOWN prediction via majority vote across 3 freshly-trained classifiers
D:/Study/AILearning/shared_Environment/Scripts/python.exe model_tester.py             # interactive menu: validation framework using precision/recall/F1/confusion matrix + regression metrics
D:/Study/AILearning/shared_Environment/Scripts/python.exe threshold_validator.py      # interactive menu: checks results against the project's minimum-performance thresholds
D:/Study/AILearning/shared_Environment/Scripts/python.exe threshold_demo.py           # standalone explainer of how thresholds are applied (no data fetch, no simple_stock_predictor import)
```

`interactive_tester.py`, `predict_direction.py`, `model_tester.py`, and `threshold_validator.py` all block on `input()` in a `while True` menu loop when run directly — they can't be run non-interactively to just "get output and exit"; only `simple_stock_predictor.py` and `threshold_demo.py` run straight through without prompting.

There is no test suite, linter, or build step — these are standalone, directly-executed scripts.

## Architecture (StockPredictionModels)

Everything downstream depends on three classes defined in `simple_stock_predictor.py`, which every other script imports rather than duplicating:

- `StockDataCollector` — wraps `yfinance` to pull OHLCV history for a symbol/period.
- `FeatureEngine` — turns raw OHLCV into exactly 19 new columns (3 price-based, 4 moving averages + 4 price/MA ratios, 2 volatility, 2 volume, RSI, 3 Bollinger Band columns) and builds three target variables: `Direction_Up` (binary), `Next_Day_Price` (regression), `Volatility_Class` (3-class, via `pd.cut`). **`Volatility_Class` is defined but never actually trained on anywhere in the codebase** — `SimpleMLModels` only has `train_direction_models()` and `train_price_models()`; no script trains a volatility classifier despite it being created every run.
- `SimpleMLModels` — trains 6 sklearn models (3 for direction, 3 for price — see Commands above) on a chronological (non-shuffled) 80/20 split with `StandardScaler`-normalized features, since shuffling would leak future data into training for a time series.

`interactive_tester.py`, `predict_direction.py`, `model_tester.py`, and `threshold_validator.py` all build on top of these three classes rather than re-implementing data fetching or feature engineering. `model_evaluation.py` is a separate, standalone visualization layer (ROC curves, scatter plots, confusion matrices) that consumes a results dict produced by the above rather than depending on the classes directly.

Performance thresholds (direction accuracy ≥45%/55%/60% for min/good/excellent; price R² ≥0.30/0.50/0.70; MAPE ≤10%/7%/5%) are treated as the project's success criteria — `threshold_validator.py` is the source of truth for these numbers if they need to be referenced elsewhere.

## Notes

- `Learning/StockPredictionModels/README.md` is a long, aspirational writeup — it references `quick_demo.py` and `test_setup.py`, which do not exist in the current file tree. Trust the actual `.py` files listed above over the README when they disagree.
- Don't build out `MLModelTraining_NanoGPT` assuming prior work exists — only tooling config is checked in, no dashboard code.
