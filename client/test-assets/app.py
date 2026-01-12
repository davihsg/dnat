# Data analysis application using pandas and numpy
# Variables available: dataset (bytes), params (dict)

import pandas as pd
import numpy as np
from io import StringIO

# Parse CSV dataset with pandas
csv_data = dataset.decode('utf-8')
df = pd.read_csv(StringIO(csv_data))

print("=" * 50)
print("CONFIDENTIAL DATA ANALYSIS (SGX Enclave)")
print("=" * 50)

# Basic statistics
print(f"\n📊 Dataset Overview:")
print(f"   Total records: {len(df)}")
print(f"   Columns: {', '.join(df.columns)}")

# Numeric analysis with numpy/pandas
numeric_cols = df.select_dtypes(include=[np.number]).columns
if len(numeric_cols) > 0:
    print(f"\n📈 Numeric Analysis:")
    for col in numeric_cols:
        print(f"\n   {col}:")
        print(f"      Mean: {df[col].mean():.2f}")
        print(f"      Std Dev: {df[col].std():.2f}")
        print(f"      Min: {df[col].min()}")
        print(f"      Max: {df[col].max()}")
        print(f"      Median: {df[col].median():.2f}")

# Correlation analysis (if multiple numeric columns)
if len(numeric_cols) > 1:
    print(f"\n🔗 Correlation Matrix:")
    corr = df[numeric_cols].corr()
    print(corr.to_string())

# Summary statistics
print(f"\n📋 Full Statistics:")
print(df.describe().to_string())

print("\n" + "=" * 50)
print("Analysis complete - executed in secure enclave")
print("=" * 50)
