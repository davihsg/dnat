# K-Means Clustering (SCONE compatible - pure Python)
# Variables available: dataset (bytes), params (dict)

import csv
import random
from io import StringIO

# Parse dataset
csv_data = dataset.decode('utf-8')
reader = csv.DictReader(StringIO(csv_data))
rows = list(reader)
columns = list(rows[0].keys()) if rows else []

print("=" * 60)
print("K-MEANS CLUSTERING (SGX Enclave)")
print("=" * 60)

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

if len(numeric_cols) < 1:
    print("ERROR: Need at least 1 numeric column!")
else:
    n_clusters = min(3, len(rows) // 2)
    
    print(f"\n📊 Dataset: {len(rows)} samples")
    print(f"🎯 Clusters: {n_clusters}")
    print(f"📈 Features: {', '.join(numeric_cols)}")
    
    # Extract numeric data
    data = []
    for row in rows:
        point = [float(row[col]) for col in numeric_cols]
        data.append(point)
    
    # Normalize data
    n_features = len(numeric_cols)
    means = [sum(d[i] for d in data) / len(data) for i in range(n_features)]
    stds = [(sum((d[i] - means[i]) ** 2 for d in data) / len(data)) ** 0.5 for i in range(n_features)]
    
    normalized = []
    for point in data:
        norm_point = [(point[i] - means[i]) / (stds[i] + 1e-8) for i in range(n_features)]
        normalized.append(norm_point)
    
    # Initialize centroids randomly
    random.seed(42)
    centroid_idx = random.sample(range(len(normalized)), n_clusters)
    centroids = [normalized[i][:] for i in centroid_idx]
    
    # K-Means iterations
    labels = [0] * len(normalized)
    for iteration in range(50):
        # Assign points to nearest centroid
        new_labels = []
        for point in normalized:
            distances = []
            for c in centroids:
                dist = sum((point[i] - c[i]) ** 2 for i in range(n_features)) ** 0.5
                distances.append(dist)
            new_labels.append(distances.index(min(distances)))
        
        # Check convergence
        if new_labels == labels:
            print(f"\n✅ Converged after {iteration + 1} iterations")
            break
        labels = new_labels
        
        # Update centroids
        for k in range(n_clusters):
            cluster_points = [normalized[i] for i in range(len(normalized)) if labels[i] == k]
            if cluster_points:
                for j in range(n_features):
                    centroids[k][j] = sum(p[j] for p in cluster_points) / len(cluster_points)
    
    # Cluster summary
    print(f"\n📊 CLUSTER SUMMARY")
    for k in range(n_clusters):
        cluster_idx = [i for i in range(len(labels)) if labels[i] == k]
        pct = len(cluster_idx) / len(rows) * 100
        print(f"\n   Cluster {k}: {len(cluster_idx)} samples ({pct:.1f}%)")
        
        if cluster_idx:
            for j, col in enumerate(numeric_cols):
                vals = [data[i][j] for i in cluster_idx]
                avg = sum(vals) / len(vals)
                print(f"      {col}: avg={avg:.2f}")
    
    # Sample assignments
    print(f"\n🔮 SAMPLE ASSIGNMENTS")
    for i in range(min(8, len(rows))):
        vals = ", ".join(f"{numeric_cols[j]}={data[i][j]:.1f}" for j in range(min(2, n_features)))
        print(f"   [{labels[i]}] {vals}")

print("\n" + "=" * 60)
print("Clustering complete - executed in secure SGX enclave")
print("=" * 60)
