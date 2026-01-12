# Data Analysis (SCONE compatible - pure Python)
# Variables available: dataset (bytes), params (dict)

import csv
from io import StringIO

# Parse dataset
csv_data = dataset.decode('utf-8')
reader = csv.DictReader(StringIO(csv_data))
rows = list(reader)
columns = list(rows[0].keys()) if rows else []

print("=" * 60)
print("CONFIDENTIAL DATA ANALYSIS (SGX Enclave)")
print("=" * 60)

print(f"\n📊 DATASET OVERVIEW")
print(f"   Rows: {len(rows)}")
print(f"   Columns: {len(columns)}")
print(f"   Column names: {', '.join(columns)}")

# Find numeric columns (skip ID columns)
numeric_cols = []
for col in columns:
    if 'id' in col.lower() or col.lower().endswith('_id'):
        continue
    try:
        float(rows[0][col])
        numeric_cols.append(col)
    except:
        pass

# Statistics for numeric columns
if numeric_cols:
    print(f"\n📈 NUMERIC STATISTICS")
    for col in numeric_cols:
        values = [float(row[col]) for row in rows if row[col]]
        n = len(values)
        if n > 0:
            mean = sum(values) / n
            sorted_vals = sorted(values)
            median = sorted_vals[n // 2] if n % 2 else (sorted_vals[n//2 - 1] + sorted_vals[n//2]) / 2
            variance = sum((v - mean) ** 2 for v in values) / n
            std = variance ** 0.5
            
            print(f"\n   {col}:")
            print(f"      Count: {n}")
            print(f"      Mean: {mean:.2f}")
            print(f"      Std: {std:.2f}")
            print(f"      Min: {min(values):.2f}")
            print(f"      Max: {max(values):.2f}")
            print(f"      Median: {median:.2f}")

# Correlation between first two numeric columns
if len(numeric_cols) >= 2:
    print(f"\n🔗 CORRELATION")
    col1, col2 = numeric_cols[0], numeric_cols[1]
    x = [float(row[col1]) for row in rows]
    y = [float(row[col2]) for row in rows]
    n = len(x)
    
    mean_x = sum(x) / n
    mean_y = sum(y) / n
    
    cov = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n)) / n
    std_x = (sum((xi - mean_x) ** 2 for xi in x) / n) ** 0.5
    std_y = (sum((yi - mean_y) ** 2 for yi in y) / n) ** 0.5
    
    corr = cov / (std_x * std_y) if std_x > 0 and std_y > 0 else 0
    print(f"   {col1} <-> {col2}: {corr:.4f}")

# Categorical analysis
cat_cols = [c for c in columns if c not in numeric_cols]
if cat_cols:
    print(f"\n📁 CATEGORICAL ANALYSIS")
    for col in cat_cols[:3]:
        counts = {}
        for row in rows:
            val = row[col]
            counts[val] = counts.get(val, 0) + 1
        
        print(f"\n   {col}:")
        sorted_counts = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]
        for val, count in sorted_counts:
            pct = count / len(rows) * 100
            print(f"      {val}: {count} ({pct:.1f}%)")

# Sample data
print(f"\n📋 SAMPLE DATA (first 5 rows)")
for i, row in enumerate(rows[:5]):
    vals = [f"{k}={v}" for k, v in list(row.items())[:4]]
    print(f"   {i+1}. {', '.join(vals)}")

print("\n" + "=" * 60)
print("Analysis complete - executed in secure SGX enclave")
print("=" * 60)
