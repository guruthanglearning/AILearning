# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A stock analysis pipeline combining XGBoost price forecasting, XGBoost trend classification, and FinBERT news-sentiment analysis, served via a FastAPI backend with a Streamlit front end. Educational/research project — see the disclaimers in `README.md` before treating any output as investment advice.

## Commands

Run everything from the `StockPrediction` project root (scripts use `os.getcwd()`-relative paths). Most modules do `from Src.X import ...`, which only resolves if `Src` is importable as a package — running them as `python Src/Foo.py` puts `Src/` itself on `sys.path`, not the project root, so those imports fail. Invoke them with `-m Src.<module>` instead:

```powershell
cd D:\Study\AILearning\MLProjects\StockPrediction

D:/Study/AILearning/shared_Environment/Scripts/pip.exe install -r requirements.txt

D:/Study/AILearning/shared_Environment/Scripts/python.exe -m Src.Data_loader              # fetch + cache historical/fundamental data for a symbol (no Src.* imports, but -m works too)
D:/Study/AILearning/shared_Environment/Scripts/python.exe -m Src.Technical_Indicators     # compute technical indicators from cached data
D:/Study/AILearning/shared_Environment/Scripts/python.exe -m Src.Price_Forecast           # train the XGBoost price-forecasting model
D:/Study/AILearning/shared_Environment/Scripts/python.exe -m Src.Trend_Classification     # train the XGBoost trend-classification model
D:/Study/AILearning/shared_Environment/Scripts/python.exe -m Src.Real_Time_Predict        # load-or-train models, predict on live data
D:/Study/AILearning/shared_Environment/Scripts/python.exe Src/Clean_Symbol_Information.py  # no Src.* imports, safe to run directly — wipes Data/<symbol> and Models/*/<symbol>, irreversible, confirm the symbol before running

D:/Study/AILearning/shared_Environment/Scripts/python.exe -m uvicorn Src.API:app --reload   # FastAPI server (note: actual file is Src/API.py, not Src/Api.py as older docs say)
D:/Study/AILearning/shared_Environment/Scripts/python.exe -m streamlit run Src/UI.py         # Streamlit dashboard, calls the API at 127.0.0.1:8000
```

No test suite is configured (`README.md`'s "Development Guidelines" mention unit tests as an aspiration, not something present in the repo).

## Architecture

Per-symbol data flows through `Data/<SYMBOL>/` (raw OHLCV + fundamentals) and `Data/Sentiment_Analysis/` (news sentiment history), with trained models under `Models/Price_Forecast/<SYMBOL>/` and `Models/Trend_Classification/<SYMBOL>/`. Everything is keyed by stock symbol and by day — `Data/last_run_date.txt` tracks the last processed date so `Clean_Symbol_Information.py` can be triggered once per new calendar day to force a refresh (`IsCleanRequired()` in `API.py` does a plain date comparison with no market-calendar awareness, so it also fires on weekends/holidays), rather than reusing stale same-day model/data files.

Module dependency chain (each script imports from the last rather than duplicating logic):
- `Data_loader.py` — `yfinance` for OHLCV, `finnhub` (needs `FINNHUB_API_KEY`) for fundamentals. No API key is needed for the yfinance calls.
- `Technical_Indicators.py` — imports `fetch_historical_data` from `Data_loader.py`; computes SMA/EMA/RSI/MACD/ATR/OBV via the `ta` library plus a hand-rolled `custom_zigzag()` trend-reversal detector.
- `MarketSentimentAnalysis.py` — pulls articles via NewsAPI (`NEWS_API_KEY`) and scores them with `ProsusAI/finbert` (loaded once at module import time — importing this module downloads/loads the BERT model even if you don't call the function yet).
- `Price_Forecast.py` / `Trend_Classification.py` — both consume technical-indicator CSVs plus `fetch_news_sentiment` from `MarketSentimentAnalysis.py`, and train separate XGBoost models (regression for Close/High/Low; 3-class classification for Downtrend/Stable/Uptrend) saved as JSON under `Models/`.
- `Real_Time_Predict.py` — `load_or_train_model()` loads a saved model if present, otherwise trains one on demand; this is the "lazy training" entry point the API relies on rather than requiring an explicit offline training step first.
- `API.py` — FastAPI app wiring all of the above together per request (`IsCleanRequired()` gates the daily cleanup), exposing a `/stock_analysis` endpoint that `UI.py` (Streamlit) calls over HTTP.

## Known issue

`.env` in this directory (holding `FINNHUB_API_KEY`/`NEWS_API_KEY`) was previously committed to git before being untracked and gitignored. The old commits still contain those key values in history, so both must be treated as compromised — rotate them rather than reusing, and never add new secrets to a tracked file.
