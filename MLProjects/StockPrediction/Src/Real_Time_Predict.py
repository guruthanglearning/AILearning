import pandas as pd
import xgboost as xgb
import os
import numpy as np
import scipy.stats as st
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import MinMaxScaler
from Src.Data_loader import fetch_real_time_data
from Src.Technical_Indicators import compute_real_time_indicators, compute_technical_indicators
from Src.MarketSentimentAnalysis import fetch_news_sentiment
from Src.Trend_Classification import train_trend_classification_model

rootPath = os.path.abspath(os.path.join(os.getcwd()))

def load_or_train_model(symbol, target_name, retrain=False):
    """Load the trained XGBoost model, or train a new one if missing or retrain=True."""
    model_path = os.path.join(rootPath, "Models", "Price_Forecast", symbol, f"Price_Forecast_{symbol}_{target_name}.json")
    
    if not os.path.exists(model_path) or retrain:
        print(f"Training new model for {symbol} - {target_name}...")
        return train_price_forecasting_model(symbol, target_name)
    
    model = xgb.XGBRegressor()
    model.load_model(model_path)
    return model

def train_price_forecasting_model(symbol, target_name):
    """Train an XGBoost regression model for Close, High, and Low price forecasting."""
    directoryPath = os.path.join(rootPath, "Data", symbol)
    filepath = os.path.join(directoryPath, f"technical_indicators_{symbol}.csv")

    if not os.path.exists(filepath):
        compute_technical_indicators(symbol)

    df = pd.read_csv(filepath, index_col='Date', parse_dates=True)
    sentiment_df = fetch_news_sentiment(symbol)
    sentiment_score = sentiment_df["sentiment_score"].mean()

    df["sentiment"] = sentiment_score
    features = df[['SMA_20', 'SMA_200', 'EMA_20', 'EMA_200',
                   'RSI_7', 'RSI_14', 'RSI_200', 'MACD', 'ATR', 'sentiment']]
    
    target = df[target_name].shift(-1)  # Predict next-day value
    valid_rows = ~target.isna()
    features = features[valid_rows]
    target = target[valid_rows]

    scaler = MinMaxScaler()
    X = scaler.fit_transform(features)
    y = target.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    confidence_interval = st.t.interval(0.95, len(y_test)-1, loc=np.mean(predictions), scale=st.sem(predictions))

    print(f"{symbol} - {target_name}:\n MSE: {mse}\n MAE: {mae}\n 95% Confidence Interval: {confidence_interval}\n")

    model_dir = os.path.join(rootPath, "Models", "Price_Forecast", symbol)
    os.makedirs(model_dir, exist_ok=True)
    model.save_model(os.path.join(model_dir, f"Price_Forecast_{symbol}_{target_name}.json"))
    
    return model

def generate_trading_signal(symbol, sentiment_score):
    """Generate Buy/Sell/Hold signal based on technical indicators and sentiment analysis."""
    trend_result = train_trend_classification_model(symbol)
    trend_strength = trend_result["trend_strength"]
    trend_classification = trend_result["trend_classification"]
    
    if sentiment_score > 0 and trend_classification == 1 and trend_strength > 0.01:
        return "Buy"
    elif sentiment_score < 0 and trend_classification == -1 and trend_strength > 0.01:
        return "Sell"
    else:
        return "Hold"

def predict_prices(symbol, retrain_models=False):
    """Predict stock prices in real-time, training models if needed."""
    try:
        df = fetch_real_time_data(symbol)
        indicators = compute_real_time_indicators(df)
        
        sentiment_df = fetch_news_sentiment(symbol)
        sentiment_score = sentiment_df["sentiment_score"].mean()
        
        indicators_df = pd.DataFrame([indicators], columns=[
            "SMA_20", "SMA_200", "EMA_20", "EMA_200", "RSI_7", "RSI_14", "RSI_200", "MACD", "ATR"
        ])
        indicators_df["Sentiment"] = sentiment_score  
        indicators_array = indicators_df.values.reshape(1, -1)

        if indicators_array.shape[1] != 10:
            raise ValueError(f"Feature shape mismatch, expected: 10, got {indicators_array.shape[1]}")

        close_model = load_or_train_model(symbol, "close", retrain=retrain_models)
        high_model = load_or_train_model(symbol, "high", retrain=retrain_models)
        low_model = load_or_train_model(symbol, "low", retrain=retrain_models)

        predicted_close = float(close_model.predict(indicators_array)[0])
        predicted_high = float(high_model.predict(indicators_array)[0])
        predicted_low = float(low_model.predict(indicators_array)[0])

        signal = generate_trading_signal(symbol, sentiment_score)
        
        return {            
            "predicted_close": round(predicted_close, 2),
            "predicted_high": round(predicted_high, 2),
            "predicted_low": round(predicted_low, 2),
            "sentiment_score": round(sentiment_score, 2),
            "trading_signal": signal
        }
      
    except Exception as e:
        raise Exception(f"Error in Real_Time_Predict-->predict_prices {symbol}: {str(e)}") 

if __name__ == "__main__":
    stock_symbol = "AAPL"
    prediction_result = predict_prices(stock_symbol, retrain_models=False)
    print(prediction_result)
