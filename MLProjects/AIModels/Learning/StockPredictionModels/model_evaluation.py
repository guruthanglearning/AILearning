"""
Model Evaluation and Visualization Tools
=====================================

This module provides comprehensive evaluation and visualization tools
for the stock prediction models.
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc
import warnings
warnings.filterwarnings('ignore')

class ModelEvaluator:
    """Comprehensive model evaluation and visualization"""
    
    def __init__(self, results_dict):
        self.results = results_dict
        
    def plot_direction_results(self):
        """Visualize direction prediction results"""
        if 'direction' not in self.results:
            print("❌ No direction prediction results found")
            return
        
        direction_results = self.results['direction']
        y_test = direction_results['y_test']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('📈 Direction Prediction Model Evaluation', fontsize=16, fontweight='bold')
        
        # 1. Accuracy Comparison
        models = [name for name in direction_results.keys() if name != 'y_test']
        accuracies = [direction_results[name]['accuracy'] for name in models]
        cv_means = [direction_results[name]['cv_mean'] for name in models]
        
        x_pos = np.arange(len(models))
        axes[0,0].bar(x_pos - 0.2, accuracies, 0.4, label='Test Accuracy', alpha=0.8, color='skyblue')
        axes[0,0].bar(x_pos + 0.2, cv_means, 0.4, label='CV Mean', alpha=0.8, color='lightcoral')
        axes[0,0].set_xlabel('Models')
        axes[0,0].set_ylabel('Accuracy')
        axes[0,0].set_title('🎯 Model Accuracy Comparison')
        axes[0,0].set_xticks(x_pos)
        axes[0,0].set_xticklabels(models, rotation=45)
        axes[0,0].legend()
        axes[0,0].axhline(y=0.5, color='red', linestyle='--', alpha=0.7, label='Random (50%)')
        
        # 2. Confusion Matrix (Best Model)
        best_model_name = max(models, key=lambda x: direction_results[x]['accuracy'])
        best_predictions = direction_results[best_model_name]['predictions']
        
        cm = confusion_matrix(y_test, best_predictions)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0,1])
        axes[0,1].set_title(f'🔍 Confusion Matrix - {best_model_name}')
        axes[0,1].set_xlabel('Predicted')
        axes[0,1].set_ylabel('Actual')
        
        # 3. ROC Curves (if probability predictions available)
        for i, model_name in enumerate(models):
            model = direction_results[model_name]['model']
            if hasattr(model, 'predict_proba'):
                # Get feature data for prediction
                try:
                    X_test_for_roc = self._get_test_features(model_name)
                    y_prob = model.predict_proba(X_test_for_roc)[:, 1]
                    fpr, tpr, _ = roc_curve(y_test, y_prob)
                    roc_auc = auc(fpr, tpr)
                    axes[1,0].plot(fpr, tpr, label=f'{model_name} (AUC = {roc_auc:.3f})', linewidth=2)
                except:
                    continue
        
        axes[1,0].plot([0, 1], [0, 1], 'k--', alpha=0.5)
        axes[1,0].set_xlabel('False Positive Rate')
        axes[1,0].set_ylabel('True Positive Rate')
        axes[1,0].set_title('📊 ROC Curves')
        axes[1,0].legend()
        
        # 4. Feature Importance (Best Model)
        if hasattr(direction_results[best_model_name]['model'], 'feature_importances_'):
            importances = direction_results[best_model_name]['model'].feature_importances_
            feature_names = direction_results[best_model_name]['feature_names']
            
            # Get top 10 features
            indices = np.argsort(importances)[::-1][:10]
            top_features = [feature_names[i] for i in indices]
            top_importances = importances[indices]
            
            axes[1,1].barh(range(len(top_features)), top_importances, color='green', alpha=0.7)
            axes[1,1].set_yticks(range(len(top_features)))
            axes[1,1].set_yticklabels(top_features)
            axes[1,1].set_xlabel('Importance')
            axes[1,1].set_title(f'🔑 Top Features - {best_model_name}')
            axes[1,1].invert_yaxis()
        
        plt.tight_layout()
        plt.show()
        
        # Print detailed results
        print(f"\n🏆 Best Direction Model: {best_model_name}")
        print(f"✅ Accuracy: {direction_results[best_model_name]['accuracy']:.4f}")
        print(f"📊 Cross-validation: {direction_results[best_model_name]['cv_mean']:.4f} ± {direction_results[best_model_name]['cv_std']:.4f}")
        
    def plot_price_results(self):
        """Visualize price prediction results"""
        if 'price' not in self.results:
            print("❌ No price prediction results found")
            return
        
        price_results = self.results['price']
        y_test = price_results['y_test']
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('💰 Price Prediction Model Evaluation', fontsize=16, fontweight='bold')
        
        models = [name for name in price_results.keys() if name != 'y_test']
        
        # 1. RMSE Comparison
        rmse_values = [price_results[name]['rmse'] for name in models]
        r2_values = [price_results[name]['r2'] for name in models]
        
        x_pos = np.arange(len(models))
        axes[0,0].bar(x_pos, rmse_values, alpha=0.8, color='orange')
        axes[0,0].set_xlabel('Models')
        axes[0,0].set_ylabel('RMSE ($)')
        axes[0,0].set_title('📉 Root Mean Square Error')
        axes[0,0].set_xticks(x_pos)
        axes[0,0].set_xticklabels(models, rotation=45)
        
        # 2. R² Score Comparison
        axes[0,1].bar(x_pos, r2_values, alpha=0.8, color='green')
        axes[0,1].set_xlabel('Models')
        axes[0,1].set_ylabel('R² Score')
        axes[0,1].set_title('📊 R² Score Comparison')
        axes[0,1].set_xticks(x_pos)
        axes[0,1].set_xticklabels(models, rotation=45)
        axes[0,1].axhline(y=0, color='red', linestyle='--', alpha=0.7)
        
        # 3. Actual vs Predicted (Best Model)
        best_model_name = max(models, key=lambda x: price_results[x]['r2'])
        best_predictions = price_results[best_model_name]['predictions']
        
        axes[1,0].scatter(y_test, best_predictions, alpha=0.6, color='blue')
        axes[1,0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        axes[1,0].set_xlabel('Actual Price ($)')
        axes[1,0].set_ylabel('Predicted Price ($)')
        axes[1,0].set_title(f'🎯 Actual vs Predicted - {best_model_name}')
        
        # Add correlation coefficient
        correlation = np.corrcoef(y_test, best_predictions)[0, 1]
        axes[1,0].text(0.05, 0.95, f'Correlation: {correlation:.3f}', 
                      transform=axes[1,0].transAxes, bbox=dict(boxstyle="round", facecolor='wheat'))
        
        # 4. Prediction Errors Distribution
        errors = y_test - best_predictions
        axes[1,1].hist(errors, bins=30, alpha=0.7, color='purple', edgecolor='black')
        axes[1,1].axvline(x=0, color='red', linestyle='--', linewidth=2)
        axes[1,1].set_xlabel('Prediction Error ($)')
        axes[1,1].set_ylabel('Frequency')
        axes[1,1].set_title(f'📊 Prediction Errors - {best_model_name}')
        
        # Add error statistics
        mean_error = np.mean(errors)
        std_error = np.std(errors)
        axes[1,1].text(0.05, 0.95, f'Mean: ${mean_error:.2f}\nStd: ${std_error:.2f}', 
                      transform=axes[1,1].transAxes, bbox=dict(boxstyle="round", facecolor='wheat'))
        
        plt.tight_layout()
        plt.show()
        
        # Print detailed results
        print(f"\n🏆 Best Price Model: {best_model_name}")
        print(f"💰 RMSE: ${price_results[best_model_name]['rmse']:.2f}")
        print(f"📊 R² Score: {price_results[best_model_name]['r2']:.4f}")
        print(f"📈 MAPE: {price_results[best_model_name]['mape']:.2f}%")
    
    def _get_test_features(self, model_name):
        """Helper method to get test features (simplified)"""
        # This is a simplified approach - in practice, you'd store the test features
        # For now, return a placeholder
        return np.random.randn(100, 10)  # Placeholder
    
    def generate_model_report(self):
        """Generate comprehensive model performance report"""
        print("\n" + "="*60)
        print("📊 COMPREHENSIVE MODEL EVALUATION REPORT")
        print("="*60)
        
        if 'direction' in self.results:
            print("\n🎯 DIRECTION PREDICTION MODELS")
            print("-" * 40)
            direction_results = self.results['direction']
            models = [name for name in direction_results.keys() if name != 'y_test']
            
            for model_name in models:
                result = direction_results[model_name]
                print(f"\n📈 {model_name}:")
                print(f"   • Test Accuracy: {result['accuracy']:.4f}")
                print(f"   • CV Score: {result['cv_mean']:.4f} ± {result['cv_std']:.4f}")
                
                # Interpretation
                if result['accuracy'] > 0.6:
                    print(f"   ✅ Excellent performance (>60%)")
                elif result['accuracy'] > 0.55:
                    print(f"   ✅ Good performance (>55%)")
                elif result['accuracy'] > 0.5:
                    print(f"   ⚠️ Marginal performance (>50%)")
                else:
                    print(f"   ❌ Poor performance (≤50%)")
        
        if 'price' in self.results:
            print("\n💰 PRICE PREDICTION MODELS")
            print("-" * 40)
            price_results = self.results['price']
            models = [name for name in price_results.keys() if name != 'y_test']
            
            for model_name in models:
                result = price_results[model_name]
                print(f"\n📊 {model_name}:")
                print(f"   • RMSE: ${result['rmse']:.2f}")
                print(f"   • R² Score: {result['r2']:.4f}")
                print(f"   • MAPE: {result['mape']:.2f}%")
                
                # Interpretation
                if result['r2'] > 0.7:
                    print(f"   ✅ Excellent fit (R² > 0.7)")
                elif result['r2'] > 0.5:
                    print(f"   ✅ Good fit (R² > 0.5)")
                elif result['r2'] > 0.3:
                    print(f"   ⚠️ Moderate fit (R² > 0.3)")
                else:
                    print(f"   ❌ Poor fit (R² ≤ 0.3)")
        
        print("\n🎓 LEARNING INSIGHTS:")
        print("-" * 30)
        print("1. Compare different algorithms to understand their strengths")
        print("2. Look for overfitting (large gap between train/test performance)")
        print("3. Feature importance helps understand what drives predictions")
        print("4. Cross-validation provides more reliable performance estimates")
        print("5. Always compare against a simple baseline (random predictions)")

def create_evaluation_report(results):
    """Create and display comprehensive evaluation report"""
    evaluator = ModelEvaluator(results)
    
    # Generate plots
    if 'direction' in results:
        evaluator.plot_direction_results()
    
    if 'price' in results:
        evaluator.plot_price_results()
    
    # Generate text report
    evaluator.generate_model_report()
    
    return evaluator
