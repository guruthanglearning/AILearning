from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from Src.Data_loader import fetch_fundamentals
from Src.MarketSentimentAnalysis import fetch_news_sentiment
from Src.Technical_Indicators import load_stock_data_computer_technical_indicator
from Src.Price_Forecast import train_price_forecasting_model
from Src.Trend_Classification import train_trend_classification_model
from Src.Real_Time_Predict import predict_prices
from Src.Clean_Symbol_Information import clean_symbol_information

app = FastAPI()

class StockRequest(BaseModel):
    symbol: str

@app.get("/")
def home():
    return {"message": "Stock Prediction API is running!"}

@app.post("/stock_analysis")
def get_stock_analysis(request: StockRequest):
    try:
        symbol = request.symbol.upper()
        
        clean_symbol_information(symbol)
        
        # Step 1: Get Fundamentals
        #fundamentals = fetch_fundamentals(symbol)

        # Step 2: Compute Technical Indicators
        technicalIdicators = load_stock_data_computer_technical_indicator(symbol)        
     
        # Step 3: Get Sentiment Analysis
        sentiment_df = fetch_news_sentiment(symbol)
        sentiment_score = sentiment_df["sentiment_score"].mean()
        

        # Step 4: Train Stock Price Forecast Model
        train_price_forecasting_model(symbol)
       

        # Step 5: Train Trend Classification Model
        trend_result = train_trend_classification_model(symbol)
  

       
        # Step 6: Predict Real-time Stock Prices
        predictions = predict_prices(symbol)        


        # Step 7: Generate Final Recommendation
        recommendation = "Buy" if predictions["trading_signal"] == "Buy" else "Sell" if predictions["trading_signal"] == "Sell" else "Hold"

        # Combine Results
        result = {
            "symbol": symbol,
            #"fundamentals": fundamentals,
            "technicalIdicators":technicalIdicators,
            "predcitions": predictions,            
            "trend_classification": trend_result,
            #"recommendation": recommendation
        }
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run API Locally
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
