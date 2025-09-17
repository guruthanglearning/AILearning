#!/usr/bin/env python3
"""
Model Testing and Validation Framework
=====================================

This script provides comprehensive testing logic to validate if the model 
results are as expected and performing correctly.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report,
    mean_squared_error, mean_absolute_error, r2_score
)
from simple_stock_predictor import StockDataCollector, FeatureEngine, SimpleMLModels

class ModelTester:
    """Comprehensive model testing and validation framework"""
    
    def __init__(self):
        self.test_results = {}
        self.validation_threshold = {
            'direction_accuracy_min': 0.45,  # Minimum 45% (better than terrible)
            'direction_accuracy_good': 0.55,  # Good performance 55%+
            'direction_accuracy_excellent': 0.60,  # Excellent 60%+
            'price_r2_min': 0.3,  # Minimum R² for price prediction
            'price_r2_good': 0.5,  # Good R² performance
            'price_r2_excellent': 0.7,  # Excellent R² performance
            'cv_std_max': 0.15,  # Maximum acceptable CV standard deviation
            'mape_max': 10.0,  # Maximum acceptable MAPE percentage
        }
    
    def test_data_quality(self, symbol='AAPL', period='1y'):
        """
        Test 1: Data Quality Validation
        Ensures the input data meets quality standards
        """
        print("🔍 TEST 1: DATA QUALITY VALIDATION")
        print("=" * 50)
        
        collector = StockDataCollector()
        data = collector.fetch_data(symbol, period)
        
        if data is None:
            print("❌ FAIL: Could not fetch data")
            return False
        
        # Test data completeness
        tests = {
            'data_not_empty': len(data) > 0,
            'has_required_columns': all(col in data.columns for col in ['Open', 'High', 'Low', 'Close', 'Volume']),
            'sufficient_data_points': len(data) >= 50,  # Minimum data points
            'no_all_nan_columns': not data.isnull().all().any(),
            'price_data_positive': (data[['Open', 'High', 'Low', 'Close']] > 0).all().all(),
            'high_ge_low': (data['High'] >= data['Low']).all(),
            'volume_non_negative': (data['Volume'] >= 0).all()
        }
        
        print(f"📊 Testing {symbol} data ({len(data)} days):")
        all_passed = True
        
        for test_name, passed in tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if not passed:
                all_passed = False
        
        # Data quality score
        quality_score = sum(tests.values()) / len(tests)
        print(f"\n📈 Data Quality Score: {quality_score:.1%}")
        
        return all_passed, data
    
    def test_feature_engineering(self, data):
        """
        Test 2: Feature Engineering Validation
        Ensures features are created correctly
        """
        print("\n🔧 TEST 2: FEATURE ENGINEERING VALIDATION")
        print("=" * 50)
        
        original_columns = len(data.columns)
        feature_data = FeatureEngine.create_technical_features(data)
        final_data = FeatureEngine.create_target_variables(feature_data)
        
        # Test feature creation
        tests = {
            'features_added': len(final_data.columns) > original_columns,
            'price_change_exists': 'Price_Change' in final_data.columns,
            'moving_averages_exist': all(f'MA_{w}' in final_data.columns for w in [5, 10, 20, 50]),
            'rsi_exists': 'RSI' in final_data.columns,
            'bollinger_bands_exist': all(col in final_data.columns for col in ['BB_Upper', 'BB_Lower', 'BB_Position']),
            'targets_created': all(col in final_data.columns for col in ['Direction_Up', 'Next_Day_Price']),
            'rsi_range_valid': final_data['RSI'].dropna().between(0, 100).all() if 'RSI' in final_data.columns else False,
            'bb_position_range_valid': final_data['BB_Position'].dropna().between(0, 1).all() if 'BB_Position' in final_data.columns else False,
        }
        
        print(f"🔧 Feature Engineering Tests:")
        all_passed = True
        
        for test_name, passed in tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if not passed:
                all_passed = False
        
        # Feature statistics
        features_created = len(final_data.columns) - original_columns
        print(f"\n📊 Features Created: {features_created}")
        print(f"📈 Total Columns: {len(final_data.columns)}")
        
        return all_passed, final_data
    
    def test_model_performance(self, data, symbol='TEST'):
        """
        Test 3: Model Performance Validation
        Tests if models meet performance expectations
        """
        print("\n🤖 TEST 3: MODEL PERFORMANCE VALIDATION")
        print("=" * 50)
        
        ml_models = SimpleMLModels()
        
        # Test direction prediction models
        print("🎯 Testing Direction Prediction Models...")
        direction_results = ml_models.train_direction_models(data)
        
        # Test price prediction models
        print("\n💰 Testing Price Prediction Models...")
        price_results = ml_models.train_price_models(data)
        
        # Validate direction prediction performance
        direction_tests = {}
        for model_name, result in direction_results.items():
            if isinstance(result, dict) and 'accuracy' in result:
                accuracy = result['accuracy']
                cv_mean = result['cv_mean']
                cv_std = result['cv_std']
                
                direction_tests[f"{model_name}_accuracy_above_random"] = accuracy > 0.5
                direction_tests[f"{model_name}_accuracy_reasonable"] = accuracy >= self.validation_threshold['direction_accuracy_min']
                direction_tests[f"{model_name}_cv_stable"] = cv_std <= self.validation_threshold['cv_std_max']
                direction_tests[f"{model_name}_cv_reasonable"] = cv_mean >= 0.4
        
        # Validate price prediction performance
        price_tests = {}
        for model_name, result in price_results.items():
            if isinstance(result, dict) and 'r2' in result:
                r2 = result['r2']
                mape = result['mape']
                
                price_tests[f"{model_name}_r2_positive"] = r2 > 0
                price_tests[f"{model_name}_r2_reasonable"] = r2 >= self.validation_threshold['price_r2_min']
                price_tests[f"{model_name}_mape_acceptable"] = mape <= self.validation_threshold['mape_max']
        
        # Combined results
        all_tests = {**direction_tests, **price_tests}
        
        print(f"\n📊 Performance Validation Results:")
        performance_passed = True
        
        for test_name, passed in all_tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if not passed:
                performance_passed = False
        
        # Performance summary
        self._print_performance_summary(direction_results, price_results)
        
        return performance_passed, direction_results, price_results
    
    def test_prediction_consistency(self, data, symbol='TEST'):
        """
        Test 4: Prediction Consistency
        Tests if models produce consistent predictions across multiple runs
        """
        print("\n🔄 TEST 4: PREDICTION CONSISTENCY VALIDATION")
        print("=" * 50)
        
        consistency_results = []
        
        # Run the same model multiple times
        for run in range(3):
            print(f"   Run {run + 1}/3...")
            ml_models = SimpleMLModels()
            direction_results = ml_models.train_direction_models(data)
            
            # Extract accuracies
            run_results = {}
            for model_name, result in direction_results.items():
                if isinstance(result, dict) and 'accuracy' in result:
                    run_results[model_name] = result['accuracy']
            
            consistency_results.append(run_results)
        
        # Calculate consistency metrics
        consistency_tests = {}
        
        if len(consistency_results) >= 2:
            for model_name in consistency_results[0].keys():
                accuracies = [run[model_name] for run in consistency_results if model_name in run]
                if len(accuracies) >= 2:
                    std_dev = np.std(accuracies)
                    consistency_tests[f"{model_name}_consistency"] = std_dev <= 0.05  # Max 5% standard deviation
        
        print(f"\n🔄 Consistency Test Results:")
        consistency_passed = True
        
        for test_name, passed in consistency_tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if not passed:
                consistency_passed = False
        
        return consistency_passed, consistency_results
    
    def test_edge_cases(self, symbol='AAPL'):
        """
        Test 5: Edge Case Handling
        Tests how models handle unusual scenarios
        """
        print("\n⚠️  TEST 5: EDGE CASE HANDLING")
        print("=" * 50)
        
        edge_tests = {}
        
        # Test with very limited data
        try:
            collector = StockDataCollector()
            limited_data = collector.fetch_data(symbol, period='5d')
            if limited_data is not None and len(limited_data) >= 5:
                feature_data = FeatureEngine.create_technical_features(limited_data)
                final_data = FeatureEngine.create_target_variables(feature_data)
                
                # Try to train with limited data
                ml_models = SimpleMLModels()
                clean_data = final_data.dropna()
                
                if len(clean_data) >= 10:  # Minimum for train/test split
                    direction_results = ml_models.train_direction_models(final_data)
                    edge_tests['handles_limited_data'] = True
                else:
                    edge_tests['handles_limited_data'] = False
            else:
                edge_tests['handles_limited_data'] = False
        except Exception as e:
            print(f"   Limited data test failed: {e}")
            edge_tests['handles_limited_data'] = False
        
        # Test with volatile stock
        try:
            volatile_data = collector.fetch_data('TSLA', period='6mo')  # Tesla is typically volatile
            if volatile_data is not None:
                feature_data = FeatureEngine.create_technical_features(volatile_data)
                final_data = FeatureEngine.create_target_variables(feature_data)
                ml_models = SimpleMLModels()
                direction_results = ml_models.train_direction_models(final_data)
                
                # Check if any model achieves reasonable performance
                any_reasonable = any(
                    result.get('accuracy', 0) >= 0.45 
                    for result in direction_results.values() 
                    if isinstance(result, dict)
                )
                edge_tests['handles_volatile_stock'] = any_reasonable
            else:
                edge_tests['handles_volatile_stock'] = False
        except Exception as e:
            print(f"   Volatile stock test failed: {e}")
            edge_tests['handles_volatile_stock'] = False
        
        print(f"\n⚠️  Edge Case Test Results:")
        edge_passed = True
        
        for test_name, passed in edge_tests.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"   {test_name}: {status}")
            if not passed:
                edge_passed = False
        
        return edge_passed, edge_tests
    
    def _print_performance_summary(self, direction_results, price_results):
        """Print detailed performance summary with validation"""
        print(f"\n📊 DETAILED PERFORMANCE ANALYSIS:")
        print("=" * 60)
        
        # Direction prediction analysis
        print(f"🎯 Direction Prediction Performance:")
        for model_name, result in direction_results.items():
            if isinstance(result, dict) and 'accuracy' in result:
                accuracy = result['accuracy']
                cv_mean = result['cv_mean']
                
                if accuracy >= self.validation_threshold['direction_accuracy_excellent']:
                    performance_rating = "🌟 EXCELLENT"
                elif accuracy >= self.validation_threshold['direction_accuracy_good']:
                    performance_rating = "✅ GOOD"
                elif accuracy >= self.validation_threshold['direction_accuracy_min']:
                    performance_rating = "⚠️  ACCEPTABLE"
                else:
                    performance_rating = "❌ POOR"
                
                print(f"   {model_name:20} | {accuracy:.1%} | CV: {cv_mean:.1%} | {performance_rating}")
        
        # Price prediction analysis
        print(f"\n💰 Price Prediction Performance:")
        for model_name, result in price_results.items():
            if isinstance(result, dict) and 'r2' in result:
                r2 = result['r2']
                mape = result['mape']
                
                if r2 >= self.validation_threshold['price_r2_excellent']:
                    performance_rating = "🌟 EXCELLENT"
                elif r2 >= self.validation_threshold['price_r2_good']:
                    performance_rating = "✅ GOOD"
                elif r2 >= self.validation_threshold['price_r2_min']:
                    performance_rating = "⚠️  ACCEPTABLE"
                else:
                    performance_rating = "❌ POOR"
                
                print(f"   {model_name:20} | R²: {r2:.3f} | MAPE: {mape:.1f}% | {performance_rating}")
    
    def run_comprehensive_test(self, symbol='AAPL', period='1y'):
        """
        Run all tests and provide overall validation
        """
        print("🧪 COMPREHENSIVE MODEL VALIDATION TEST SUITE")
        print("=" * 70)
        print(f"Testing Symbol: {symbol} | Period: {period}")
        print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        all_tests_passed = True
        test_summary = {}
        
        # Test 1: Data Quality
        data_passed, data = self.test_data_quality(symbol, period)
        test_summary['Data Quality'] = data_passed
        if not data_passed:
            all_tests_passed = False
            print("\n❌ CRITICAL: Data quality test failed. Cannot proceed with other tests.")
            return False, test_summary
        
        # Test 2: Feature Engineering
        feature_passed, final_data = self.test_feature_engineering(data)
        test_summary['Feature Engineering'] = feature_passed
        if not feature_passed:
            all_tests_passed = False
        
        # Test 3: Model Performance
        performance_passed, direction_results, price_results = self.test_model_performance(final_data, symbol)
        test_summary['Model Performance'] = performance_passed
        if not performance_passed:
            all_tests_passed = False
        
        # Test 4: Prediction Consistency
        consistency_passed, consistency_results = self.test_prediction_consistency(final_data, symbol)
        test_summary['Prediction Consistency'] = consistency_passed
        if not consistency_passed:
            all_tests_passed = False
        
        # Test 5: Edge Cases
        edge_passed, edge_results = self.test_edge_cases(symbol)
        test_summary['Edge Case Handling'] = edge_passed
        if not edge_passed:
            all_tests_passed = False
        
        # Final Summary
        self._print_final_summary(all_tests_passed, test_summary, symbol)
        
        return all_tests_passed, test_summary
    
    def _print_final_summary(self, all_passed, test_summary, symbol):
        """Print final test summary"""
        print("\n" + "=" * 70)
        print("🏆 FINAL TEST SUMMARY")
        print("=" * 70)
        
        for test_name, passed in test_summary.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{test_name:25} | {status}")
        
        overall_score = sum(test_summary.values()) / len(test_summary)
        
        print(f"\n📊 Overall Test Score: {overall_score:.1%}")
        
        if all_passed:
            print(f"🎉 SUCCESS: All tests passed for {symbol}!")
            print("✅ The model is performing as expected and meeting validation criteria.")
        else:
            print(f"⚠️  WARNING: Some tests failed for {symbol}")
            print("❌ The model may not be performing as expected. Review failed tests above.")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        if overall_score >= 0.8:
            print("✅ Model is ready for production use with this stock")
        elif overall_score >= 0.6:
            print("⚠️  Model shows promise but needs improvement")
            print("   • Consider tuning hyperparameters")
            print("   • Try different time periods")
            print("   • Add more features")
        else:
            print("❌ Model needs significant improvement")
            print("   • Review data quality")
            print("   • Consider different algorithms")
            print("   • Increase training data")

def main():
    """Run interactive testing"""
    print("🧪 Model Testing and Validation Framework")
    print("=" * 50)
    
    tester = ModelTester()
    
    while True:
        print(f"\n🧪 Testing Options:")
        print("1. 🔍 Quick validation test (single stock)")
        print("2. 📊 Comprehensive test suite")
        print("3. ⚖️  Compare multiple stocks")
        print("4. 🏁 Batch test multiple stocks")
        print("5. 🚪 Exit")
        
        choice = input(f"\n👉 Choose option (1-5): ").strip()
        
        if choice == '1':
            symbol = input("📊 Enter stock symbol (default: AAPL): ").strip().upper() or 'AAPL'
            print(f"\n🔍 Running quick validation for {symbol}...")
            
            # Quick test
            passed, data = tester.test_data_quality(symbol)
            if passed:
                _, final_data = tester.test_feature_engineering(data)
                tester.test_model_performance(final_data, symbol)
        
        elif choice == '2':
            symbol = input("📊 Enter stock symbol (default: AAPL): ").strip().upper() or 'AAPL'
            period = input("📅 Enter period (default: 1y): ").strip() or '1y'
            
            tester.run_comprehensive_test(symbol, period)
        
        elif choice == '3':
            symbols = input("📊 Enter symbols to compare (comma-separated): ").strip().upper()
            if symbols:
                symbol_list = [s.strip() for s in symbols.split(',')]
                
                print(f"\n⚖️  Comparing {len(symbol_list)} stocks...")
                results = {}
                
                for symbol in symbol_list:
                    print(f"\n" + "─" * 50)
                    passed, summary = tester.run_comprehensive_test(symbol, '6mo')
                    results[symbol] = {
                        'passed': passed,
                        'score': sum(summary.values()) / len(summary),
                        'summary': summary
                    }
                
                # Comparison summary
                print(f"\n📊 STOCK COMPARISON SUMMARY")
                print("=" * 60)
                print(f"{'Stock':<8} | {'Score':<8} | {'Status':<12} | {'Best Test'}")
                print("-" * 60)
                
                for symbol, result in results.items():
                    score = result['score']
                    status = "✅ PASS" if result['passed'] else "❌ FAIL"
                    best_test = max(result['summary'], key=result['summary'].get)
                    print(f"{symbol:<8} | {score:<7.1%} | {status:<12} | {best_test}")
        
        elif choice == '4':
            symbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA']  # Default batch
            custom_symbols = input(f"📊 Enter custom symbols or press Enter for default {symbols}: ").strip()
            
            if custom_symbols:
                symbols = [s.strip().upper() for s in custom_symbols.split(',')]
            
            print(f"\n🏁 Batch testing {len(symbols)} stocks...")
            batch_results = {}
            
            for i, symbol in enumerate(symbols, 1):
                print(f"\n{'='*20} TESTING {symbol} ({i}/{len(symbols)}) {'='*20}")
                try:
                    passed, summary = tester.run_comprehensive_test(symbol, '6mo')
                    batch_results[symbol] = {
                        'passed': passed,
                        'score': sum(summary.values()) / len(summary)
                    }
                except Exception as e:
                    print(f"❌ Error testing {symbol}: {e}")
                    batch_results[symbol] = {'passed': False, 'score': 0.0}
            
            # Batch summary
            print(f"\n🏁 BATCH TEST RESULTS SUMMARY")
            print("=" * 50)
            passed_count = sum(1 for r in batch_results.values() if r['passed'])
            avg_score = np.mean([r['score'] for r in batch_results.values()])
            
            print(f"📊 Tests Passed: {passed_count}/{len(symbols)} ({passed_count/len(symbols):.1%})")
            print(f"📈 Average Score: {avg_score:.1%}")
            
            # Individual results
            for symbol, result in batch_results.items():
                status = "✅" if result['passed'] else "❌"
                print(f"   {symbol}: {status} ({result['score']:.1%})")
        
        elif choice == '5':
            print("👋 Testing complete! Use these insights to improve your models.")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1-5.")

if __name__ == "__main__":
    main()
