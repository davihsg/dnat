# Simple application that analyzes the dataset
# Variables available: dataset (bytes), params (dict)

import csv
from io import StringIO

# Parse CSV dataset
csv_data = dataset.decode('utf-8')
reader = csv.DictReader(StringIO(csv_data))
rows = list(reader)

print("=== Dataset Analysis ===")
print(f"Total records in dataset: {len(rows)}")

# Calculate average age and salary
total_age = sum(int(row['Age']) for row in rows)
total_salary = sum(int(row['Salary']) for row in rows)

avg_age = total_age / len(rows)
avg_salary = total_salary / len(rows)

print(f"Average age: {avg_age:.1f}")
print(f"Average salary: ${avg_salary:,.2f}")

# Find highest salary
highest = max(rows, key=lambda x: int(x['Salary']))
print(f"Highest earner: {highest['Name']} (${highest['Salary']})")

print("=== Analysis Complete ===")

