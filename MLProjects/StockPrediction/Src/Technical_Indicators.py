import pandas as pd
import numpy as np
import ta  # Technical Analysis library for indicators
import os
from Src.Data_loader import fetch_historical_data

# Custom ZigZag implementation
def custom_zigzag(prices, threshold=0.05):
    """Custom ZigZag indicator that identifies significant price reversals."""
    trend = np.zeros(len(prices))
    last_pivot = prices[0]

    for i in range(1, len(prices)):
        change = (prices[i] - last_pivot) / last_pivot
        if abs(change) >= threshold:  # Significant movement detected
            trend[i] = prices[i]
            last_pivot = prices[i]
        else:
            trend[i] = np.nan  # Minor fluctuations ignored
    return pd.Series(trend)

def compute_real_time_indicators(df):
    """Compute technical indicators for real-time prediction."""
    return compute_technical_indicators(df).iloc[-1].to_dict()

# Function to compute technical indicators
def compute_technical_indicators(df):

    try:
        # Calculate Simple Moving Averages (SMA)
        df['SMA_20'] = ta.trend.sma_indicator(df['Close'], window=20)
        df['SMA_200'] = ta.trend.sma_indicator(df['Close'], window=200)

        # Calculate Exponential Moving Averages (EMA)
        df['EMA_20'] = ta.trend.ema_indicator(df['Close'], window=20)
        df['EMA_200'] = ta.trend.ema_indicator(df['Close'], window=200)

        # Calculate Relative Strength Index (RSI)
        df['RSI_7'] = ta.momentum.rsi(df['Close'], window=7)
        df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
        df['RSI_200'] = ta.momentum.rsi(df['Close'], window=200)

        # Calculate MACD (Moving Average Convergence Divergence)
        df['MACD'] = ta.trend.macd(df['Close'], window_slow=13, window_fast=6)

        # Calculate Average True Range (ATR)
        df['ATR'] = ta.volatility.average_true_range(df['High'], df['Low'], df['Close'], window=14)

        # Apply Custom ZigZag Trend Detection
        df['ZigZag'] = custom_zigzag(df['Close'].values, threshold=0.05)
        
        # Calculate DMA for 20, 50 & 200 days
        df["DMA_20"] = df["Close"].shift(20).rolling(window=20).mean()
        df["DMA_50"] = df["Close"].shift(50).rolling(window=50).mean()
        df["DMA_200"] = df["Close"].shift(200).rolling(window=200).mean()
        
        # Calculate On Balance Value
        df["OBV"] = ta.volume.on_balance_volume(df["Close"], df["Volume"])
        
        return df
    except Exception as e:
        raise Exception(f"Error in Technical_Indicators-->compute_technical_indicators {symbol}: {str(e)}")  
  
def load_stock_data_computer_technical_indicator(symbol):
    """Calculates technical indicators for the stock."""
    
    try:
        rootPath = os.path.abspath(os.path.join(os.getcwd()))
        directoryPath = os.path.join(rootPath, "Data",symbol)
        filepath =  os.path.join(directoryPath,f"stock_data_{symbol}.csv")
        output_path =  os.path.join(directoryPath,f"technical_indicators_{symbol}.csv")    
        
        if not os.path.exists(filepath):
            fetch_historical_data(symbol)

        df = pd.read_csv(filepath,skiprows=[1])

        # Ensure 'Date' column is datetime type and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)

        df = compute_technical_indicators(df)
        
        # Save processed data with technical indicators
        
        df.to_csv(output_path)       
        print(f"Technical indicators for {symbol} saved to {output_path}")
        return {    
            "sma_20": round(float(df['SMA_20'].iloc[-1]), 4),
            "sma_200": round(float(df['SMA_200'].iloc[-1]), 4),
            "ema_20": round(float(df['EMA_20'].iloc[-1]), 4),
            "ema_200": round(float(df['EMA_200'].iloc[-1]), 4),
            "dma_20": round(float(df['DMA_20'].iloc[-1]), 4) if not np.isnan(df['DMA_20'].iloc[-1]) else None,
            "dma_50": round(float(df['DMA_50'].iloc[-1]), 4) if not np.isnan(df['DMA_50'].iloc[-1]) else None,
            "dma_200": round(float(df['DMA_200'].iloc[-1]), 4) if not np.isnan(df['DMA_200'].iloc[-1]) else None,
            "rsi_7": round(float(df['RSI_7'].iloc[-1]), 2),
            "rsi_14": round(float(df['RSI_14'].iloc[-1]), 2),
            "rsi_200": round(float(df['RSI_200'].iloc[-1]), 2),
            "macd": round(float(df['MACD'].iloc[-1]), 4),
            "atr": round(float(df['ATR'].iloc[-1]), 4),
            "zigzag": round(float(df['ZigZag'].dropna().iloc[-1]), 4) if not df['ZigZag'].dropna().empty else None,
            "obv": round(float(df['OBV'].iloc[-1]), 2)
        }
    except Exception as e:
        raise Exception(f"Error in Technical_Indicators-->load_stock_data_computer_technical_indicator {symbol}: {str(e)}")  
    

# Example usage
if __name__ == "__main__":
    stock_symbols = ["AAPL"]  # Add more symbols as needed
    for symbol in stock_symbols:

        load_stock_data_computer_technical_indicator(symbol)
                
        rootPath = os.path.abspath(os.path.join(os.getcwd()))
        directoryPath = os.path.join(rootPath, "Data",symbol)

        filepath =  os.path.join(directoryPath,f"stock_data_{symbol}.csv")
        if not os.path.exists(filepath):
            fetch_historical_data(symbol)

        df = pd.read_csv(filepath,skiprows=[1])

        # Ensure 'Date' column is datetime type and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df = compute_real_time_indicators(df)
        print(df)

