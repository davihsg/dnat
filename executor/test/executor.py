#!/usr/bin/env python3
import os

print("Hello from SGX enclave!")

# Check if secret was injected by CAS
key = os.environ.get('CODE_KEY')
if key:
    print(f"Secret received from CAS: {key[:20]}...")
else:
    print("No secret found in environment")

