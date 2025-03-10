# Stock Prediction Project

## Overview

This project aims to develop a comprehensive stock prediction system that leverages historical data, technical indicators, and machine learning models to forecast stock prices and trends. The system includes data collection, feature engineering, model training, and a real-time prediction API.

## Project Structure

```
stock_prediction_project/
├── data/
│   ├── fundamentals/                  # Fundamental data for stocks
│   ├── technical_indicators/          # Technical indicators per stock
├── models/
│   ├── price_forecast/                # Models for price forecasting
│   ├── trend_classification/          # Models for trend classification
├── src/
│   ├── data_loader.py                 # Fetches historical and real-time stock data
│   ├── feature_engineering.py         # Computes technical indicators & custom ZigZag
│   ├── model_price_forecast.py        # Trains stock price forecasting model
│   ├── model_trend_classification.py  # Trains trend classification model
│   ├── real_time_predict.py           # Fetches live stock data for predictions
│   ├── api.py                         # FastAPI server for real-time predictions
├── notebooks/                         # Jupyter notebooks for analysis and testing
├── requirements.txt                   # Dependency list
├── Dockerfile                         # For containerization and deployment
└── README.md                          # Project documentation
```

## Features

- **Data Collection**: Retrieve historical and real-time stock data using `yfinance` and other financial APIs.
- **Feature Engineering**: Calculate technical indicators such as SMA, EMA, RSI, MACD, ATR, and implement a custom ZigZag indicator.
- **Model Training**: Develop and train machine learning models (e.g., XGBoost) for:
  - Stock price forecasting (predicting closing, high, and low prices).
  - Stock trend classification (predicting upward, downward, or stable trends).
- **Real-Time Predictions**: Serve predictions through a RESTful API built with FastAPI.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/guruthanglearning/AILearning.git
   cd stock_prediction_project
   ```

2. **Set Up a Virtual Environment**:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. **Install Dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. **Data Collection**:

   - Run `data_loader.py` to fetch and store historical stock data.
     ```bash
     python MLProjects\StockPrediction\Code\Data_loader.py
     ```

2. **Feature Engineering**:

   - Execute `feature_engineering.py` to compute and save technical indicators.
     ```bash
     python src/feature_engineering.py
     ```

3. **Model Training**:

   - Train the price forecasting model:
     ```bash
     python src/model_price_forecast.py
     ```
   - Train the trend classification model:
     ```bash
     python src/model_trend_classification.py
     ```

4. **Real-Time Predictions**:

   - Use `real_time_predict.py` to fetch live data and make predictions.
     ```bash
     python src/real_time_predict.py
     ```

5. **API Deployment**:

   - Start the FastAPI server to serve real-time predictions.
     ```bash
     uvicorn src.api:app --reload
     ```
   - Access the API documentation at `http://127.0.0.1:8000/docs`.

## Docker Deployment

1. **Build the Docker Image**:

   ```bash
   docker build -t stock_prediction_api .
   ```

2. **Run the Docker Container**:

   ```bash
   docker run -d -p 8000:8000 stock_prediction_api
   ```

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational purposes only. Use it at your own risk. The authors and all affiliates assume no responsibility for your trading results. Do not risk money which you cannot afford to lose.


https://github.dev/github/dev