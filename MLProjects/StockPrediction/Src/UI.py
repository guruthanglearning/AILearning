import streamlit as st
import requests

debug = False

# Set your FastAPI endpoint URL
if debug:
    API_URL = "http://127.0.0.1:8000/"
else:
    API_URL = "http://127.0.0.1:8000/stock_analysis"


st.title("📈 Stock Analysis Dashboard")

# Input from user
symbol = st.text_input("Enter Stock Symbol (e.g., AAPL):")

if st.button("Analyze Stock"):
    if symbol := symbol.strip().upper():
        # Call your API
        with st.spinner("Fetching data from API..."):
            if debug:
                response = requests.get(API_URL)
            else:
                response = requests.post(API_URL, json={"symbol": symbol})            

        # Check response
        if response.status_code == 200:
            if not debug:
                data = response.json()
            else:
                data = {
                    "symbol": "AAPL",
                    "fundamentals": {
                        "symbol": "AAPL",
                        "market_cap": 3591317749760,
                        "pe_ratio": 36.107933,
                        "eps": 6.3,
                        "dividend_yield": 0.44,
                        "sector": "Technology",
                        "industry": "Consumer Electronics",
                        "beta": 1.178
                    },
                    "technicalIdicators": {
                        "sma_20": 239.4605,
                        "sma_200": 226.833,
                        "ema_20": 237.6548,
                        "ema_200": 224.3449,
                        "dma_20": 231.1833,
                        "dma_50": 235.0215,
                        "dma_200": "null",
                        "rsi_7": 28.13,
                        "rsi_14": 37.74,
                        "rsi_200": 52.66,
                        "macd": -2.2532,
                        "atr": 6.6552,
                        "zigzag": 5.3,
                        "obv": 1811911600.0
                    },
                    "predcitions": {
                        "predicted_close": 232.86,
                        "predicted_high": 240.71,
                        "predicted_low": 234.69,
                        "sentiment_score": 0.48,
                        "trading_signal": "Hold"
                    },
                    "trend": {
                        "trend_classification": "Downtrend 📉",
                        "trend_strength": 0.0485
                    },
                    "recommendation": "Hold"
                } 

            st.success(f"✅ Analysis for {symbol}")

            # Display Fundamental Analysis
            st.subheader("Fundamental Analysis")
            fundamentals = data.get("fundamentals", {})                    
            st.write(f"**Symbol:** {fundamentals.get('symbol')}")
            st.write(f"**Market Cap:** {fundamentals.get('market_cap')}")   
            st.write(f"**P/E Ratio:** {fundamentals.get('pe_ratio')}")
            st.write(f"**EPS:** {fundamentals.get('eps')}")
            st.write(f"**Dividend Yield:** {fundamentals.get('dividend_yield')}")
            st.write(f"**Sector:** {fundamentals.get('sector')}")
            st.write(f"**Industry:** {fundamentals.get('industry')}")
            st.write(f"**Beta:** {fundamentals.get('beta')}")            
            #st.json(fundamentals)

            # Technical Indicators
            st.subheader("Technical Indicators")
            tech_indicators = data.get("technicalIdicators", {})
            st.write(f"**SMA 20:** {tech_indicators.get('sma_20')}")
            st.write(f"**SMA 200:** {tech_indicators.get('sma_200')}")  
            st.write(f"**EMA 20:** {tech_indicators.get('ema_20')}")
            st.write(f"**EMA 200:** {tech_indicators.get('ema_200')}")
            st.write(f"**DMA 20:** {tech_indicators.get('dma_20')}")
            st.write(f"**DMA 50:** {tech_indicators.get('dma_50')}")
            st.write(f"**DMA 200:** {tech_indicators.get('dma_200')}")
            st.write(f"**RSI 7:** {tech_indicators.get('rsi_7')}")
            st.write(f"**RSI 14:** {tech_indicators.get('rsi_14')}")
            st.write(f"**RSI 200:** {tech_indicators.get('rsi_200')}")
            st.write(f"**MACD:** {tech_indicators.get('macd')}")
            st.write(f"**ATR:** {tech_indicators.get('atr')}")
            st.write(f"**ZigZag:** {tech_indicators.get('zigzag')}")
            st.write(f"**OBV:** {tech_indicators.get('obv')}")
            #st.json(tech_indicators)
           

            # Trend Classification
            st.subheader("Trend Classification")
            trend = data["trend"]
            trend_classification =  trend.get("trend_classification", "N/A")
            trend_strength = trend.get("trend_strength", "N/A")
            st.write(f"**Trend:** {trend_classification}")
            st.write(f"**Trend Strength:** {trend_strength}")

            # Stock Price Forecast
            st.subheader("Stock Price Forecast")
            forecast = data.get("predcitions", {})
            st.write(f"**Predicted Close:** {forecast.get('predicted_close', 'N/A')}")
            st.write(f"Predicted High: {forecast.get('predicted_high', 'N/A')}")
            st.write(f"Predicted Low: {forecast.get('predicted_low', 'N/A')}")

             # Market Sentiment
            st.subheader("Market Sentiment Analysis")
            sentiment_score = forecast.get("sentiment_score", "N/A")
            st.metric("Sentiment Score", sentiment_score)

            # Final Recommendation
            st.subheader("Recommendation")
            recommendation = data.get("recommendation", "N/A")
            if recommendation == "Buy":
                st.success(f"🚀 {recommendation}")
            elif recommendation == "Sell":
                st.error("⚠️ Sell")
            else:
                st.info("🟡 Hold")
            

        else:
            st.error(f"Error fetching data: {response.status_code}")
            st.write(response.text)
    else:
        st.warning("Please enter a stock symbol.")
