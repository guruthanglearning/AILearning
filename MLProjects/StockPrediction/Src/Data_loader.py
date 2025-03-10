
import yfinance as yf
import finnhub
import pandas as pd
import os
from dotenv import load_dotenv
import time

# Load environment variables from .env file
load_dotenv()

# Initialize Finnhub client with your API key
# API_KEY should be available in .env file 
client = finnhub.Client(api_key=os.getenv('FINNHUB_API_KEY'))

# Function to fetch historical stock data using yfinance
def fetch_historical_data(symbol, period="1y", interval="1d"):    
    rootPath =   os.path.abspath(os.path.join(os.getcwd()))
    directoryPath = os.path.join(rootPath, "Data",symbol)   
    filePath = os.path.join(directoryPath, f"stock_data_{symbol}.csv")           
    try:                                        
        """Fetch historical stock data for multiple symbols. """  
        
        df = yf.download(
            symbol,
            period=period,  # Time range (e.g., 1 year)
            interval=interval,  # Data interval (e.g., daily)
            auto_adjust=True,  # Adjust for dividends and splits
            group_by="column"  # Ensure flat data structure
        )

        # Reset index to flatten Date index and remove multi-index issues
        df = df.reset_index()

        # Remove 'Ticker' column if it exists to avoid redundancy
        if 'Ticker' in df.columns:
            df = df.drop(columns=['Ticker']) 

        
        if not os.path.exists(directoryPath):
            os.makedirs(directoryPath, exist_ok=True)

        # Save to CSV with the proper index label
        
        df.to_csv(filePath, index=False)
    except Exception as e:
            FileNotFoundError(f"Error saving data in Data_loader module for {symbol} to {filePath}: {e} ")

    print(f"Saved historical data for {symbol} to {filePath}")


def fetch_real_time_data(symbol):
    """Fetch the latest stock market data for real-time prediction."""
    stock = yf.Ticker(symbol)
    df = stock.history(period="1d", interval="5m")  # Fetch intraday data with 5-minute intervals

    if df.empty:
        raise ValueError(f"No real-time data available for {symbol}")
    
    # Reset index to flatten Date index and remove multi-index issues
    df = df.reset_index()

    # Remove 'Ticker' column if it exists to avoid redundancy
    if 'Ticker' in df.columns:
        df = df.drop(columns=['Ticker']) 
    
    df.rename(columns={"Datetime": "Date"}, inplace=True)
    df.set_index("Date", inplace=True)

    return df

def fetch_fundamentals(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        return {
            "symbol": symbol,
            "market_cap": info.get("marketCap"),
            "pe_ratio": info.get("trailingPE"),
            "eps": info.get("trailingEps"),
            "dividend_yield": info.get("dividendYield"),
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "beta": stock.info.get("beta")
        }
    except Exception as e:
        raise Exception(f"Error fetching fundamental data from Data_Loader for {symbol}: {str(e)}")  


# Example usage
if __name__ == "__main__":
    stock_symbols = ["AAPL"]


    # Fetch and display real-time data
    for symbol in stock_symbols:
        # Fetch and save historical data
        fetch_historical_data(symbol)
        # Add a 2-second delay between API calls to avoid rate limiting
        time.sleep(30)
        real_time_data = fetch_real_time_data(symbol)
        print(real_time_data)