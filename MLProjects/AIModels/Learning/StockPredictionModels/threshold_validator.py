#!/usr/bin/env python3
"""
Performance Threshold Validator
==============================

This script demonstrates and validates performance thresholds for machine learning models
with clear minimum value highlighting and business context explanations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, r2_score
from simple_stock_predictor import StockDataCollector, FeatureEngine, SimpleMLModels

class ThresholdValidator:
    """Comprehensive threshold validation with clear minimum value highlighting"""
    
    def __init__(self):
        """Initialize with industry-standard thresholds"""
        
        # ===============================================
        # MINIMUM PERFORMANCE THRESHOLDS DEFINITION
        # ===============================================
        
        self.DIRECTION_THRESHOLDS = {
            'accuracy_min': 0.45,      # 45% - Minimum acceptable accuracy
            'accuracy_good': 0.55,     # 55% - Good performance threshold
            'accuracy_excellent': 0.60, # 60% - Excellent performance threshold
            'cv_mean_min': 0.40,       # 40% - Minimum CV mean for stability
            'cv_std_max': 0.15,        # 15% - Maximum CV standard deviation
        }
        
        self.PRICE_THRESHOLDS = {
            'r2_min': 0.30,           # 30% - Minimum R² score
            'r2_good': 0.50,          # 50% - Good R² score
            'r2_excellent': 0.70,     # 70% - Excellent R² score
            'mape_max': 10.0,         # 10% - Maximum acceptable MAPE
            'mape_good': 7.0,         # 7% - Good MAPE threshold
            'mape_excellent': 5.0,    # 5% - Excellent MAPE threshold
        }
        
        self.validation_results = {}
    
    def explain_threshold_determination(self):
        """Explain how thresholds are determined in real-world ML projects"""
        
        print("🎯 HOW MINIMUM THRESHOLDS ARE DETERMINED")
        print("=" * 60)
        
        print("\n📚 1. INDUSTRY STANDARDS & RESEARCH")
        print("-" * 40)
        print("• Quantitative Finance: 52-58% sustained direction accuracy")
        print("• Academic Papers: 45-65% accuracy for short-term prediction")
        print("• Risk Management: Consistent performance across market conditions")
        print("• Statistical Significance: Must beat random baseline (50%)")
        
        print("\n🏭 2. BUSINESS REQUIREMENTS")
        print("-" * 40)
        print("• Cost of Wrong Predictions: False positives vs false negatives")
        print("• Use Case Context: Learning vs Production vs High-frequency trading")
        print("• Risk Tolerance: How much error can the application handle?")
        print("• ROI Requirements: Performance needed to justify investment")
        
        print("\n📊 3. STATISTICAL BASELINES")
        print("-" * 40)
        print("• Random Baseline: 50% for binary classification (coin flip)")
        print("• Market Baseline: ~51% (slight upward bias in stock markets)")
        print("• Naive Baseline: Using simple moving average or last price")
        print("• Minimum Skill: Statistically significantly better than random")
        
        print("\n👥 4. TEAM DECISIONS (Our Project)")
        print("-" * 40)
        print("• Context: Educational project focused on learning ML concepts")
        print("• Tolerance: More forgiving thresholds for learning purposes")
        print("• Progression: Start with achievable goals, increase difficulty")
        print("• Validation: Ensure models are actually learning patterns")
        
        print("\n💡 THRESHOLD SETTING PROCESS:")
        print("-" * 40)
        print("1️⃣  Research industry benchmarks")
        print("2️⃣  Define business requirements")
        print("3️⃣  Establish statistical baselines")
        print("4️⃣  Set conservative initial thresholds")
        print("5️⃣  Iterate based on actual results")
        print("6️⃣  Document rationale for future reference")
    
    def display_minimum_thresholds(self):
        """Display comprehensive minimum threshold table with explanations"""
        
        print("\n⚖️  COMPREHENSIVE MINIMUM PERFORMANCE THRESHOLDS")
        print("=" * 80)
        
        # Direction Prediction Thresholds
        print("\n🎯 DIRECTION PREDICTION (Classification) THRESHOLDS:")
        print("-" * 65)
        print(f"{'Metric':<20} | {'Minimum':<10} | {'Good':<10} | {'Excellent':<10} | {'Business Logic'}")
        print("-" * 65)
        print(f"{'Accuracy':<20} | {self.DIRECTION_THRESHOLDS['accuracy_min']:<10.1%} | {self.DIRECTION_THRESHOLDS['accuracy_good']:<10.1%} | {self.DIRECTION_THRESHOLDS['accuracy_excellent']:<10.1%} | Better than terrible")
        print(f"{'CV Score Mean':<20} | {self.DIRECTION_THRESHOLDS['cv_mean_min']:<10.1%} | {'N/A':<10} | {'N/A':<10} | Stability across folds")
        print(f"{'CV Std Dev':<20} | {'N/A':<10} | {'N/A':<10} | {self.DIRECTION_THRESHOLDS['cv_std_max']:<10.1%} | Consistency check")
        
        # Price Prediction Thresholds  
        print("\n💰 PRICE PREDICTION (Regression) THRESHOLDS:")
        print("-" * 65)
        print(f"{'Metric':<20} | {'Minimum':<10} | {'Good':<10} | {'Excellent':<10} | {'Business Logic'}")
        print("-" * 65)
        print(f"{'R² Score':<20} | {self.PRICE_THRESHOLDS['r2_min']:<10.2f} | {self.PRICE_THRESHOLDS['r2_good']:<10.2f} | {self.PRICE_THRESHOLDS['r2_excellent']:<10.2f} | Variance explained")
        print(f"{'MAPE':<20} | {self.PRICE_THRESHOLDS['mape_max']:<10.1f}% | {self.PRICE_THRESHOLDS['mape_good']:<10.1f}% | {self.PRICE_THRESHOLDS['mape_excellent']:<10.1f}% | Error tolerance")
        print(f"{'RMSE':<20} | {'Stock-dep':<10} | {'Lower':<10} | {'Context':<10} | Relative to volatility")
        
        print("\n📋 THRESHOLD EXPLANATIONS:")
        print("-" * 50)
        print("🎯 Accuracy ≥ 45%:")
        print("   • Random baseline is 50% (coin flip)")
        print("   • Stock prediction is inherently difficult")
        print("   • 45% minimum ensures model is learning patterns")
        print("   • Professional traders achieve 52-58% sustained accuracy")
        
        print("\n📊 R² Score ≥ 0.30:")
        print("   • Explains at least 30% of price variance")
        print("   • Reasonable for volatile financial markets")
        print("   • Academic threshold for publishable results")
        print("   • Higher than 0.30 indicates meaningful predictive power")
        
        print("\n📈 MAPE ≤ 10%:")
        print("   • Price predictions within 10% error tolerance")
        print("   • Reasonable for day-ahead price forecasting")
        print("   • Industry acceptable for trading applications")
        print("   • Accounts for normal market volatility")
        
        print("\n🔄 CV Standard Deviation ≤ 15%:")
        print("   • Ensures model consistency across different data splits")
        print("   • Prevents overfitting to specific time periods")
        print("   • Validates model stability for production use")
        print("   • Lower values indicate more reliable models")
    
    def validate_single_model(self, accuracy=None, cv_mean=None, cv_std=None, 
                            r2=None, mape=None, rmse=None, model_name="Test Model"):
        """
        Validate a single model against thresholds with detailed highlighting
        
        Args:
            accuracy (float): Classification accuracy (0-1)
            cv_mean (float): Cross-validation mean score
            cv_std (float): Cross-validation standard deviation
            r2 (float): R² score for regression
            mape (float): Mean Absolute Percentage Error
            rmse (float): Root Mean Square Error
            model_name (str): Name of the model being validated
        """
        
        print(f"\n🔍 VALIDATING MODEL: {model_name}")
        print("=" * 60)
        
        validation_passed = True
        issues = []
        
        # Direction Prediction Validation
        if accuracy is not None:
            print(f"\n🎯 DIRECTION PREDICTION VALIDATION:")
            print("-" * 40)
            
            # Accuracy validation
            if accuracy >= self.DIRECTION_THRESHOLDS['accuracy_excellent']:
                acc_status = "🌟 EXCELLENT"
                acc_color = "🟢"
            elif accuracy >= self.DIRECTION_THRESHOLDS['accuracy_good']:
                acc_status = "✅ GOOD"
                acc_color = "🟢"
            elif accuracy >= self.DIRECTION_THRESHOLDS['accuracy_min']:
                acc_status = "⚠️  ACCEPTABLE"
                acc_color = "🟡"
            else:
                acc_status = "❌ POOR"
                acc_color = "🔴"
                validation_passed = False
                issues.append(f"Accuracy {accuracy:.1%} below minimum {self.DIRECTION_THRESHOLDS['accuracy_min']:.1%}")
            
            print(f"   Accuracy: {acc_color} {accuracy:.1%} vs Min {self.DIRECTION_THRESHOLDS['accuracy_min']:.1%} → {acc_status}")
            
            # CV Mean validation
            if cv_mean is not None:
                if cv_mean >= self.DIRECTION_THRESHOLDS['cv_mean_min']:
                    cv_mean_status = "✅ STABLE"
                    cv_mean_color = "🟢"
                else:
                    cv_mean_status = "❌ UNSTABLE"
                    cv_mean_color = "🔴"
                    validation_passed = False
                    issues.append(f"CV mean {cv_mean:.1%} below minimum {self.DIRECTION_THRESHOLDS['cv_mean_min']:.1%}")
                
                print(f"   CV Mean: {cv_mean_color} {cv_mean:.1%} vs Min {self.DIRECTION_THRESHOLDS['cv_mean_min']:.1%} → {cv_mean_status}")
            
            # CV Std validation
            if cv_std is not None:
                if cv_std <= self.DIRECTION_THRESHOLDS['cv_std_max']:
                    cv_std_status = "✅ CONSISTENT"
                    cv_std_color = "🟢"
                else:
                    cv_std_status = "❌ INCONSISTENT"
                    cv_std_color = "🔴"
                    validation_passed = False
                    issues.append(f"CV std {cv_std:.1%} exceeds maximum {self.DIRECTION_THRESHOLDS['cv_std_max']:.1%}")
                
                print(f"   CV Std: {cv_std_color} {cv_std:.1%} vs Max {self.DIRECTION_THRESHOLDS['cv_std_max']:.1%} → {cv_std_status}")
        
        # Price Prediction Validation
        if r2 is not None or mape is not None:
            print(f"\n💰 PRICE PREDICTION VALIDATION:")
            print("-" * 40)
            
            # R² validation
            if r2 is not None:
                if r2 >= self.PRICE_THRESHOLDS['r2_excellent']:
                    r2_status = "🌟 EXCELLENT"
                    r2_color = "🟢"
                elif r2 >= self.PRICE_THRESHOLDS['r2_good']:
                    r2_status = "✅ GOOD"
                    r2_color = "🟢"
                elif r2 >= self.PRICE_THRESHOLDS['r2_min']:
                    r2_status = "⚠️  ACCEPTABLE"
                    r2_color = "🟡"
                else:
                    r2_status = "❌ POOR"
                    r2_color = "🔴"
                    validation_passed = False
                    issues.append(f"R² {r2:.3f} below minimum {self.PRICE_THRESHOLDS['r2_min']:.2f}")
                
                print(f"   R² Score: {r2_color} {r2:.3f} vs Min {self.PRICE_THRESHOLDS['r2_min']:.2f} → {r2_status}")
            
            # MAPE validation
            if mape is not None:
                if mape <= self.PRICE_THRESHOLDS['mape_excellent']:
                    mape_status = "🌟 EXCELLENT"
                    mape_color = "🟢"
                elif mape <= self.PRICE_THRESHOLDS['mape_good']:
                    mape_status = "✅ GOOD"
                    mape_color = "🟢"
                elif mape <= self.PRICE_THRESHOLDS['mape_max']:
                    mape_status = "⚠️  ACCEPTABLE"
                    mape_color = "🟡"
                else:
                    mape_status = "❌ POOR"
                    mape_color = "🔴"
                    validation_passed = False
                    issues.append(f"MAPE {mape:.1f}% exceeds maximum {self.PRICE_THRESHOLDS['mape_max']:.1f}%")
                
                print(f"   MAPE: {mape_color} {mape:.1f}% vs Max {self.PRICE_THRESHOLDS['mape_max']:.1f}% → {mape_status}")
            
            # RMSE context
            if rmse is not None:
                print(f"   RMSE: ${rmse:.2f} (context-dependent, lower is better)")
        
        # Overall validation result
        print(f"\n🏆 OVERALL VALIDATION RESULT:")
        print("-" * 40)
        
        if validation_passed:
            print(f"🎉 SUCCESS: {model_name} meets all minimum performance thresholds!")
            print("✅ Model is ready for further development/deployment")
        else:
            print(f"⚠️  ISSUES DETECTED: {model_name} has performance concerns")
            print("❌ Review the following issues:")
            for issue in issues:
                print(f"   • {issue}")
            print("\n💡 RECOMMENDATIONS:")
            print("   • Try different hyperparameters")
            print("   • Increase training data size")
            print("   • Engineer additional features")
            print("   • Consider different algorithms")
        
        return validation_passed, issues
    
    def run_comprehensive_validation(self, symbol='AAPL', period='1y'):
        """
        Run comprehensive validation on real models with threshold highlighting
        """
        
        print("🧪 COMPREHENSIVE MODEL VALIDATION WITH THRESHOLD HIGHLIGHTING")
        print("=" * 70)
        print(f"Symbol: {symbol} | Period: {period}")
        print(f"Validation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Explain thresholds first
        self.explain_threshold_determination()
        self.display_minimum_thresholds()
        
        # Get data and train models
        print(f"\n📊 TRAINING MODELS FOR VALIDATION...")
        print("-" * 50)
        
        collector = StockDataCollector()
        data = collector.fetch_data(symbol, period)
        
        if data is None:
            print("❌ Could not fetch data for validation")
            return False
        
        # Create features and targets
        feature_data = FeatureEngine.create_technical_features(data)
        final_data = FeatureEngine.create_target_variables(feature_data)
        
        # Train models
        ml_models = SimpleMLModels()
        direction_results = ml_models.train_direction_models(final_data)
        price_results = ml_models.train_price_models(final_data)
        
        # Validate each model
        print(f"\n🔍 INDIVIDUAL MODEL VALIDATION RESULTS:")
        print("=" * 70)
        
        all_passed = True
        
        # Validate direction models
        for model_name, result in direction_results.items():
            if isinstance(result, dict) and 'accuracy' in result:
                passed, issues = self.validate_single_model(
                    accuracy=result['accuracy'],
                    cv_mean=result['cv_mean'],
                    cv_std=result['cv_std'],
                    model_name=f"{model_name} (Direction)"
                )
                if not passed:
                    all_passed = False
        
        # Validate price models
        for model_name, result in price_results.items():
            if isinstance(result, dict) and 'r2' in result:
                passed, issues = self.validate_single_model(
                    r2=result['r2'],
                    mape=result['mape'],
                    rmse=result['rmse'],
                    model_name=f"{model_name} (Price)"
                )
                if not passed:
                    all_passed = False
        
        # Final summary
        print(f"\n🏆 FINAL VALIDATION SUMMARY:")
        print("=" * 50)
        
        if all_passed:
            print("🎉 SUCCESS: All models meet minimum performance thresholds!")
            print("✅ Your ML pipeline is performing as expected")
            print("🚀 Ready for production or advanced experimentation")
        else:
            print("⚠️  MIXED RESULTS: Some models need improvement")
            print("📈 Consider model tuning and additional training")
            print("💡 Use this feedback to guide your learning journey")
        
        return all_passed

def main():
    """Run interactive threshold validation demo"""
    
    print("🎯 MACHINE LEARNING THRESHOLD VALIDATOR")
    print("=" * 50)
    
    validator = ThresholdValidator()
    
    while True:
        print(f"\n🧪 Validation Options:")
        print("1. 📚 Explain how thresholds are determined")
        print("2. ⚖️  Display minimum threshold table")
        print("3. 🔍 Validate single model (manual input)")
        print("4. 🚀 Run comprehensive validation (real models)")
        print("5. 📊 Demo with example values")
        print("6. 🚪 Exit")
        
        choice = input(f"\n👉 Choose option (1-6): ").strip()
        
        if choice == '1':
            validator.explain_threshold_determination()
        
        elif choice == '2':
            validator.display_minimum_thresholds()
        
        elif choice == '3':
            print(f"\n🔍 Manual Model Validation")
            print("-" * 30)
            
            model_name = input("Model name: ").strip() or "Test Model"
            
            try:
                accuracy = input("Accuracy (0-1, or press Enter to skip): ").strip()
                accuracy = float(accuracy) if accuracy else None
                
                cv_mean = input("CV Mean (0-1, or press Enter to skip): ").strip()
                cv_mean = float(cv_mean) if cv_mean else None
                
                cv_std = input("CV Std Dev (0-1, or press Enter to skip): ").strip()
                cv_std = float(cv_std) if cv_std else None
                
                r2 = input("R² Score (-∞ to 1, or press Enter to skip): ").strip()
                r2 = float(r2) if r2 else None
                
                mape = input("MAPE (%, or press Enter to skip): ").strip()
                mape = float(mape) if mape else None
                
                rmse = input("RMSE ($, or press Enter to skip): ").strip()
                rmse = float(rmse) if rmse else None
                
                validator.validate_single_model(
                    accuracy=accuracy, cv_mean=cv_mean, cv_std=cv_std,
                    r2=r2, mape=mape, rmse=rmse, model_name=model_name
                )
                
            except ValueError:
                print("❌ Invalid input. Please enter valid numbers.")
        
        elif choice == '4':
            symbol = input("📊 Stock symbol (default: AAPL): ").strip().upper() or 'AAPL'
            period = input("📅 Period (default: 1y): ").strip() or '1y'
            
            validator.run_comprehensive_validation(symbol, period)
        
        elif choice == '5':
            print(f"\n📊 DEMO: Validation Examples")
            print("-" * 40)
            
            # Good model example
            print(f"\n✅ Example 1: Good Direction Model")
            validator.validate_single_model(
                accuracy=0.58, cv_mean=0.55, cv_std=0.08,
                model_name="Random Forest (Good)"
            )
            
            # Poor model example
            print(f"\n❌ Example 2: Poor Direction Model")
            validator.validate_single_model(
                accuracy=0.42, cv_mean=0.35, cv_std=0.20,
                model_name="Logistic Regression (Poor)"
            )
            
            # Good price model example
            print(f"\n✅ Example 3: Good Price Model")
            validator.validate_single_model(
                r2=0.65, mape=6.2, rmse=5.45,
                model_name="Random Forest Regressor (Good)"
            )
            
            # Poor price model example
            print(f"\n❌ Example 4: Poor Price Model")
            validator.validate_single_model(
                r2=0.15, mape=15.8, rmse=12.30,
                model_name="Linear Regression (Poor)"
            )
        
        elif choice == '6':
            print("👋 Validation complete! Use these insights to improve your models.")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-6.")

if __name__ == "__main__":
    main()
