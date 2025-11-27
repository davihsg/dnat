#!/usr/bin/env python3
"""
Simple Dataset Logger

This application simply logs the raw dataset content.
Useful for testing the execution flow and verifying that
data is correctly decrypted and passed to the application.

Input:
  - dataset: Raw bytes of the decrypted dataset (CSV)
  - params: Optional parameters (not used)

Output:
  - Prints the dataset content to stdout
"""

# The dataset is passed as a global variable by the executor
# It contains the raw decrypted bytes

print("=" * 60)
print("DATASET LOGGER - Raw Dataset Content")
print("=" * 60)

try:
    # 'dataset' is injected by the executor
    if 'dataset' in dir() or 'dataset' in globals():
        data = dataset  # noqa: F821
        
        # Print metadata
        print(f"\nDataset size: {len(data)} bytes")
        print(f"Dataset type: {type(data)}")
        
        # Try to decode as UTF-8 text
        print("\n" + "-" * 60)
        print("CONTENT:")
        print("-" * 60)
        
        try:
            text_content = data.decode('utf-8')
            print(text_content)
        except UnicodeDecodeError:
            print("[Binary data - cannot decode as UTF-8]")
            print(f"First 100 bytes (hex): {data[:100].hex()}")
        
        # If it's a CSV, show some stats
        print("\n" + "-" * 60)
        print("STATS:")
        print("-" * 60)
        
        try:
            lines = text_content.strip().split('\n')
            print(f"Number of lines: {len(lines)}")
            if len(lines) > 0:
                header = lines[0]
                columns = header.split(',')
                print(f"Number of columns: {len(columns)}")
                print(f"Columns: {columns}")
                print(f"Data rows: {len(lines) - 1}")
        except:
            print("[Could not parse as CSV]")
            
    else:
        print("ERROR: 'dataset' variable not found!")
        print("Available variables:", dir())
        
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("END OF DATASET LOG")
print("=" * 60)

