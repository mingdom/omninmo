#!/usr/bin/env python3
"""
Model Comparison Script

This script compares the performance of the current Random Forest model
with the new XGBoost model on historical stock data.
"""

import os
import sys
import argparse
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.models.stock_rating_predictor import StockRatingPredictor
from src.models.xgboost_predictor import XGBoostRatingPredictor
from src.data.stock_data_fetcher import StockDataFetcher
from src.data.features import FeatureEngineer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Compare Random Forest and XGBoost models')
    parser.add_argument('--tickers', type=str, default='AAPL,MSFT,GOOGL,AMZN,META',
                        help='Comma-separated list of stock tickers to use for comparison')
    parser.add_argument('--period', type=str, default='2y',
                        help='Period of historical data to use (e.g., 1y, 2y)')
    parser.add_argument('--test-size', type=float, default=0.3,
                        help='Proportion of data to use for testing')
    parser.add_argument('--output-dir', type=str, default='model_comparison',
                        help='Directory to save comparison results')
    return parser.parse_args()

def prepare_data(tickers, period, test_size=0.3):
    """
    Prepare data for model training and evaluation.
    
    Args:
        tickers (list): List of stock tickers
        period (str): Period of historical data
        test_size (float): Proportion of data to use for testing
        
    Returns:
        tuple: (X_train, X_test, y_train, y_test)
    """
    logger.info(f"Preparing data for {len(tickers)} tickers over {period} period")
    
    # Initialize data containers
    all_features = []
    all_targets = []
    
    # Initialize feature engineer
    feature_engineer = FeatureEngineer()
    
    # Map period to approximate number of days for sample data
    period_to_days = {
        '1mo': 30,
        '3mo': 90,
        '6mo': 180,
        '1y': 365,
        '2y': 730,
        '5y': 1825,
        '10y': 3650,
        'ytd': datetime.now().timetuple().tm_yday,  # Days since beginning of year
        'max': 3650  # Default to 10 years
    }
    
    days = period_to_days.get(period, 365)  # Default to 1 year if period not recognized
    
    # Process each ticker
    for ticker in tickers:
        try:
            logger.info(f"Processing data for {ticker}")
            
            # Generate sample data directly
            end_date = datetime.now()
            dates = []
            current_date = end_date
            
            # Generate approximately days * 1.4 calendar days to get enough business days
            for i in range(int(days * 1.4)):
                current_date = current_date - timedelta(days=1)
                # Skip weekends (0 = Monday, 6 = Sunday)
                if current_date.weekday() < 5:  # Only include weekdays
                    dates.append(current_date)
                if len(dates) >= days:
                    break
                    
            dates.reverse()
            
            # Get base price and volatility for the ticker
            base_price = 100.0  # Default price
            volatility = 0.02   # Default volatility
            
            # Generate price series with realistic trends and volatility
            price_series = []
            current_price = base_price
            for i in range(len(dates)):
                # Add some trend and randomness
                change = np.random.normal(0, volatility)
                # Add some mean reversion
                if current_price > base_price * 1.5:
                    change -= 0.001
                elif current_price < base_price * 0.5:
                    change += 0.001
                current_price *= (1 + change)
                price_series.append(current_price)
            
            # Create DataFrame
            df = pd.DataFrame({
                'Open': price_series,
                'Close': [p * (1 + np.random.normal(0, volatility/3)) for p in price_series],
                'High': [max(o, c) * (1 + abs(np.random.normal(0, volatility/2))) 
                        for o, c in zip(price_series, [p * (1 + np.random.normal(0, volatility/3)) for p in price_series])],
                'Low': [min(o, c) * (1 - abs(np.random.normal(0, volatility/2))) 
                       for o, c in zip(price_series, [p * (1 + np.random.normal(0, volatility/3)) for p in price_series])],
                'Volume': [int(np.random.normal(base_price * 100000, base_price * 20000)) for _ in range(len(dates))]
            }, index=dates)
            
            # Ensure High is always >= Open and Close
            df['High'] = df[['Open', 'Close', 'High']].max(axis=1)
            
            # Ensure Low is always <= Open and Close
            df['Low'] = df[['Open', 'Close', 'Low']].min(axis=1)
            
            # Ensure Volume is always positive
            df['Volume'] = df['Volume'].abs()
            
            logger.info(f"Generated {len(df)} records of sample data for {ticker}")
            
            if df is None or df.empty:
                logger.warning(f"No data available for {ticker}")
                continue
                
            # Calculate features
            features_df = feature_engineer.add_technical_indicators(df)
            
            if features_df is None or features_df.empty:
                logger.warning(f"No features calculated for {ticker}")
                continue
                
            # Prepare features
            features_result = feature_engineer.prepare_features(features_df)
            
            if features_result is None or features_result[0] is None:
                logger.warning(f"No valid features prepared for {ticker}")
                continue
                
            # Extract features and feature names from the result
            X_features, feature_names = features_result
            
            # Create a DataFrame with the features
            X = pd.DataFrame(X_features, index=features_df.index, columns=feature_names)
            
            # Create target variable (future 5-day return)
            features_df['future_return'] = features_df['Close'].pct_change(5).shift(-5)
            
            # Create rating categories based on future return
            def create_rating(return_value):
                if pd.isna(return_value):
                    return None
                if return_value > 0.05:
                    return 'Strong Buy'
                elif return_value > 0.02:
                    return 'Buy'
                elif return_value > -0.02:
                    return 'Hold'
                elif return_value > -0.05:
                    return 'Sell'
                else:
                    return 'Strong Sell'
            
            features_df['rating'] = features_df['future_return'].apply(create_rating)
            
            # Drop rows with NaN in target
            features_df = features_df.dropna()
            
            if features_df.empty:
                logger.warning(f"No valid data after creating target for {ticker}")
                continue
            
            # Ensure X and y have the same index
            X = X.loc[features_df.index]
            
            # Separate features and target
            y = features_df['rating']
            
            # Add to our collections
            all_features.append(X)
            all_targets.append(y)
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
    
    # Combine data from all tickers
    if not all_features:
        logger.error("No valid data collected for any ticker")
        return None, None, None, None
        
    X_combined = pd.concat(all_features, axis=0)
    y_combined = pd.concat(all_targets, axis=0)
    
    logger.info(f"Combined dataset: {X_combined.shape[0]} samples with {X_combined.shape[1]} features")
    
    # Split into training and testing sets
    from sklearn.model_selection import train_test_split
    X_train, X_test, y_train, y_test = train_test_split(
        X_combined, y_combined, test_size=test_size, random_state=42, stratify=y_combined
    )
    
    return X_train, X_test, y_train, y_test

def train_and_evaluate_models(X_train, X_test, y_train, y_test):
    """
    Train and evaluate both models.
    
    Args:
        X_train, X_test, y_train, y_test: Training and testing data
        
    Returns:
        dict: Dictionary containing evaluation results for both models
    """
    results = {}
    
    # Train and evaluate Random Forest model
    logger.info("Training Random Forest model")
    rf_model = StockRatingPredictor()
    rf_model.train(X_train, y_train)
    
    # Evaluate Random Forest
    rf_pred = rf_model.model.predict(X_test)
    rf_accuracy = accuracy_score(y_test, rf_pred)
    rf_report = classification_report(y_test, rf_pred, output_dict=True)
    rf_cm = confusion_matrix(y_test, rf_pred)
    
    # Get feature importance for Random Forest
    rf_importance = pd.Series(
        rf_model.model.feature_importances_,
        index=X_train.columns
    ).sort_values(ascending=False)
    
    results['random_forest'] = {
        'accuracy': rf_accuracy,
        'classification_report': rf_report,
        'confusion_matrix': rf_cm,
        'feature_importance': rf_importance,
        'predictions': rf_pred
    }
    
    # Train and evaluate XGBoost model
    logger.info("Training XGBoost model")
    xgb_model = XGBoostRatingPredictor()
    xgb_model.train(X_train, y_train)
    
    # Evaluate XGBoost
    xgb_pred = xgb_model.model.predict(X_test)
    xgb_accuracy = accuracy_score(y_test, xgb_pred)
    xgb_report = classification_report(y_test, xgb_pred, output_dict=True)
    xgb_cm = confusion_matrix(y_test, xgb_pred)
    
    # Get feature importance for XGBoost
    xgb_importance = xgb_model.feature_importance
    
    results['xgboost'] = {
        'accuracy': xgb_accuracy,
        'classification_report': xgb_report,
        'confusion_matrix': xgb_cm,
        'feature_importance': xgb_importance,
        'predictions': xgb_pred
    }
    
    return results

def plot_comparison(results, output_dir):
    """
    Create comparison plots and save them.
    
    Args:
        results (dict): Dictionary containing evaluation results
        output_dir (str): Directory to save plots
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Plot accuracy comparison
    plt.figure(figsize=(10, 6))
    accuracies = [results['random_forest']['accuracy'], results['xgboost']['accuracy']]
    plt.bar(['Random Forest', 'XGBoost'], accuracies, color=['blue', 'green'])
    plt.title('Model Accuracy Comparison')
    plt.ylabel('Accuracy')
    plt.ylim(0, 1)
    for i, v in enumerate(accuracies):
        plt.text(i, v + 0.01, f"{v:.4f}", ha='center')
    plt.savefig(os.path.join(output_dir, 'accuracy_comparison.png'))
    
    # Plot feature importance comparison (top 10 features)
    plt.figure(figsize=(12, 8))
    
    # Get top 10 features from each model
    rf_top10 = results['random_forest']['feature_importance'].head(10)
    xgb_top10 = results['xgboost']['feature_importance'].head(10)
    
    # Combine and get unique features
    all_features = pd.concat([rf_top10, xgb_top10])
    unique_features = all_features.index.unique()
    
    # Create a DataFrame with importance from both models
    comparison_df = pd.DataFrame(index=unique_features, columns=['Random Forest', 'XGBoost'])
    
    for feature in unique_features:
        if feature in rf_top10.index:
            comparison_df.loc[feature, 'Random Forest'] = rf_top10[feature]
        else:
            comparison_df.loc[feature, 'Random Forest'] = 0
            
        if feature in xgb_top10.index:
            comparison_df.loc[feature, 'XGBoost'] = xgb_top10[feature]
        else:
            comparison_df.loc[feature, 'XGBoost'] = 0
    
    # Sort by average importance
    comparison_df['Average'] = comparison_df.mean(axis=1)
    comparison_df = comparison_df.sort_values('Average', ascending=False).drop('Average', axis=1)
    
    # Plot
    comparison_df.plot(kind='bar', figsize=(12, 8))
    plt.title('Top Feature Importance Comparison')
    plt.ylabel('Importance Score')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'feature_importance_comparison.png'))
    
    # Plot confusion matrices
    class_names = np.unique(np.concatenate([
        results['random_forest']['confusion_matrix'],
        results['xgboost']['confusion_matrix']
    ]))
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    
    # Random Forest confusion matrix
    rf_cm = results['random_forest']['confusion_matrix']
    im = axes[0].imshow(rf_cm, interpolation='nearest', cmap=plt.cm.Blues)
    axes[0].set_title('Random Forest Confusion Matrix')
    fig.colorbar(im, ax=axes[0])
    tick_marks = np.arange(len(class_names))
    axes[0].set_xticks(tick_marks)
    axes[0].set_yticks(tick_marks)
    axes[0].set_xticklabels(class_names, rotation=45, ha='right')
    axes[0].set_yticklabels(class_names)
    
    # Add text annotations
    thresh = rf_cm.max() / 2
    for i in range(rf_cm.shape[0]):
        for j in range(rf_cm.shape[1]):
            axes[0].text(j, i, format(rf_cm[i, j], 'd'),
                         ha="center", va="center",
                         color="white" if rf_cm[i, j] > thresh else "black")
    
    # XGBoost confusion matrix
    xgb_cm = results['xgboost']['confusion_matrix']
    im = axes[1].imshow(xgb_cm, interpolation='nearest', cmap=plt.cm.Blues)
    axes[1].set_title('XGBoost Confusion Matrix')
    fig.colorbar(im, ax=axes[1])
    axes[1].set_xticks(tick_marks)
    axes[1].set_yticks(tick_marks)
    axes[1].set_xticklabels(class_names, rotation=45, ha='right')
    axes[1].set_yticklabels(class_names)
    
    # Add text annotations
    thresh = xgb_cm.max() / 2
    for i in range(xgb_cm.shape[0]):
        for j in range(xgb_cm.shape[1]):
            axes[1].text(j, i, format(xgb_cm[i, j], 'd'),
                         ha="center", va="center",
                         color="white" if xgb_cm[i, j] > thresh else "black")
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'confusion_matrix_comparison.png'))
    
    # Save classification reports
    with open(os.path.join(output_dir, 'classification_report.txt'), 'w') as f:
        f.write("Random Forest Classification Report:\n")
        f.write(classification_report(y_test, results['random_forest']['predictions']))
        f.write("\n\nXGBoost Classification Report:\n")
        f.write(classification_report(y_test, results['xgboost']['predictions']))

def save_results(results, output_dir):
    """
    Save detailed results to files.
    
    Args:
        results (dict): Dictionary containing evaluation results
        output_dir (str): Directory to save results
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Save summary to CSV
    summary = pd.DataFrame({
        'Model': ['Random Forest', 'XGBoost'],
        'Accuracy': [results['random_forest']['accuracy'], results['xgboost']['accuracy']]
    })
    
    # Add class-specific metrics
    for model_name in ['random_forest', 'xgboost']:
        report = results[model_name]['classification_report']
        for class_name in report.keys():
            if class_name not in ['accuracy', 'macro avg', 'weighted avg']:
                for metric in ['precision', 'recall', 'f1-score']:
                    col_name = f"{class_name}_{metric}"
                    if col_name not in summary.columns:
                        summary[col_name] = None
                    idx = 0 if model_name == 'random_forest' else 1
                    summary.loc[idx, col_name] = report[class_name][metric]
    
    summary.to_csv(os.path.join(output_dir, 'model_comparison_summary.csv'), index=False)
    
    # Save feature importance
    rf_importance = results['random_forest']['feature_importance']
    xgb_importance = results['xgboost']['feature_importance']
    
    rf_importance.to_csv(os.path.join(output_dir, 'random_forest_feature_importance.csv'))
    xgb_importance.to_csv(os.path.join(output_dir, 'xgboost_feature_importance.csv'))
    
    # Save a timestamp file
    with open(os.path.join(output_dir, 'comparison_timestamp.txt'), 'w') as f:
        f.write(f"Comparison run at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Random Forest accuracy: {results['random_forest']['accuracy']:.4f}\n")
        f.write(f"XGBoost accuracy: {results['xgboost']['accuracy']:.4f}\n")
        
        # Calculate improvement
        improvement = (results['xgboost']['accuracy'] - results['random_forest']['accuracy']) / results['random_forest']['accuracy'] * 100
        f.write(f"Improvement: {improvement:.2f}%\n")

if __name__ == "__main__":
    args = parse_args()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Parse tickers
    tickers = [ticker.strip() for ticker in args.tickers.split(',')]
    
    # Prepare data
    X_train, X_test, y_train, y_test = prepare_data(tickers, args.period, args.test_size)
    
    if X_train is None:
        logger.error("Failed to prepare data. Exiting.")
        sys.exit(1)
    
    # Train and evaluate models
    results = train_and_evaluate_models(X_train, X_test, y_train, y_test)
    
    # Plot comparison
    plot_comparison(results, args.output_dir)
    
    # Save detailed results
    save_results(results, args.output_dir)
    
    # Print summary
    logger.info("Model Comparison Summary:")
    logger.info(f"Random Forest accuracy: {results['random_forest']['accuracy']:.4f}")
    logger.info(f"XGBoost accuracy: {results['xgboost']['accuracy']:.4f}")
    
    improvement = (results['xgboost']['accuracy'] - results['random_forest']['accuracy']) / results['random_forest']['accuracy'] * 100
    logger.info(f"Improvement: {improvement:.2f}%")
    
    logger.info(f"Detailed results saved to {args.output_dir}") 