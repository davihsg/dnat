# Sample ML Applications

This directory contains sample Python applications that train machine learning models using different algorithms. These applications can be registered as **Application** assets in the DNAT Marketplace.

## Architecture

These applications are designed to run inside SGX enclaves:
- **Input**: CSV data read from stdin
- **Output**: JSON results printed to stdout
- **No file I/O**: All processing is in-memory
- **Error handling**: Errors are returned as JSON

## Applications

### 1. Linear Regression (`linear_regression_trainer.py`)
Trains a linear regression model for predicting continuous target variables.

**Usage:**
```bash
cat dataset.csv | python linear_regression_trainer.py
```

**Example:**
```bash
cat ../computer_theory_grades.csv | python linear_regression_trainer.py
```

**Output:**
- JSON with model metrics (RMSE, MAE, R²)
- Full model weights (coefficients and intercept)
- Feature importance and insights
- Sample predictions

### 2. Decision Tree Classifier (`decision_tree_classifier.py`)
Trains a decision tree classifier for predicting categorical target variables.

**Usage:**
```bash
cat dataset.csv | python decision_tree_classifier.py
```

**Example:**
```bash
cat ../computer_theory_grades.csv | python decision_tree_classifier.py
```

**Output:**
- JSON with classification accuracy
- Full tree structure
- Feature importance
- Confusion matrices
- Sample predictions

### 3. Neural Network Trainer (`neural_network_trainer.py`)
Trains a multi-layer perceptron (MLP) neural network for regression or classification.

**Usage:**
```bash
cat dataset.csv | python neural_network_trainer.py
```

**Example:**
```bash
cat ../computer_theory_grades.csv | python neural_network_trainer.py
```

**Output:**
- JSON with training and test metrics
- Full network weights (all layers)
- Model architecture details
- Loss curve
- Sample predictions

### 4. Random Forest Trainer (`random_forest_trainer.py`)
Trains a random forest model (regressor or classifier) using ensemble of decision trees.

**Usage:**
```bash
cat dataset.csv | python random_forest_trainer.py
```

**Example:**
```bash
cat ../computer_theory_grades.csv | python random_forest_trainer.py
```

**Output:**
- JSON with training and test metrics
- Feature importance rankings
- Tree structure summaries
- Sample predictions

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Auto-Detection

All applications automatically:
- Detect the target column (last numeric column for regression, last column for classification)
- Detect feature columns (all numeric columns except target)
- Detect task type (regression vs classification based on target data type)

## Output Format

All applications output JSON to stdout with the following structure:

```json
{
  "status": "success" | "error",
  "timestamp": "ISO-8601 timestamp",
  "application": {
    "name": "Application Name",
    "version": "1.0.0",
    "algorithm": "algorithm_name"
  },
  "dataset": {
    "rows": 100,
    "columns": 5,
    "column_names": [...]
  },
  "learning": {
    "model_type": "...",
    "target_variable": "...",
    "features_used": [...],
    "insights": {
      "key_findings": [...],
      "feature_importance": {...}
    },
    "model_performance": {...},
    "model_parameters": {
      "full_weights": {...}  // Complete model weights
    },
    "sample_predictions": [...]
  },
  "execution": {
    "training_time_seconds": 0.023,
    "samples_trained": 80,
    "samples_tested": 20
  }
}
```

**Error Format:**
```json
{
  "status": "error",
  "timestamp": "ISO-8601 timestamp",
  "error": {
    "type": "ErrorType",
    "message": "Error message"
  }
}
```

## Registering as Assets

To register these applications in the DNAT Marketplace:

1. **Single file registration**: Upload the `.py` file directly
2. **Project registration**: Create a `.zip` file containing:
   - The Python script(s)
   - `requirements.txt`
   - Any additional dependencies

**Example manifest for registration:**
- **Name**: "Linear Regression Trainer"
- **Description**: "Trains a linear regression model to predict continuous targets from CSV datasets. Reads CSV from stdin and outputs JSON results to stdout."
- **Version**: "1.0.0"
- **Author**: Your name
- **Framework**: "scikit-learn"
- **Dependencies**: "pandas, numpy, scikit-learn"

## Testing Locally

You can test these applications locally with the example datasets:

```bash
# Test linear regression
cat ../computer_theory_grades.csv | python linear_regression_trainer.py

# Test decision tree
cat ../computer_theory_grades.csv | python decision_tree_classifier.py

# Test neural network
cat ../computer_theory_grades.csv | python neural_network_trainer.py

# Test random forest
cat ../computer_theory_grades.csv | python random_forest_trainer.py
```

Or save output to a file:
```bash
cat ../computer_theory_grades.csv | python linear_regression_trainer.py > results.json
```

## Notes

- All applications use a 80/20 train/test split
- Random seed is set to 42 for reproducibility
- Applications automatically detect numeric vs categorical targets
- Feature scaling is applied for neural networks
- Results are saved in JSON format for easy parsing by the executor

