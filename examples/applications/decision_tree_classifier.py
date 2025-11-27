#!/usr/bin/env python3
"""
Decision Tree Classifier

This application trains a decision tree classifier to predict categorical
targets from input features in a CSV dataset.

Reads CSV from stdin and outputs JSON results to stdout.
"""

import sys
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier, export_text
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import json
from datetime import datetime

def train_decision_tree(df, target_column=None, feature_columns=None, max_depth=None):
    """
    Train a decision tree classifier on the provided dataset.
    
    Args:
        df: pandas DataFrame with the dataset
        target_column: Name of the target column (default: last column)
        feature_columns: List of feature columns (default: all numeric except target)
        max_depth: Maximum depth of the tree (default: None for unlimited)
    
    Returns:
        Dictionary with model metrics and results
    """
    # Determine target column
    if target_column is None:
        # Use last column as target
        target_column = df.columns[-1]
    
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
    
    # Get unique classes
    unique_classes = np.unique(y)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Train model
    import time
    start_time = time.time()
    model = DecisionTreeClassifier(max_depth=max_depth, random_state=42)
    model.fit(X_train, y_train)
    training_time = time.time() - start_time
    
    # Make predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Calculate metrics
    train_accuracy = accuracy_score(y_train, y_train_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    # Classification report
    train_report = classification_report(y_train, y_train_pred, output_dict=True, zero_division=0)
    test_report = classification_report(y_test, y_test_pred, output_dict=True, zero_division=0)
    
    # Confusion matrix
    train_cm = confusion_matrix(y_train, y_train_pred).tolist()
    test_cm = confusion_matrix(y_test, y_test_pred).tolist()
    
    # Feature importance
    feature_importance = {feature_columns[i]: float(model.feature_importances_[i]) 
                        for i in range(len(feature_columns))}
    sorted_importance = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)
    
    # Generate insights
    top_feature = sorted_importance[0][0] if sorted_importance else None
    insights = []
    if top_feature:
        insights.append(f"{top_feature} is the most important feature (importance: {feature_importance[top_feature]:.4f})")
    insights.append(f"Model achieved {test_accuracy*100:.2f}% accuracy on test set")
    insights.append(f"Tree depth: {model.get_depth()}, leaves: {model.get_n_leaves()}")
    
    # Sample predictions
    sample_predictions = []
    for i in range(min(10, len(y_test))):
        sample_predictions.append({
            "actual": str(y_test[i]),
            "predicted": str(y_test_pred[i]),
            "correct": bool(y_test[i] == y_test_pred[i])
        })
    
    # Get tree structure (simplified representation)
    tree_rules = export_text(model, feature_names=feature_columns, max_depth=3)
    
    # Prepare results
    results = {
        "status": "success",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "application": {
            "name": "Decision Tree Classifier",
            "version": "1.0.0",
            "algorithm": "decision_tree"
        },
        "dataset": {
            "rows": int(df.shape[0]),
            "columns": int(df.shape[1]),
            "column_names": list(df.columns)
        },
        "learning": {
            "model_type": "Decision Tree Classifier",
            "target_variable": target_column,
            "features_used": feature_columns,
            "classes": [str(c) for c in unique_classes],
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
            "model_performance": {
                "train": {
                    "accuracy": float(train_accuracy),
                    "classification_report": train_report
                },
                "test": {
                    "accuracy": float(test_accuracy),
                    "classification_report": test_report
                }
            },
            "model_parameters": {
                "max_depth": int(model.get_depth()) if max_depth is None else max_depth,
                "n_leaves": int(model.get_n_leaves()),
                "feature_importance": feature_importance,
                "full_tree_structure": tree_rules
            },
            "confusion_matrices": {
                "train": {
                    "matrix": train_cm,
                    "classes": [str(c) for c in unique_classes]
                },
                "test": {
                    "matrix": test_cm,
                    "classes": [str(c) for c in unique_classes]
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
        results = train_decision_tree(df)
        
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
