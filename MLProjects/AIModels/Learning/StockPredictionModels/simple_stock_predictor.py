"""
Simple Stock Prediction Learning Project
=====================================

This project demonstrates fundamental machine learning concepts using stock market data.
Perfect for learning ML basics with practical, real-world applications.

Models Included:
1. Direction Predictor - Binary classification (Up/Down)
2. Price Predictor - Regression (Actual price prediction)
3. Volatility Predictor - Classification (Low/Medium/High volatility)

Learning Goals:
- Feature engineering with financial data
- Model selection and comparison
- Cross-validation and evaluation metrics
- Overfitting detection and prevention
- Model interpretability
"""

import pandas as pd
import numpy as np
import yfinance as yf
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.metrics import accuracy_score, classification_report, mean_squared_error, r2_score
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

class StockDataCollector:
    """Handles stock data collection and basic preprocessing"""
    
    def __init__(self):
        self.data = None
        self.symbol = None
    
    def fetch_data(self, symbol, period='2y'):
        """
        Fetch stock data using yfinance
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
            period (str): Time period ('1y', '2y', '5y', 'max')
        """
        print(f"📊 Fetching data for {symbol}...")
        
        try:
            stock = yf.Ticker(symbol)
            self.data = stock.history(period=period)
            self.symbol = symbol
            
            if self.data.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            print(f"✅ Successfully fetched {len(self.data)} days of data")
            print(f"📅 Date range: {self.data.index[0].date()} to {self.data.index[-1].date()}")
            
            return self.data
            
        except Exception as e:
            print(f"❌ Error fetching data: {e}")
            return None
    
    def get_basic_info(self):
        """Display basic information about the dataset"""
        if self.data is None:
            print("❌ No data available. Please fetch data first.")
            return
        
        print(f"\n📊 Basic Info for {self.symbol}:")
        print(f"Shape: {self.data.shape}")
        print(f"Columns: {list(self.data.columns)}")
        print(f"Date range: {self.data.index[0].date()} to {self.data.index[-1].date()}")
        print(f"Missing values: {self.data.isnull().sum().sum()}")
        
        # Display recent data
        print("\n📈 Recent data (last 5 days):")
        print(self.data.tail())

class FeatureEngine:
    """Creates technical indicators and features for ML models"""
    
    @staticmethod
    def create_technical_features(df):
        """
        Create technical analysis features
        
        Args:
            df (DataFrame): Stock price data with OHLCV columns
            
        Returns:
            DataFrame: Data with technical features added
        """
        print("🔧 Creating technical features...")
        
        # Make a copy to avoid modifying original data
        data = df.copy()
        
        # Price-based features
        data['Price_Change'] = data['Close'].pct_change()
        data['High_Low_Pct'] = (data['High'] - data['Low']) / data['Close']
        data['Open_Close_Pct'] = (data['Close'] - data['Open']) / data['Open']
        
        # Moving averages
        for window in [5, 10, 20, 50]:
            data[f'MA_{window}'] = data['Close'].rolling(window).mean()
            data[f'Price_MA_{window}_Ratio'] = data['Close'] / data[f'MA_{window}']
        
        # Volatility features
        data['Volatility_5'] = data['Price_Change'].rolling(5).std()
        data['Volatility_20'] = data['Price_Change'].rolling(20).std()
        
        # Volume features
        data['Volume_MA_10'] = data['Volume'].rolling(10).mean()
        data['Volume_Ratio'] = data['Volume'] / data['Volume_MA_10']
        
        # RSI (Relative Strength Index)
        data['RSI'] = FeatureEngine._calculate_rsi(data['Close'])
        
        # Bollinger Bands
        data['BB_Upper'], data['BB_Lower'] = FeatureEngine._calculate_bollinger_bands(data['Close'])
        data['BB_Position'] = (data['Close'] - data['BB_Lower']) / (data['BB_Upper'] - data['BB_Lower'])
        
        print(f"✅ Created {len(data.columns) - len(df.columns)} new features")
        return data
    
    @staticmethod
    def _calculate_rsi(prices, window=14):
        """Calculate RSI indicator"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def _calculate_bollinger_bands(prices, window=20, num_std=2):
        """Calculate Bollinger Bands"""
        ma = prices.rolling(window).mean()
        std = prices.rolling(window).std()
        upper = ma + (std * num_std)
        lower = ma - (std * num_std)
        return upper, lower
    
    @staticmethod
    def create_target_variables(df):
        """
        Create target variables for different prediction tasks
        
        Args:
            df (DataFrame): Stock data with features
            
        Returns:
            DataFrame: Data with target variables
        """
        print("🎯 Creating target variables...")
        
        data = df.copy()
        
        # 1. Direction prediction (Binary classification)
        # Will the stock go up tomorrow?
        data['Next_Day_Return'] = data['Close'].shift(-1) / data['Close'] - 1
        data['Direction_Up'] = (data['Next_Day_Return'] > 0).astype(int)
        
        # 2. Price prediction (Regression)
        # What will be tomorrow's closing price?
        data['Next_Day_Price'] = data['Close'].shift(-1)
        
        # 3. Volatility prediction (Multi-class classification)
        # Will tomorrow be low/medium/high volatility?
        data['Next_Day_Volatility'] = data['Volatility_20'].shift(-1)
        data['Volatility_Class'] = pd.cut(
            data['Next_Day_Volatility'], 
            bins=3, 
            labels=['Low', 'Medium', 'High']
        )
        
        print("✅ Created target variables:")
        print(f"   - Direction_Up: {data['Direction_Up'].value_counts().to_dict()}")
        print(f"   - Next_Day_Price: Range ${data['Next_Day_Price'].min():.2f} - ${data['Next_Day_Price'].max():.2f}")
        print(f"   - Volatility_Class: {data['Volatility_Class'].value_counts().to_dict()}")
        
        return data

class SimpleMLModels:
    """Collection of simple ML models for learning purposes"""
    
    def __init__(self):
        self.models = {}
        self.results = {}
        self.scaler = StandardScaler()
    
    def prepare_data(self, df, target_column, feature_columns=None):
        """
        Prepare data for machine learning
        
        Args:
            df (DataFrame): Dataset with features and targets
            target_column (str): Name of target column
            feature_columns (list): List of feature columns to use
            
        Returns:
            tuple: X_train, X_test, y_train, y_test
        """
        print(f"🎯 Preparing data for {target_column} prediction...")
        
        # Remove rows with NaN values
        clean_data = df.dropna()
        
        # Select features
        if feature_columns is None:
            # Use all numeric columns except targets and price columns
            exclude_cols = ['Next_Day_Return', 'Direction_Up', 'Next_Day_Price', 
                           'Next_Day_Volatility', 'Volatility_Class', 'Open', 'High', 'Low', 'Close']
            feature_columns = [col for col in clean_data.select_dtypes(include=[np.number]).columns 
                             if col not in exclude_cols]
        
        print(f"📊 Using {len(feature_columns)} features: {feature_columns[:5]}...")
        
        X = clean_data[feature_columns]
        y = clean_data[target_column]
          # Remove any remaining NaN values
        mask = ~(X.isnull().any(axis=1) | y.isnull())
        X = X[mask].reset_index(drop=True)
        y = y[mask].reset_index(drop=True)
        
        print(f"📈 Final dataset shape: {X.shape}, Target shape: {y.shape}")
        
        # Split data (use time series split to avoid look-ahead bias)
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        return X_train_scaled, X_test_scaled, y_train.values, y_test.values, feature_columns
    
    def train_direction_models(self, df):
        """Train models to predict stock direction (up/down)"""
        print("\n🚀 Training Direction Prediction Models...")
        print("="*50)
        
        X_train, X_test, y_train, y_test, features = self.prepare_data(df, 'Direction_Up')
        
        # Models to compare
        models = {
            'Random Forest': RandomForestClassifier(n_estimators=100, random_state=42),
            'Logistic Regression': LogisticRegression(random_state=42, max_iter=1000),
            'SVM': SVC(random_state=42, probability=True)
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"\n🔧 Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, y_pred)
            
            # Cross-validation score
            cv_scores = cross_val_score(model, X_train, y_train, cv=5)
            
            results[name] = {
                'model': model,
                'accuracy': accuracy,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std(),
                'predictions': y_pred,
                'feature_names': features
            }
            print(f"   ✅ Test Accuracy: {accuracy:.4f}")
            print(f"   📊 CV Score: {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        
        self.results['direction'] = results
        self.results['direction']['y_test'] = y_test
        
        # Validate against minimum thresholds with highlighting
        self._validate_direction_performance(results)
        
        return results
    
    def _validate_direction_performance(self, results):
        """Validate direction prediction performance against minimum thresholds"""
        print(f"\n📊 PERFORMANCE VALIDATION - DIRECTION PREDICTION")
        print("=" * 65)
        
        # Define minimum thresholds
        THRESHOLDS = {
            'accuracy_min': 0.45,      # 45% minimum accuracy
            'accuracy_good': 0.55,     # 55% good performance  
            'accuracy_excellent': 0.60, # 60% excellent
            'cv_mean_min': 0.40,       # 40% minimum CV mean
            'cv_std_max': 0.15,        # 15% maximum CV std deviation
        }
        
        print(f"🎯 Minimum Thresholds:")
        print(f"   • Accuracy: ≥{THRESHOLDS['accuracy_min']:.1%} (Minimum) | ≥{THRESHOLDS['accuracy_good']:.1%} (Good) | ≥{THRESHOLDS['accuracy_excellent']:.1%} (Excellent)")
        print(f"   • CV Mean: ≥{THRESHOLDS['cv_mean_min']:.1%} (Stability)")
        print(f"   • CV Std Dev: ≤{THRESHOLDS['cv_std_max']:.1%} (Consistency)")
        print("-" * 65)
        
        for name, result in results.items():
            if name != 'y_test' and isinstance(result, dict) and 'accuracy' in result:
                accuracy = result['accuracy']
                cv_mean = result['cv_mean']
                cv_std = result['cv_std']
                
                # Performance rating
                if accuracy >= THRESHOLDS['accuracy_excellent']:
                    accuracy_rating = "🌟 EXCELLENT"
                    accuracy_color = "🟢"
                elif accuracy >= THRESHOLDS['accuracy_good']:
                    accuracy_rating = "✅ GOOD"
                    accuracy_color = "🟢"
                elif accuracy >= THRESHOLDS['accuracy_min']:
                    accuracy_rating = "⚠️  ACCEPTABLE"
                    accuracy_color = "🟡"
                else:
                    accuracy_rating = "❌ POOR"
                    accuracy_color = "🔴"
                
                # CV stability check
                cv_stable = cv_std <= THRESHOLDS['cv_std_max']
                cv_adequate = cv_mean >= THRESHOLDS['cv_mean_min']
                
                cv_color = "🟢" if (cv_stable and cv_adequate) else "🟡" if cv_stable else "🔴"
                
                print(f"{name:<20} | {accuracy_color} {accuracy:.1%} | CV: {cv_mean:.1%}±{cv_std:.1%} {cv_color} | {accuracy_rating}")
                
                # Detailed validation feedback
                if accuracy < THRESHOLDS['accuracy_min']:
                    print(f"   ⚠️  WARNING: {name} accuracy {accuracy:.1%} below minimum {THRESHOLDS['accuracy_min']:.1%}")
                if not cv_stable:
                    print(f"   ⚠️  WARNING: {name} CV std {cv_std:.1%} exceeds maximum {THRESHOLDS['cv_std_max']:.1%}")
                if not cv_adequate:
                    print(f"   ⚠️  WARNING: {name} CV mean {cv_mean:.1%} below minimum {THRESHOLDS['cv_mean_min']:.1%}")
        
        # Overall assessment
        all_models_meet_minimum = all(
            result.get('accuracy', 0) >= THRESHOLDS['accuracy_min'] and
            result.get('cv_std', 1) <= THRESHOLDS['cv_std_max'] and
            result.get('cv_mean', 0) >= THRESHOLDS['cv_mean_min']
            for result in results.values() 
            if isinstance(result, dict) and 'accuracy' in result
        )
        
        if all_models_meet_minimum:
            print(f"\n🎉 SUCCESS: All models meet minimum performance thresholds!")
        else:
            print(f"\n⚠️  NOTICE: Some models below minimum thresholds - consider tuning or more data")
    
    def train_price_models(self, df):
        """Train models to predict actual stock prices"""
        print("\n🚀 Training Price Prediction Models...")
        print("="*50)
        
        X_train, X_test, y_train, y_test, features = self.prepare_data(df, 'Next_Day_Price')
        
        # Models to compare
        models = {
            'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42),
            'Linear Regression': LinearRegression(),
            'SVR': SVR(kernel='rbf')
        }
        
        results = {}
        
        for name, model in models.items():
            print(f"\n🔧 Training {name}...")
            
            # Train model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            r2 = r2_score(y_test, y_pred)
            
            # Mean Absolute Percentage Error
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            results[name] = {
                'model': model,
                'mse': mse,
                'rmse': rmse,
                'r2': r2,
                'mape': mape,
                'predictions': y_pred,
                'feature_names': features
            }
            
            print(f"   ✅ RMSE: ${rmse:.2f}")
            print(f"   📊 R² Score: {r2:.4f}")
            print(f"   📈 MAPE: {mape:.2f}%")
        
        self.results['price'] = results
        self.results['price']['y_test'] = y_test
        
        # Validate against minimum thresholds with highlighting
        self._validate_price_performance(results)
        
        return results
    
    def _validate_price_performance(self, results):
        """Validate price prediction performance against minimum thresholds"""
        print(f"\n📊 PERFORMANCE VALIDATION - PRICE PREDICTION")
        print("=" * 65)
        
        # Define minimum thresholds
        THRESHOLDS = {
            'r2_min': 0.30,           # 30% minimum R² score
            'r2_good': 0.50,          # 50% good R² score
            'r2_excellent': 0.70,     # 70% excellent R² score
            'mape_max': 10.0,         # 10% maximum MAPE
            'mape_good': 7.0,         # 7% good MAPE
            'mape_excellent': 5.0,    # 5% excellent MAPE
        }
        
        print(f"🎯 Minimum Thresholds:")
        print(f"   • R² Score: ≥{THRESHOLDS['r2_min']:.2f} (Minimum) | ≥{THRESHOLDS['r2_good']:.2f} (Good) | ≥{THRESHOLDS['r2_excellent']:.2f} (Excellent)")
        print(f"   • MAPE: ≤{THRESHOLDS['mape_max']:.1f}% (Maximum) | ≤{THRESHOLDS['mape_good']:.1f}% (Good) | ≤{THRESHOLDS['mape_excellent']:.1f}% (Excellent)")
        print(f"   • RMSE: Context-dependent (lower is better)")
        print("-" * 65)
        
        for name, result in results.items():
            if name != 'y_test' and isinstance(result, dict) and 'r2' in result:
                r2 = result['r2']
                mape = result['mape']
                rmse = result['rmse']
                
                # R² performance rating
                if r2 >= THRESHOLDS['r2_excellent']:
                    r2_rating = "🌟 EXCELLENT"
                    r2_color = "🟢"
                elif r2 >= THRESHOLDS['r2_good']:
                    r2_rating = "✅ GOOD"
                    r2_color = "🟢"
                elif r2 >= THRESHOLDS['r2_min']:
                    r2_rating = "⚠️  ACCEPTABLE"
                    r2_color = "🟡"
                else:
                    r2_rating = "❌ POOR"
                    r2_color = "🔴"
                
                # MAPE performance rating
                if mape <= THRESHOLDS['mape_excellent']:
                    mape_rating = "🌟 EXCELLENT"
                    mape_color = "🟢"
                elif mape <= THRESHOLDS['mape_good']:
                    mape_rating = "✅ GOOD"
                    mape_color = "🟢"
                elif mape <= THRESHOLDS['mape_max']:
                    mape_rating = "⚠️  ACCEPTABLE"
                    mape_color = "🟡"
                else:
                    mape_rating = "❌ POOR"
                    mape_color = "🔴"
                
                print(f"{name:<20} | {r2_color} R²:{r2:6.3f} | {mape_color} MAPE:{mape:5.1f}% | RMSE:${rmse:6.2f} | {r2_rating}")
                
                # Detailed validation feedback
                if r2 < THRESHOLDS['r2_min']:
                    print(f"   ⚠️  WARNING: {name} R² {r2:.3f} below minimum {THRESHOLDS['r2_min']:.2f}")
                if mape > THRESHOLDS['mape_max']:
                    print(f"   ⚠️  WARNING: {name} MAPE {mape:.1f}% exceeds maximum {THRESHOLDS['mape_max']:.1f}%")
        
        # Overall assessment
        all_models_meet_minimum = all(
            result.get('r2', -1) >= THRESHOLDS['r2_min'] and
            result.get('mape', 100) <= THRESHOLDS['mape_max']
            for result in results.values() 
            if isinstance(result, dict) and 'r2' in result
        )
        
        if all_models_meet_minimum:
            print(f"\n🎉 SUCCESS: All models meet minimum performance thresholds!")
        else:
            print(f"\n⚠️  NOTICE: Some models below minimum thresholds - consider tuning or more data")

def main():
    """Main function to run the learning exercise"""
    print("🎓 Welcome to Stock Prediction Learning Project!")
    print("=" * 60)
    
    # Step 1: Collect Data
    collector = StockDataCollector()
    
    # Use a well-known stock for learning
    symbol = 'AAPL'  # Apple - good for learning due to liquidity and patterns
    data = collector.fetch_data(symbol, period='2y')
    
    if data is None:
        print("❌ Failed to fetch data. Please check your internet connection.")
        return
    
    collector.get_basic_info()
    
    # Step 2: Create Features
    feature_data = FeatureEngine.create_technical_features(data)
    final_data = FeatureEngine.create_target_variables(feature_data)
    
    # Step 3: Train Models
    ml_models = SimpleMLModels()
    
    # Train direction prediction models
    direction_results = ml_models.train_direction_models(final_data)
    
    # Train price prediction models  
    price_results = ml_models.train_price_models(final_data)
    
    # Step 4: Summary
    print("\n🎉 Learning Exercise Complete!")
    print("=" * 60)
    
    print("\n📚 What you learned:")
    print("1. Data collection from financial APIs")
    print("2. Feature engineering with technical indicators")
    print("3. Multiple model comparison")
    print("4. Classification vs Regression tasks")
    print("5. Model evaluation metrics")
    print("6. Cross-validation techniques")
    
    print(f"\n💡 Next Steps:")
    print("1. Try different stocks and time periods")
    print("2. Experiment with feature selection")
    print("3. Tune hyperparameters")
    print("4. Add more sophisticated features")
    print("5. Try ensemble methods")
    
    return ml_models

if __name__ == "__main__":
    # Run the learning exercise
    models = main()
