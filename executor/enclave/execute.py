#!/usr/bin/env python3
"""
SGX Enclave Execution Script

This script runs inside the SGX enclave and:
1. Receives encrypted dataset and application
2. Gets decryption keys from SCONE CAS (injected after attestation)
3. Decrypts and runs the application over the dataset
4. Returns results

Keys are injected by SCONE CAS as environment variables:
- DATASET_KEY: Key to decrypt the dataset
- APP_KEY: Key to decrypt the application
"""

import os
import sys
import base64
import json
from Crypto.Cipher import AES


def decrypt_data(encrypted_path: str, key_b64: str) -> bytes:
    """Decrypt AES-256-GCM encrypted data."""
    key = base64.b64decode(key_b64)
    
    with open(encrypted_path, 'rb') as f:
        data = f.read()
    
    nonce = data[:12]
    ciphertext = data[12:-16]
    tag = data[-16:]
    
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    
    return plaintext


def run_application(app_code: str, dataset: bytes, params: dict) -> str:
    """
    Run the application code over the dataset.
    
    The application receives:
    - dataset: The decrypted dataset as bytes
    - params: Execution parameters from the user
    
    Returns the output as a string.
    """
    import io
    from contextlib import redirect_stdout, redirect_stderr
    
    # Prepare execution environment
    exec_globals = {
        "dataset": dataset,
        "params": params,
        "__builtins__": __builtins__,
    }
    
    # Capture output
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    
    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(app_code, exec_globals)
        
        output = stdout_capture.getvalue()
        errors = stderr_capture.getvalue()
        
        if errors:
            output += f"\n[STDERR]\n{errors}"
        
        return output
        
    except Exception as e:
        return f"Execution error: {str(e)}\n{stderr_capture.getvalue()}"


def main():
    # Use fixed paths (mounted by the executor API at /data/)
    dataset_path = "/data/dataset.enc"
    app_path = "/data/application.enc"
    params_path = "/data/params.json"
    
    # Get keys from environment (injected by SCONE CAS after attestation)
    dataset_key = os.environ.get("DATASET_KEY")
    app_key = os.environ.get("APP_KEY")
    
    if not dataset_key or not app_key:
        print("Error: Decryption keys not found. CAS attestation may have failed.", file=sys.stderr)
        sys.exit(1)
    
    # Load params from file
    params = {}
    if os.path.isfile(params_path):
        with open(params_path, 'r') as f:
            params = json.load(f)
    
    print("=" * 50)
    print("SGX Enclave Execution")
    print("=" * 50)
    print("Keys retrieved from CAS")
    
    # Step 1: Decrypt dataset
    print("Decrypting dataset...")
    try:
        dataset = decrypt_data(dataset_path, dataset_key)
        print(f"  Dataset decrypted: {len(dataset)} bytes")
    except Exception as e:
        print(f"Error decrypting dataset: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Step 2: Decrypt application
    print("Decrypting application...")
    try:
        app_code = decrypt_data(app_path, app_key).decode('utf-8')
        print(f"  Application decrypted: {len(app_code)} bytes")
    except Exception as e:
        print(f"Error decrypting application: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Step 3: Run the application
    print("Executing application...")
    print("-" * 50)
    
    output = run_application(app_code, dataset, params)
    print(output)
    
    print("-" * 50)
    print("Execution complete.")


if __name__ == "__main__":
    main()

