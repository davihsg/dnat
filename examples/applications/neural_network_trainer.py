#!/usr/bin/env python3
"""
Neural Network (MLP) Trainer

This application trains a multi-layer perceptron (MLP) neural network
to predict a target variable from input features in a CSV dataset.

Reads CSV from stdin and outputs JSON results to stdout.
"""

import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor, MLPClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, accuracy_score, classification_report
import json
from datetime import datetime

def train_neural_network(df, target_column=None, feature_columns=None, 
                         hidden_layers=(64, 32), is_classification=False):
    """
    Train a neural network (MLP) on the provided dataset.
    
    Args:
        df: pandas DataFrame with the dataset
        target_column: Name of the target column (default: last column)
        feature_columns: List of feature columns (default: all numeric except target)
        hidden_layers: Tuple of hidden layer sizes (default: (64, 32))
        is_classification: Whether to use classification (default: False for regression)
    
    Returns:
        Dictionary with model metrics and results
    """
    # Determine target column
    if target_column is None:
        # Use last numeric column as target for regression, last column for classification
        if is_classification:
            target_column = df.columns[-1]
        else:
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
    
    # Auto-detect classification if target is not numeric
    if not is_classification and not pd.api.types.is_numeric_dtype(df[target_column]):
        is_classification = True
    
    # Get unique classes for classification
    if is_classification:
        unique_classes = np.unique(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, 
        stratify=y if is_classification else None
    )
    
    # Scale features (important for neural networks)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Parse hidden layers
    if isinstance(hidden_layers, str):
        hidden_layers = tuple(int(x.strip()) for x in hidden_layers.split(','))
    
    # Train model
    import time
    start_time = time.time()
    if is_classification:
        model = MLPClassifier(
            hidden_layer_sizes=hidden_layers,
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
    else:
        model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            max_iter=500,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.1
        )
    
    model.fit(X_train_scaled, y_train)
    training_time = time.time() - start_time
    
    # Make predictions
    y_train_pred = model.predict(X_train_scaled)
    y_test_pred = model.predict(X_test_scaled)
    
    # Calculate metrics
    if is_classification:
        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        train_report = classification_report(y_train, y_train_pred, output_dict=True, zero_division=0)
        test_report = classification_report(y_test, y_test_pred, output_dict=True, zero_division=0)
        
        metrics = {
            "train": {
                "accuracy": float(train_accuracy),
                "classification_report": train_report
            },
            "test": {
                "accuracy": float(test_accuracy),
                "classification_report": test_report
            }
        }
    else:
        train_mse = mean_squared_error(y_train, y_train_pred)
        test_mse = mean_squared_error(y_test, y_test_pred)
        train_rmse = np.sqrt(train_mse)
        test_rmse = np.sqrt(test_mse)
        train_mae = mean_absolute_error(y_train, y_train_pred)
        test_mae = mean_absolute_error(y_test, y_test_pred)
        train_r2 = r2_score(y_train, y_train_pred)
        test_r2 = r2_score(y_test, y_test_pred)
        
        metrics = {
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
        }
    
    # Generate insights
    insights = []
    if is_classification:
        insights.append(f"Model achieved {test_accuracy*100:.2f}% accuracy on test set")
    else:
        insights.append(f"Model explains {metrics['test']['r2_score']*100:.2f}% of variance")
        if test_rmse < train_rmse * 1.2:
            insights.append("Model generalizes well")
        else:
            insights.append("Model may be overfitting")
    insights.append(f"Network architecture: {len(feature_columns)} inputs -> {hidden_layers} -> {1 if not is_classification else len(unique_classes)} outputs")
    insights.append(f"Training converged after {model.n_iter_} iterations")
    
    # Sample predictions
    sample_predictions = []
    for i in range(min(10, len(y_test))):
        if is_classification:
            sample_predictions.append({
                "actual": str(y_test[i]),
                "predicted": str(y_test_pred[i]),
                "correct": bool(y_test[i] == y_test_pred[i])
            })
        else:
            sample_predictions.append({
                "actual": float(y_test[i]),
                "predicted": float(y_test_pred[i]),
                "error": float(abs(y_test[i] - y_test_pred[i]))
            })
    
    # Extract full model weights
    # MLP stores weights as list of arrays (one per layer)
    full_weights = {
        "layers": []
    }
    for i, (coef, intercept) in enumerate(zip(model.coefs_, model.intercepts_)):
        full_weights["layers"].append({
            "layer_index": i,
            "weights": coef.tolist(),
            "biases": intercept.tolist(),
            "shape": list(coef.shape)
        })
    
    # Prepare results
    results = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "application": {
            "name": "Neural Network (MLP) Trainer",
            "version": "1.0.0",
            "algorithm": "neural_network"
        },
        "dataset": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": list(df.columns)
        },
        "learning": {
            "model_type": "Neural Network (MLP)",
            "task_type": "Classification" if is_classification else "Regression",
            "target_variable": target_column,
            "features_used": feature_columns,
            "insights": {
                "key_findings": insights
            },
            "model_performance": metrics,
            "model_parameters": {
                "hidden_layers": list(hidden_layers),
                "n_iterations": int(model.n_iter_),
                "loss_curve": model.loss_curve_.tolist() if hasattr(model, 'loss_curve_') else None,
                "full_weights": full_weights
            },
            "sample_predictions": sample_predictions
        },
        "execution": {
            "training_time_seconds": float(training_time),
            "samples_trained": int(X_train.shape[0]),
            "samples_tested": int(X_test.shape[0])
        }
    }
    
    if is_classification:
        results["learning"]["classes"] = [str(c) for c in unique_classes]
    
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
        
        # Train model (auto-detect target and features, default to regression)
        results = train_neural_network(df)
        
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
