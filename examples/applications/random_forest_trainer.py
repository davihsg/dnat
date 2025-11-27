#!/usr/bin/env python3
"""
Random Forest Trainer

This application trains a random forest model (regressor or classifier)
to predict targets from input features in a CSV dataset.

Reads CSV from stdin and outputs JSON results to stdout.
"""

import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, accuracy_score, classification_report
import json
from datetime import datetime

def train_random_forest(df, target_column=None, feature_columns=None, 
                       n_estimators=100, is_classification=False):
    """
    Train a random forest model on the provided dataset.
    
    Args:
        df: pandas DataFrame with the dataset
        target_column: Name of the target column (default: last column)
        feature_columns: List of feature columns (default: all numeric except target)
        n_estimators: Number of trees in the forest (default: 100)
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
    
    # Train model
    import time
    start_time = time.time()
    if is_classification:
        model = RandomForestClassifier(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    else:
        model = RandomForestRegressor(n_estimators=n_estimators, random_state=42, n_jobs=-1)
    
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    
    # Make predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
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
    
    # Feature importance
    feature_importance = {feature_columns[i]: float(model.feature_importances_[i]) 
                        for i in range(len(feature_columns))}
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    # Generate insights
    top_feature = sorted_importance[0][0] if sorted_importance else None
    insights = []
    if top_feature:
        insights.append(f"{top_feature} is the most important feature (importance: {feature_importance[top_feature]:.4f})")
    if is_classification:
        insights.append(f"Model achieved {test_accuracy*100:.2f}% accuracy on test set")
    else:
        insights.append(f"Model explains {metrics['test']['r2_score']*100:.2f}% of variance")
    insights.append(f"Ensemble of {n_estimators} decision trees")
    
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
    
    # Extract full model weights (all tree structures)
    # For random forest, we store feature importances and tree structures
    full_weights = {
        "n_estimators": n_estimators,
        "feature_importances": feature_importance,
        "trees": []
    }
    
    # Store tree structures (simplified - just depth and leaf counts for each tree)
    for i, tree in enumerate(model.estimators_):
        full_weights["trees"].append({
            "tree_index": i,
            "max_depth": int(tree.tree_.max_depth),
            "n_leaves": int(tree.tree_.n_leaves),
            "n_nodes": int(tree.tree_.node_count)
        })
    
    # Prepare results
    results = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "application": {
            "name": "Random Forest Trainer",
            "version": "1.0.0",
            "algorithm": "random_forest"
        },
        "dataset": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": list(df.columns)
        },
        "learning": {
            "model_type": "Random Forest",
            "task_type": "Classification" if is_classification else "Regression",
            "target_variable": target_column,
            "features_used": feature_columns,
            "insights": {
                "key_findings": insights,
                "feature_importance": {k: v for k, v in sorted_importance},
                "feature_relationships": {
                    feat: {
                        "importance": feature_importance[feat],
                        "importance_rank": idx + 1
                    }
                    for idx, (feat, _) in enumerate(sorted_importance)
                }
            },
            "model_performance": metrics,
            "model_parameters": {
                "n_estimators": n_estimators,
                "feature_importance": feature_importance,
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
        results = train_random_forest(df)
        
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
