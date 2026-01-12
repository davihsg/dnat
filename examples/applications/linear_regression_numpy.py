# Linear Regression (SCONE compatible - pure Python, no numpy)
# Variables available: dataset (bytes), params (dict)

import csv
from io import StringIO

# Parse dataset
csv_data = dataset.decode('utf-8')
reader = csv.DictReader(StringIO(csv_data))
rows = list(reader)

print("=" * 60)
print("LINEAR REGRESSION TRAINER (SGX Enclave)")
print("=" * 60)

# Find numeric columns (skip ID columns)
numeric_cols = []
for key in rows[0].keys():
    # Skip columns that look like IDs
    if 'id' in key.lower() or key.lower().endswith('_id'):
        continue
    try:
        float(rows[0][key])
        numeric_cols.append(key)
    except:
        pass

if len(numeric_cols) < 2:
    print("ERROR: Need at least 2 numeric columns!")
else:
    target_col = numeric_cols[-1]
    feature_col = numeric_cols[0]  # Use first non-ID numeric as feature
    
    print(f"\n📊 Dataset: {len(rows)} rows")
    print(f"🎯 Target: {target_col}")
    print(f"📈 Feature: {feature_col}")
    
    # Extract data
    X = [float(row[feature_col]) for row in rows]
    y = [float(row[target_col]) for row in rows]
    n = len(X)
    
    # Simple linear regression: y = mx + b
    # m = (n*Σxy - Σx*Σy) / (n*Σx² - (Σx)²)
    # b = (Σy - m*Σx) / n
    
    sum_x = sum(X)
    sum_y = sum(y)
    sum_xy = sum(X[i] * y[i] for i in range(n))
    sum_x2 = sum(x * x for x in X)
    
    denom = n * sum_x2 - sum_x * sum_x
    if denom == 0:
        print("ERROR: Cannot compute regression (division by zero)")
    else:
        m = (n * sum_xy - sum_x * sum_y) / denom
        b = (sum_y - m * sum_x) / n
        
        # Predictions
        y_pred = [m * x + b for x in X]
        
        # Calculate MSE and R²
        mse = sum((y[i] - y_pred[i]) ** 2 for i in range(n)) / n
        
        mean_y = sum_y / n
        ss_tot = sum((yi - mean_y) ** 2 for yi in y)
        ss_res = sum((y[i] - y_pred[i]) ** 2 for i in range(n))
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        print(f"\n📉 Model Performance:")
        print(f"   MSE: {mse:.4f}")
        print(f"   R²:  {r2:.4f}")
        
        print(f"\n🔢 Model: {target_col} = {m:.4f} * {feature_col} + {b:.4f}")
        
        print(f"\n🔮 Sample Predictions:")
        for i in range(min(5, n)):
            print(f"   {feature_col}={X[i]:.2f} → Actual: {y[i]:.2f}, Predicted: {y_pred[i]:.2f}")

print("\n" + "=" * 60)
print("Analysis complete - executed in secure SGX enclave")
print("=" * 60)
