"""
Interactive Model Testing and Experimentation
==========================================

This script allows you to interactively test different stocks, 
parameters, and model configurations for learning purposes.
"""

from simple_stock_predictor import StockDataCollector, FeatureEngine, SimpleMLModels
from model_evaluation import create_evaluation_report
import pandas as pd
import numpy as np

class InteractiveModelTester:
    """Interactive interface for testing models with different configurations"""
    
    def __init__(self):
        self.collector = StockDataCollector()
        self.models = SimpleMLModels()
        self.current_data = None
        self.current_symbol = None
        
    def run_experiment(self, symbol='AAPL', period='2y', show_plots=True):
        """
        Run a complete experiment with specified parameters
        
        Args:
            symbol (str): Stock symbol to analyze
            period (str): Time period for data
            show_plots (bool): Whether to show evaluation plots
        """
        print(f"\n🧪 Starting Experiment: {symbol}")
        print("=" * 50)
        
        # Step 1: Collect data
        print("📊 Step 1: Data Collection")
        raw_data = self.collector.fetch_data(symbol, period)
        
        if raw_data is None:
            print(f"❌ Failed to get data for {symbol}")
            return None
        
        self.current_symbol = symbol
        
        # Step 2: Feature engineering
        print("\n🔧 Step 2: Feature Engineering")
        feature_data = FeatureEngine.create_technical_features(raw_data)
        self.current_data = FeatureEngine.create_target_variables(feature_data)
        
        # Step 3: Model training
        print("\n🤖 Step 3: Model Training")
        
        # Train both types of models
        direction_results = self.models.train_direction_models(self.current_data)
        price_results = self.models.train_price_models(self.current_data)
        
        # Combine results
        all_results = {
            'direction': direction_results,
            'price': price_results
        }
        
        # Step 4: Evaluation
        if show_plots:
            print("\n📈 Step 4: Model Evaluation")
            create_evaluation_report(all_results)
        
        return all_results
    
    def compare_stocks(self, symbols=['AAPL', 'GOOGL', 'MSFT', 'TSLA'], period='1y'):
        """
        Compare model performance across different stocks
        
        Args:
            symbols (list): List of stock symbols to compare
            period (str): Time period for analysis
        """
        print(f"\n🏁 Stock Comparison Experiment")
        print("=" * 50)
        
        comparison_results = {}
        
        for symbol in symbols:
            print(f"\n📊 Testing {symbol}...")
            try:
                results = self.run_experiment(symbol, period, show_plots=False)
                if results:
                    comparison_results[symbol] = results
            except Exception as e:
                print(f"❌ Error with {symbol}: {e}")
                continue
        
        # Create comparison summary
        self._create_comparison_summary(comparison_results)
        
        return comparison_results
    
    def _create_comparison_summary(self, results):
        """Create summary comparison table"""
        if not results:
            print("❌ No results to compare")
            return
        
        print(f"\n📊 STOCK COMPARISON SUMMARY")
        print("=" * 70)
        
        # Direction prediction comparison
        print(f"\n🎯 Direction Prediction Accuracy:")
        print(f"{'Stock':<8} | {'Random Forest':<12} | {'Logistic Reg':<12} | {'SVM':<12}")
        print("-" * 60)
        
        for stock, result in results.items():
            if 'direction' in result:
                rf_acc = result['direction'].get('Random Forest', {}).get('accuracy', 0)
                lr_acc = result['direction'].get('Logistic Regression', {}).get('accuracy', 0)
                svm_acc = result['direction'].get('SVM', {}).get('accuracy', 0)
                
                print(f"{stock:<8} | {rf_acc:<12.4f} | {lr_acc:<12.4f} | {svm_acc:<12.4f}")
        
        # Price prediction comparison
        print(f"\n💰 Price Prediction R² Score:")
        print(f"{'Stock':<8} | {'Random Forest':<12} | {'Linear Reg':<12} | {'SVR':<12}")
        print("-" * 60)
        
        for stock, result in results.items():
            if 'price' in result:
                rf_r2 = result['price'].get('Random Forest', {}).get('r2', 0)
                lr_r2 = result['price'].get('Linear Regression', {}).get('r2', 0)
                svr_r2 = result['price'].get('SVR', {}).get('r2', 0)
                
                print(f"{stock:<8} | {rf_r2:<12.4f} | {lr_r2:<12.4f} | {svr_r2:<12.4f}")
    
    def experiment_with_features(self, symbol='AAPL', period='1y'):
        """
        Experiment with different feature combinations
        """
        print(f"\n🔬 Feature Importance Experiment: {symbol}")
        print("=" * 50)
        
        # Get base data
        raw_data = self.collector.fetch_data(symbol, period)
        if raw_data is None:
            return
        
        feature_data = FeatureEngine.create_technical_features(raw_data)
        final_data = FeatureEngine.create_target_variables(feature_data)
        
        # Test different feature groups
        feature_groups = {
            'Price Features': ['Price_Change', 'High_Low_Pct', 'Open_Close_Pct'],
            'Moving Averages': ['MA_5', 'MA_10', 'MA_20', 'MA_50', 'Price_MA_5_Ratio', 'Price_MA_20_Ratio'],
            'Technical Indicators': ['RSI', 'BB_Position', 'Volatility_5', 'Volatility_20'],
            'Volume Features': ['Volume_MA_10', 'Volume_Ratio']
        }
        
        print(f"\n🧪 Testing Feature Groups:")
        
        for group_name, features in feature_groups.items():
            print(f"\n📊 Testing {group_name}...")
            
            # Prepare data with only these features
            try:
                X_train, X_test, y_train, y_test, _ = self.models.prepare_data(
                    final_data, 'Direction_Up', features
                )
                
                # Train a simple Random Forest
                from sklearn.ensemble import RandomForestClassifier
                from sklearn.metrics import accuracy_score
                
                model = RandomForestClassifier(n_estimators=50, random_state=42)
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)
                
                print(f"   ✅ Accuracy with {group_name}: {accuracy:.4f}")
                print(f"   📊 Features: {features}")
                
            except Exception as e:
                print(f"   ❌ Error with {group_name}: {e}")

def run_learning_session():
    """Run an interactive learning session"""
    print("🎓 Welcome to Interactive Stock Prediction Learning!")
    print("=" * 60)
    
    tester = InteractiveModelTester()
    
    while True:
        print(f"\n📚 Learning Options:")
        print("1. 🔍 Single Stock Analysis")
        print("2. 🏁 Compare Multiple Stocks") 
        print("3. 🧪 Feature Importance Experiment")
        print("4. 💡 Quick Demo (AAPL)")
        print("5. 🚪 Exit")
        
        try:
            choice = input(f"\n👉 Choose an option (1-5): ").strip()
            
            if choice == '1':
                symbol = input("📊 Enter stock symbol (e.g., AAPL): ").strip().upper()
                period = input("📅 Enter period (1y, 2y, 5y): ").strip() or '1y'
                
                print(f"\n🚀 Analyzing {symbol} for {period}...")
                tester.run_experiment(symbol, period)
                
            elif choice == '2':
                symbols_input = input("📊 Enter stock symbols (comma-separated, e.g., AAPL,MSFT,GOOGL): ").strip()
                if symbols_input:
                    symbols = [s.strip().upper() for s in symbols_input.split(',')]
                else:
                    symbols = ['AAPL', 'MSFT', 'GOOGL', 'TSLA']  # Default
                
                period = input("📅 Enter period (1y, 2y): ").strip() or '1y'
                
                print(f"\n🏁 Comparing {len(symbols)} stocks...")
                tester.compare_stocks(symbols, period)
                
            elif choice == '3':
                symbol = input("📊 Enter stock symbol for feature experiment: ").strip().upper() or 'AAPL'
                
                print(f"\n🔬 Running feature importance experiment...")
                tester.experiment_with_features(symbol)
                
            elif choice == '4':
                print(f"\n💡 Running quick demo with AAPL...")
                tester.run_experiment('AAPL', '1y')
                
            elif choice == '5':
                print(f"\n👋 Thanks for learning! Keep experimenting!")
                break
                
            else:
                print(f"❌ Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print(f"\n\n👋 Learning session ended. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Let's try again...")

if __name__ == "__main__":
    # Run interactive learning session
    run_learning_session()
