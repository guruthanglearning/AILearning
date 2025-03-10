import pandas as pd
import numpy as np
import xgboost as xgb
import os
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import MinMaxScaler
from MarketSentimentAnalysis import fetch_news_sentiment

rootPath = os.path.abspath(os.path.join(os.getcwd()))

def train_trend_classification_model(symbol):
    """Train an XGBoost classification model for predicting stock trends with trend strength score."""
    try:

        # Check for <symbol>_indicators.csv file
        filepath = os.path.join(rootPath, "Data", symbol, f"technical_indicators_{symbol}.csv")
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return

        # Load technical indicators from CSV
        df = pd.read_csv(filepath, index_col='Date', parse_dates=True)

        # Fetch sentiment and merge
        sentiment_df = fetch_news_sentiment(symbol)
        sentiment_score = sentiment_df["sentiment_score"].mean()
        df["sentiment"] = sentiment_score

        # Prepare features using technical indicators
        features = df[['SMA_20', 'SMA_200', 'EMA_20', 'EMA_200', 'RSI_7', 'RSI_14', 'RSI_200', 'MACD', 'ATR', 'sentiment']]

        # Define target variable: Trend classification
        df["trend"] = df["Close"].pct_change().shift(-1).apply(lambda x: 1 if x > 0.005 else -1 if x < -0.005 else 0)

        # Calculate trend strength score (absolute % change in Close price)
        df["trend_strength"] = df["Close"].pct_change().shift(-1).abs()
        df.dropna(subset=["trend", "trend_strength"], inplace=True)

        # Ensure valid rows
        valid_rows = ~df['trend'].isna()
        features = features[valid_rows]
        target_trend = df['trend'][valid_rows]
        trend_strength = df['trend_strength'][valid_rows]

        # Handle NaNs and infinite values in features
        features = features.fillna(0)
        features.replace([np.inf, -np.inf], 0, inplace=True)

        # Normalize features
        scaler = MinMaxScaler()
        X = scaler.fit_transform(features)

        # Map trend labels to non-negative values for classification
        y = target_trend.map({-1: 0, 0: 1, 1: 2})

        # Ensure target labels are integer values
        y = y.astype(int)

        # Split data into training and testing sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize and train the XGBoost classifier
        model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
        model.fit(X_train, y_train)

        # Predict and evaluate the model
        predictions = model.predict(X_test)
        print(f"Classification Report for {symbol}:")
        print(classification_report(y_test, predictions))
        print(f"Confusion Matrix for {symbol}:")
        print(confusion_matrix(y_test, predictions))

        # Save the trained model
        directoryPath = os.path.join(rootPath, "Models", "Trend_Classification", symbol)
        model_path = os.path.join(directoryPath, f"Trend_classification_{symbol}.json")
        if os.path.exists(model_path):
            os.remove(model_path)
        os.makedirs(directoryPath, exist_ok=True)
        model.save_model(model_path)

        print(f"Trained and saved trend classification model for {symbol}.")
        classification_labels = {-1: "Downtrend 📉", 0: "Stable ⚖️", 1: "Uptrend 📈"}
        
        # Return trend classification and strength
        return {
            "trend_classification": classification_labels[int(target_trend.iloc[-1])],
            "trend_strength": round(float(trend_strength.iloc[-1]), 4)
        }

    except Exception as e:
        raise Exception(f"Error in Trend_Classification-->train_trend_classification_model {symbol}: {str(e)}") 

# Example usage
if __name__ == "__main__":
    stock_symbols = ["AAPL"]
    for symbol in stock_symbols:
        result = train_trend_classification_model(symbol)
        print(result)
