#!/usr/bin/env python3
"""
Stock Direction Predictor
========================

This script makes actual UP/DOWN predictions for tomorrow's stock movement.
"""

from simple_stock_predictor import StockDataCollector, FeatureEngine, SimpleMLModels
import numpy as np

def predict_stock_direction(symbol='AAPL', period='1y'):
    """
    Predict if a stock will go UP or DOWN tomorrow
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL', 'TSLA', 'PLTR')
        period (str): Historical data period for training
    
    Returns:
        dict: Prediction results with confidence levels
    """
    print(f"🔮 Predicting direction for {symbol}")
    print("=" * 50)
    
    # Step 1: Get and prepare data
    collector = StockDataCollector()
    raw_data = collector.fetch_data(symbol, period)
    
    if raw_data is None:
        return None
    
    # Create features and targets
    feature_data = FeatureEngine.create_technical_features(raw_data)
    final_data = FeatureEngine.create_target_variables(feature_data)
    
    # Step 2: Train models
    ml_models = SimpleMLModels()
    X_train, X_test, y_train, y_test, features = ml_models.prepare_data(final_data, 'Direction_Up')
    
    # Train the best performing models
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    
    models = {
        'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
        'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
        'SVM': SVC(random_state=42, probability=True)
    }
    
    predictions = {}
    
    print(f"\n🤖 Training models and making predictions...")
    
    for name, model in models.items():
        # Train model
        model.fit(X_train, y_train)
        
        # Get the most recent data point (today's features)
        latest_features = X_test[-1:] if len(X_test) > 0 else X_train[-1:]
        
        # Make prediction for tomorrow
        prediction = model.predict(latest_features)[0]
        
        # Get probability/confidence if available
        if hasattr(model, 'predict_proba'):
            probabilities = model.predict_proba(latest_features)[0]
            confidence = max(probabilities)  # Highest probability
            up_prob = probabilities[1] if len(probabilities) > 1 else probabilities[0]
        else:
            confidence = 0.5  # No probability available
            up_prob = 0.5
        
        direction = "📈 UP" if prediction == 1 else "📉 DOWN"
        
        predictions[name] = {
            'prediction': prediction,
            'direction': direction,
            'confidence': confidence,
            'up_probability': up_prob
        }
        
        print(f"   {name:20} → {direction} (Confidence: {confidence:.1%})")
    
    # Step 3: Ensemble prediction (majority vote)
    votes = [pred['prediction'] for pred in predictions.values()]
    majority_vote = 1 if sum(votes) > len(votes) / 2 else 0
    ensemble_direction = "📈 UP" if majority_vote == 1 else "📉 DOWN"
    
    # Calculate average confidence
    avg_confidence = np.mean([pred['confidence'] for pred in predictions.values()])
    
    print(f"\n🎯 ENSEMBLE PREDICTION:")
    print("=" * 30)
    print(f"📊 Tomorrow's Direction: {ensemble_direction}")
    print(f"🎲 Average Confidence: {avg_confidence:.1%}")
    print(f"🗳️  Model Votes: {sum(votes)}/{len(votes)} models predict UP")
    
    # Current price context
    current_price = raw_data['Close'].iloc[-1]
    print(f"\n💰 Current {symbol} Price: ${current_price:.2f}")
    
    return {
        'symbol': symbol,
        'ensemble_direction': ensemble_direction,
        'ensemble_prediction': majority_vote,
        'confidence': avg_confidence,
        'current_price': current_price,
        'individual_predictions': predictions,
        'votes': votes
    }

def batch_predict_multiple_stocks(symbols=['AAPL', 'GOOGL', 'TSLA', 'MSFT']):
    """Predict direction for multiple stocks"""
    print("🔮 BATCH STOCK DIRECTION PREDICTIONS")
    print("=" * 60)
    
    results = {}
    
    for symbol in symbols:
        print(f"\n" + "─" * 60)
        try:
            result = predict_stock_direction(symbol, '6mo')
            if result:
                results[symbol] = result
        except Exception as e:
            print(f"❌ Error predicting {symbol}: {e}")
    
    # Summary table
    print(f"\n📊 PREDICTION SUMMARY")
    print("=" * 60)
    print(f"{'Stock':<8} | {'Prediction':<12} | {'Confidence':<12} | {'Current Price':<15}")
    print("-" * 60)
    
    for symbol, result in results.items():
        direction_str = "UP ⬆️" if result['ensemble_prediction'] == 1 else "DOWN ⬇️"
        print(f"{symbol:<8} | {direction_str:<12} | {result['confidence']:<11.1%} | ${result['current_price']:<14.2f}")
    
    return results

def main():
    """Interactive prediction interface"""
    print("🔮 Stock Direction Predictor")
    print("=" * 40)
    
    while True:
        print(f"\n📚 Options:")
        print("1. 🎯 Predict single stock direction")
        print("2. 📊 Batch predict multiple stocks")
        print("3. 🚪 Exit")
        
        choice = input(f"\n👉 Choose option (1-3): ").strip()
        
        if choice == '1':
            symbol = input("📊 Enter stock symbol: ").strip().upper() or 'AAPL'
            result = predict_stock_direction(symbol)
            
            if result:
                print(f"\n🎉 Prediction complete for {symbol}!")
                
        elif choice == '2':
            symbols_input = input("📊 Enter symbols (comma-separated) or press Enter for default: ").strip()
            if symbols_input:
                symbols = [s.strip().upper() for s in symbols_input.split(',')]
            else:
                symbols = ['AAPL', 'GOOGL', 'TSLA', 'MSFT']
            
            batch_predict_multiple_stocks(symbols)
            
        elif choice == '3':
            print("👋 Happy trading! Remember: These are predictions, not financial advice!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-3.")

if __name__ == "__main__":
    main()
