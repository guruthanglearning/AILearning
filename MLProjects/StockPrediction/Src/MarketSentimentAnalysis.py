import pandas as pd 
import requests
import torch
import os
import datetime
from dotenv import load_dotenv
from transformers import BertTokenizer, BertForSequenceClassification


# Load environment variables
load_dotenv()

# Load FinBERT model
tokenizer = BertTokenizer.from_pretrained("ProsusAI/finbert")
model = BertForSequenceClassification.from_pretrained("ProsusAI/finbert")

def fetch_news_sentiment(query, page_size=10, track_history=True):
    """Fetch latest news and compute sentiment score. Optionally tracks historical sentiment."""
    try:
        newsapikey = os.getenv("NEWS_API_KEY")
        url = f"https://newsapi.org/v2/everything?q={query}&pageSize={page_size}&apiKey={newsapikey}"
        response = requests.get(url)
        articles = response.json().get("articles", [])
        
        news_data = []
        for article in articles:
            text = article["title"] + " " + (article["description"] if article["description"] else "")
            inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=512)
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            sentiment = probs[0][2].item() - probs[0][0].item()  # Positive - Negative sentiment

            news_data.append({
                "date": article["publishedAt"].split("T")[0],
                "title": article["title"],
                "sentiment_score": round(sentiment, 4)  # Normalized sentiment score
            })
        
        news_df = pd.DataFrame(news_data)
        
        if track_history:
            save_sentiment_history(query, news_df)
        
        return news_df
    except Exception as e:
        raise Exception(f"Error in MarketSentimentAnalysis-->fetch_news_sentiment {query}: {str(e)}")  

def save_sentiment_history(symbol, news_df):
    """Save historical sentiment scores for trend analysis."""
    rootPath = os.path.abspath(os.path.join(os.getcwd()))
    directory = os.path.join(rootPath, "Data", "Sentiment_Analysis")
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filepath = os.path.join(directory, f"sentiment_history_{symbol}.csv")
    
    if os.path.exists(filepath):
        existing_df = pd.read_csv(filepath)
        news_df = pd.concat([existing_df, news_df], ignore_index=True)
        news_df.drop_duplicates(subset=["title"], keep="last", inplace=True)
    
    news_df.to_csv(filepath, index=False)
    print(f"Saved sentiment history for {symbol} to {filepath}")

def get_historical_sentiment(symbol):
    """Retrieve historical sentiment scores for trend analysis."""
    rootPath = os.path.abspath(os.path.join(os.getcwd()))
    filepath = os.path.join(rootPath, "Data", "Sentiment_Analysis", f"sentiment_history_{symbol}.csv")
    
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        return df
    else:
        print(f"No historical sentiment data found for {symbol}.")
        return None

# Example usage
if __name__ == "__main__":
    news_df = fetch_news_sentiment("AAPL")
    print(news_df)
    historical_sentiment = get_historical_sentiment("AAPL")
    print(historical_sentiment)
