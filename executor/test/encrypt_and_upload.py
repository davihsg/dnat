#!/usr/bin/env python3
"""
Encrypts a Python file and uploads the key to SCONE CAS.
Based on: https://sconedocs.github.io/cas_blender_example/
"""

import os
import sys
import base64
import subprocess
import re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CAS_URL = "scone-cas.cf"
SESSION_NAME = "dnat-test"
CERT_PATH = "conf/client.crt"
KEY_PATH = "conf/client.key"

def get_session_digest():
    """Get the current session digest (if exists) for updating."""
    result = subprocess.run([
        "curl", "-k", "-s",
        "--cert", CERT_PATH,
        "--key", KEY_PATH,
        f"https://{CAS_URL}:8081/session/{SESSION_NAME}"
    ], capture_output=True, text=True)
    
    # Extract digest from response
    match = re.search(r'digest:\s*([a-f0-9]+)', result.stdout)
    if match:
        return match.group(1)
    return None

def main():
    if len(sys.argv) < 3:
        print("Usage: python encrypt_and_upload.py <file.py> <mrenclave>")
        print("\nTo get MRENCLAVE, run:")
        print("  docker build -t dnat-executor .")
        print("  docker run --rm -e SCONE_HASH=1 dnat-executor")
        sys.exit(1)
    
    filepath = sys.argv[1]
    mrenclave = sys.argv[2]
    
    # Check certificate exists
    if not os.path.exists(CERT_PATH) or not os.path.exists(KEY_PATH):
        print("Error: Certificate not found. Run ./generate_cert.sh first")
        sys.exit(1)
    
    # Read plaintext
    with open(filepath, 'rb') as f:
        plaintext = f.read()
    
    # Generate key and encrypt
    key = os.urandom(32)
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)
    
    # Save encrypted file
    enc_path = filepath + ".enc"
    with open(enc_path, 'wb') as f:
        f.write(nonce + ciphertext)
    
    key_b64 = base64.b64encode(key).decode()
    
    print(f"Encrypted: {enc_path}")
    print(f"Key (base64): {key_b64}")
    
    # Check if session already exists (for update)
    predecessor = get_session_digest()
    if predecessor:
        print(f"Existing session found, updating (predecessor: {predecessor[:16]}...)")
        predecessor_line = f"predecessor: {predecessor}"
    else:
        print("Creating new session")
        predecessor_line = ""
    
    # Generate session file with the key
    session_content = f"""name: {SESSION_NAME}
version: "0.3.1"
{predecessor_line}

security:
  attestation:
    tolerate: [debug-mode, hyperthreading, insecure-igpu, outdated-tcb, software-hardening-needed]
    ignore_advisories: "*"

services:
  - name: executor
    mrenclaves: [{mrenclave}]
    command: python /app/executor.py

secrets:
  - name: CODE_KEY
    kind: ascii
    value: "{key_b64}"
"""
    
    with open("session.yaml", 'w') as f:
        f.write(session_content)
    
    print(f"Session: {SESSION_NAME}")
    
    # Upload to CAS using curl with client certificate
    print(f"Uploading session to CAS ({CAS_URL})...")
    result = subprocess.run([
        "curl", "-k", "-s",
        "--cert", CERT_PATH,
        "--key", KEY_PATH,
        "--data-binary", "@session.yaml",
        "-X", "POST",
        f"https://{CAS_URL}:8081/session"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.stderr:
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    main()

