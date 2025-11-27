#!/usr/bin/env python3
"""
Linear Regression Model Trainer

This application trains a linear regression model to predict a target variable
from input features in a CSV dataset.

Reads CSV from stdin and outputs JSON results to stdout.
"""

import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import json
from datetime import datetime

def train_linear_regression(df, target_column=None, feature_columns=None):
    """
    Train a linear regression model on the provided dataset.
    
    Args:
        df: pandas DataFrame with the dataset
        target_column: Name of the target column (default: last numeric column)
        feature_columns: List of feature columns (default: all numeric except target)
    
    Returns:
        Dictionary with model metrics and results
    """
    # Load dataset from stdin
    try:
        if df is None:
            df = pd.read_csv(sys.stdin)
    except Exception as e:
        raise ValueError(f"Failed to read CSV from stdin: {e}")
    
    # Determine target column
    if target_column is None:
        # Use last numeric column as target
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        if len(numeric_cols) > 0:
            target_column = numeric_cols[-1]
        else:
            raise ValueError("No numeric columns found for target variable")
    
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in dataset")
    
    # Determine feature columns
    if feature_columns is None:
        # Use all numeric columns except target
        feature_columns = [col for col in df.select_dtypes(include=[np.number]).columns 
                         if col != target_column]
    
    # Validate feature columns
    for col in feature_columns:
        if col not in df.columns:
            raise ValueError(f"Feature column '{col}' not found in dataset")
    
    # Prepare data
    X = df[feature_columns].values
    y = df[target_column].values
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Train model
    import time
    start_time = time.time()
    model = LinearRegression()
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    
    # Make predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Calculate metrics
    train_mse = mean_squared_error(y_train, y_train_pred)
    test_mse = mean_squared_error(y_test, y_test_pred)
    train_rmse = np.sqrt(train_mse)
    test_rmse = np.sqrt(test_mse)
    train_mae = mean_absolute_error(y_train, y_train_pred)
    test_mae = mean_absolute_error(y_test, y_test_pred)
    train_r2 = r2_score(y_train, y_train_pred)
    test_r2 = r2_score(y_test, y_test_pred)
    
    # Model coefficients (full weights)
    coefficients = {feature_columns[i]: float(model.coef_[i]) for i in range(len(feature_columns))}
    intercept = float(model.intercept_)
    
    # Calculate feature importance (absolute coefficient values)
    feature_importance = {feature_columns[i]: abs(float(model.coef_[i])) 
                         for i in range(len(feature_columns))}
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    # Generate insights
    top_feature = sorted_importance[0][0] if sorted_importance else None
    insights = []
    if top_feature:
        insights.append(f"{top_feature} has the strongest influence (coefficient: {coefficients[top_feature]:.4f})")
    insights.append(f"Model explains {test_r2*100:.2f}% of variance in {target_column}")
    if test_rmse < train_rmse * 1.2:
        insights.append("Model generalizes well (test RMSE close to training RMSE)")
    else:
        insights.append("Model may be overfitting (test RMSE significantly higher than training)")
    
    # Sample predictions with errors
    sample_predictions = []
    for i in range(min(10, len(y_test))):
        sample_predictions.append({
            "actual": float(y_test[i]),
            "predicted": float(y_test_pred[i]),
            "error": float(abs(y_test[i] - y_test_pred[i]))
        })
    
    # Prepare results
    results = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "application": {
            "name": "Linear Regression Trainer",
            "version": "1.0.0",
            "algorithm": "linear_regression"
        },
        "dataset": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": list(df.columns)
        },
        "learning": {
            "model_type": "Linear Regression",
            "target_variable": target_column,
            "features_used": feature_columns,
            "insights": {
                "key_findings": insights,
                "feature_importance": {k: v for k, v in sorted_importance},
                "feature_relationships": {
                    feat: {
                        "coefficient": coefficients[feat],
                        "importance_rank": idx + 1
                    }
                    for idx, (feat, _) in enumerate(sorted_importance)
                }
            },
            "model_performance": {
                "train": {
                    "mse": float(train_mse),
                    "rmse": float(train_rmse),
                    "mae": float(train_mae),
                    "r2_score": float(train_r2)
                },
                "test": {
                    "mse": float(test_mse),
                    "rmse": float(test_rmse),
                    "mae": float(test_mae),
                    "r2_score": float(test_r2)
                }
            },
            "model_parameters": {
                "coefficients": coefficients,
                "intercept": intercept,
                "full_weights": {
                    "coef": [float(c) for c in model.coef_],
                    "intercept": float(model.intercept_),
                    "feature_names": feature_columns
                }
            },
            "sample_predictions": sample_predictions
        },
        "execution": {
            "training_time_seconds": float(training_time),
            "samples_trained": int(X_train.shape[0]),
            "samples_tested": int(X_test.shape[0])
        }
    }
    
    return results

def main():
    try:
        # Read CSV from stdin
        df = pd.read_csv(sys.stdin)
        
        if df.empty:
            error_result = {
                "status": "error",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "error": {
                    "type": "EmptyDataset",
                    "message": "Dataset is empty"
                }
            }
            print(json.dumps(error_result, indent=2))
            sys.exit(1)
        
        # Train model (auto-detect target and features)
        results = train_linear_regression(df)
        
        # Output JSON to stdout
        print(json.dumps(results, indent=2))
        
    except pd.errors.EmptyDataError:
        error_result = {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": {
                "type": "EmptyDataError",
                "message": "CSV file is empty or invalid"
            }
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)
    except Exception as e:
        error_result = {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "error": {
                "type": type(e).__name__,
                "message": str(e)
            }
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()

