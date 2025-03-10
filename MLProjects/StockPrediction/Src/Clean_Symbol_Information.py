import os
import shutil

def clean_symbol_information(symbol):
    try:
        rootPath =   os.path.abspath(os.path.join(os.getcwd()))
        
        # Remove  data directory
        directory = os.path.join(rootPath, "Data",symbol)
        if os.path.exists(directory):
            shutil.rmtree(directory)
        
        # Remove  Price Forecast directory
        directory = os.path.join(rootPath, "Models","Price_Forecast",symbol)
        if os.path.exists(directory):
            shutil.rmtree(directory)

        # Remove Trend Classification directory
        directory = os.path.join(rootPath, "Models","Trend_Classification",symbol)
        if os.path.exists(directory):
            shutil.rmtree(directory)

        # Remove Sentiment_Analysis  directory
        directory = os.path.join(rootPath, "Data","Sentiment_Analysis",symbol)
        if os.path.exists(directory):
            shutil.rmtree(directory)

    except Exception as e:
        raise e
        
# Example usage
if __name__ == "__main__":
    clean_symbol_information("AAPL")