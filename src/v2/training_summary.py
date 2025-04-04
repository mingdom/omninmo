"""
Functions for generating and saving training summaries
"""

import json
import logging
import os
from datetime import datetime

import matplotlib.pyplot as plt
import mlflow
import numpy as np
import pandas as pd
import shap

logger = logging.getLogger(__name__)

# Get the project root directory
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
MLRUNS_DIR = os.path.join(project_root, 'logs/mlruns')

def generate_training_summary(predictor, cv_results, training_results, processed_tickers, skipped_tickers, error_tickers):
    """
    Generate an executive summary of the training results

    Args:
        predictor: The trained Predictor instance
        cv_results: Results from cross-validation
        training_results: Results from final training
        processed_tickers: List of successfully processed tickers
        skipped_tickers: List of skipped tickers
        error_tickers: List of tickers that had errors

    Returns:
        dict: Summary of training results
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    summary = {
        "timestamp": timestamp,
        "mode": "regression",
        "data_coverage": {
            "processed_tickers": len(processed_tickers),
            "skipped_tickers": len(skipped_tickers),
            "error_tickers": len(error_tickers),
            "total_tickers": len(processed_tickers) + len(skipped_tickers) + len(error_tickers)
        },
        "model_params": {
            "learning_rate": predictor.learning_rate,
            "max_depth": predictor.max_depth,
            "n_estimators": predictor.n_estimators
        }
    }

    # Add metrics (regression only)
    summary["cross_validation"] = {
        "rmse": {
            "mean": float(cv_results['mean_rmse']),
            "std": float(cv_results['std_rmse'])
        },
        "r2": {
            "mean": float(cv_results['mean_r2']),
            "std": float(cv_results['std_r2'])
        },
        "mae": {
            "mean": float(cv_results['mean_mae']),
            "std": float(cv_results['std_mae'])
        }
    }
    summary["final_model"] = {
        "rmse": float(training_results['rmse']),
        "r2": float(training_results['r2']),
        "mae": float(training_results['mae'])
    }

    # Add feature importance analysis
    feature_importance = pd.Series(training_results['feature_importance'])
    top_features = feature_importance.nlargest(10)

    summary["feature_analysis"] = {
        "stability_score": float(cv_results['feature_stability']),
        "top_features": {
            name: float(importance)
            for name, importance in top_features.items()
        },
        "cumulative_importance": float(top_features.sum())
    }

    return summary

def save_training_summary(summary, base_dir="logs/training"):
    """
    Save the training summary to a JSON file

    Args:
        summary (dict): The training summary
        base_dir (str): Directory to save summaries

    Returns:
        str: Path to the saved summary file
    """
    # Create directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)

    # Generate filename with timestamp
    filename = f"training_summary_{summary['timestamp']}.json"
    filepath = os.path.join(base_dir, filename)

    # Save summary
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2)

    logger.info(f"\nTraining summary saved to: {filepath}")

    # Print executive summary to console


    for _i, (_feature, _importance) in enumerate(list(summary['feature_analysis']['top_features'].items())[:5], 1):
        pass

    return filepath

def log_mlflow_metrics(predictor, cv_results, training_results, X_data, processed_tickers, skipped_tickers, error_tickers, model_path):
    """
    Log metrics, parameters, and artifacts to MLflow

    Args:
        predictor: The trained Predictor instance
        cv_results: Results from cross-validation
        training_results: Results from final training
        X_data: Feature data used for training
        processed_tickers: List of successfully processed tickers
        skipped_tickers: List of skipped tickers
        error_tickers: List of tickers that had errors
        model_path: Path where the model is saved

    Returns:
        str: MLflow run ID
    """
    # Get the project root directory and set up MLflow tracking
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    mlruns_dir = os.path.join(project_root, 'mlruns')
    tracking_uri = f"file:{mlruns_dir}"

    if os.path.exists(mlruns_dir):
        # Clean up any malformed experiments
        for exp_dir in os.listdir(mlruns_dir):
            exp_path = os.path.join(mlruns_dir, exp_dir)
            meta_path = os.path.join(exp_path, "meta.yaml")
            if not os.path.exists(meta_path) and exp_dir != ".trash":
                logger.warning(f"Removing malformed experiment directory: {exp_dir}")
                import shutil
                shutil.rmtree(exp_path, ignore_errors=True)

    mlflow.set_tracking_uri(tracking_uri)

    # Create experiment if it doesn't exist
    experiment_name = "stock_prediction"
    try:
        experiment = mlflow.get_experiment_by_name(experiment_name)
        if experiment is None:
            logger.info(f"Creating new experiment: {experiment_name}")
            experiment_id = mlflow.create_experiment(experiment_name)
        else:
            experiment_id = experiment.experiment_id
    except Exception as e:
        logger.warning(f"Error accessing experiment, creating new one: {e!s}")
        # Force create new experiment
        try:
            experiment_id = mlflow.create_experiment(experiment_name)
        except Exception as e2:
            logger.error(f"Failed to create experiment: {e2!s}")
            raise

    # Start a new MLflow run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_name = f"model_training_{timestamp}"

    with mlflow.start_run(run_name=run_name, experiment_id=experiment_id) as run:
        # Log basic parameters
        mlflow.log_params({
            "mode": "regression",
            "learning_rate": predictor.learning_rate,
            "max_depth": predictor.max_depth,
            "n_estimators": predictor.n_estimators,
            "processed_tickers_count": len(processed_tickers),
            "skipped_tickers_count": len(skipped_tickers),
            "error_tickers_count": len(error_tickers),
            "total_samples": X_data.shape[0],
            "feature_count": X_data.shape[1]
        })

        # Log processed tickers as a list
        mlflow.log_param("processed_tickers", ", ".join(processed_tickers))

        # Log metrics
        mlflow.log_metrics({
            "cv_rmse_mean": cv_results['mean_rmse'],
            "cv_rmse_std": cv_results['std_rmse'],
            "cv_r2_mean": cv_results['mean_r2'],
            "cv_r2_std": cv_results['std_r2'],
            "cv_mae_mean": cv_results['mean_mae'],
            "cv_mae_std": cv_results['std_mae'],
            "final_rmse": training_results['rmse'],
            "final_r2": training_results['r2'],
            "final_mae": training_results['mae'],
            "feature_stability": cv_results['feature_stability']
        })

        # Create model signature and input example
        input_example = X_data.head(5).copy()  # Create explicit copy

        # Convert integer columns to float64 to handle potential missing values
        input_schema = {}
        for col in X_data.columns:
            if X_data[col].dtype.kind in 'iu':  # integer types
                input_schema[col] = np.float64
                input_example.loc[:, col] = input_example[col].astype(np.float64)

        if input_schema:
            X_data = X_data.astype(input_schema)

        signature = mlflow.models.infer_signature(
            model_input=X_data,
            model_output=predictor.model.predict(X_data[:5])
        )

        # Log the model with signature and input example
        mlflow.sklearn.log_model(
            predictor.model,
            "model",
            signature=signature,
            input_example=input_example
        )

        # Generate and log feature importance plot
        try:
            plt.figure(figsize=(10, 6))
            feature_importance = pd.Series(training_results['feature_importance'])
            top_features = feature_importance.nlargest(15).sort_values(ascending=True)

            top_features.plot(kind='barh', title='Feature Importance')
            plt.tight_layout()

            # Save and log the plot
            importance_plot_path = "feature_importance.png"
            plt.savefig(importance_plot_path)
            mlflow.log_artifact(importance_plot_path)
            os.remove(importance_plot_path)  # Clean up

            # Generate SHAP summary plot if possible
            try:
                # Create SHAP explainer
                explainer = shap.Explainer(predictor.model)

                # Calculate SHAP values (limit to 1000 samples if dataset is large)
                sample_size = min(1000, X_data.shape[0])
                X_sample = X_data.sample(sample_size) if X_data.shape[0] > sample_size else X_data

                # Calculate SHAP values
                shap_values = explainer(X_sample)

                # Create summary plot
                plt.figure(figsize=(10, 8))
                shap.summary_plot(shap_values, X_sample, show=False)
                plt.tight_layout()

                # Save and log the plot
                shap_plot_path = "shap_summary.png"
                plt.savefig(shap_plot_path)
                mlflow.log_artifact(shap_plot_path)
                os.remove(shap_plot_path)  # Clean up

                # Create and log SHAP dependence plots for top 3 features
                top_feature_names = list(top_features.index)[-3:]
                for feature in top_feature_names:
                    if feature in X_sample.columns:
                        plt.figure(figsize=(10, 6))
                        feature_idx = list(X_sample.columns).index(feature)
                        shap.dependence_plot(feature_idx, shap_values.values, X_sample, show=False)
                        plt.tight_layout()

                        # Save and log the plot
                        dep_plot_path = f"shap_dependence_{feature}.png"
                        plt.savefig(dep_plot_path)
                        mlflow.log_artifact(dep_plot_path)
                        os.remove(dep_plot_path)  # Clean up

            except Exception as e:
                logger.warning(f"Could not generate SHAP plots: {e}")

        except Exception as e:
            logger.warning(f"Could not generate feature importance plot: {e}")

        # Log the model file as an artifact
        if os.path.exists(model_path):
            mlflow.log_artifact(model_path)

        # Print MLflow tracking info

        return run.info.run_id
