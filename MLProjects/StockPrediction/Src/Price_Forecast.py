import pandas as pd
import xgboost as xgb
import os
import numpy as np
import scipy.stats as st
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sklearn.preprocessing import MinMaxScaler
from Src.Technical_Indicators import compute_technical_indicators
from Src.MarketSentimentAnalysis import fetch_news_sentiment


# Function to train the XGBoost regression model for stock price forecasting
def train_price_forecasting_model(symbol):
    """Train an XGBoost regression model to forecast Close, High, and Low prices."""
    try:
        # Load technical indicator data
        rootPath = os.path.abspath(os.path.join(os.getcwd()))
        directoryPath = os.path.join(rootPath, "Data", symbol)
        filepath = os.path.join(directoryPath, f"technical_indicators_{symbol}.csv")

        if not os.path.exists(filepath):
            compute_technical_indicators(symbol)

        df = pd.read_csv(filepath, index_col='Date', parse_dates=True)

        # Fetch sentiment and merge with stock data
        sentiment_df = fetch_news_sentiment(symbol)
        sentiment_score = sentiment_df["sentiment_score"].mean()  # Average sentiment score

        # Add sentiment as a feature
        df["sentiment"] = sentiment_score    

        # Prepare features using technical indicators
        features = df[['SMA_20', 'SMA_200', 'EMA_20', 'EMA_200',
                    'RSI_7', 'RSI_14', 'RSI_200', 'MACD', 'ATR', 'sentiment']]

        # Define target variables: Predict next day's Close, High, and Low prices
        target_close = df['Close'].shift(-1)  # Predict next day's close price
        target_high = df['High'].shift(-1)    # Predict next day's high price
        target_low = df['Low'].shift(-1)      # Predict next day's low price

        # Remove rows with missing values
        valid_rows = ~target_close.isna()
        features = features[valid_rows]
        target_close = target_close[valid_rows]
        target_high = target_high[valid_rows]
        target_low = target_low[valid_rows]

        # Check for NaN or infinite values and handle them
        features = features.fillna(0)
        features.replace([np.inf, -np.inf], 0, inplace=True)

        # Normalize the features for better model performance
        scaler = MinMaxScaler()
        X = scaler.fit_transform(features)

        # Function to train and evaluate model for a single target
        def train_single_target(y, target_name):
            # Split data into training and testing sets (80% train, 20% test)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            # Initialize and train the XGBoost regressor
            model = xgb.XGBRegressor(
                n_estimators=100,
                learning_rate=0.05,
                max_depth=5,
                random_state=42
            )
            model.fit(X_train, y_train)

            # Evaluate the model using Mean Squared Error (MSE) and Confidence Interval
            predictions = model.predict(X_test)
            mse = mean_squared_error(y_test, predictions)
            mae = mean_absolute_error(y_test, predictions)
            confidence_interval = st.t.interval(0.95, len(y_test)-1, loc=np.mean(predictions), scale=st.sem(predictions))
            
            print(f"{symbol} - {target_name}:\n MSE: {mse}\n MAE: {mae}\n 95% Confidence Interval: {confidence_interval}\n")

            # Save the model
            model_dir = os.path.join(rootPath, "Models", "Price_Forecast", symbol)
            
            if not os.path.exists(model_dir):
                os.makedirs(model_dir)

            filepath = os.path.join(model_dir, f"Price_Forecast_{symbol}_{target_name}.json")        
            model.save_model(filepath)

            return model

        # Train models for each target (Close, High, Low)
        close_model = train_single_target(target_close, "close")
        high_model = train_single_target(target_high, "high")
        low_model = train_single_target(target_low, "low")

        print(f"Trained and saved XGBoost regression models for {symbol}.")
    except Exception as e:
        raise Exception(f"Error in Price_Forecast-->train_price_forecasting_model {symbol}: {str(e)}") 

# Example usage for multiple stock symbols
if __name__ == "__main__":
    stock_symbols = ["AAPL"]  # Add more symbols as needed
    for symbol in stock_symbols:
        train_price_forecasting_model(symbol)
