#!/usr/bin/env python3
"""
Encrypts a Python file and uploads the key to SCONE CAS.
Based on: https://sconedocs.github.io/cas_blender_example/
"""

import os
import sys
import base64
import subprocess
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CAS_URL = "scone-cas.cf"
SESSION_NAME = "dnat-test"

def main():
    if len(sys.argv) < 2:
        print("Usage: python encrypt_and_upload.py <file.py>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    
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
    
    # Generate session file with the key
    session_content = f"""name: {SESSION_NAME}
version: "0.3"

services:
  - name: executor
    attestation:
      - mrenclave: ["*"]

secrets:
  - name: CODE_KEY
    kind: ascii
    value: "{key_b64}"
    export:
      - session: $SELF
        service: executor
"""
    
    with open("session.yaml", 'w') as f:
        f.write(session_content)
    
    print(f"Session: {SESSION_NAME}")
    
    # Upload to CAS using curl (insecure, no client cert)
    print(f"Uploading session to CAS ({CAS_URL})...")
    result = subprocess.run([
        "curl", "-k", "-s",
        "--data-binary", "@session.yaml",
        "-X", "POST",
        f"https://{CAS_URL}:8081/session"
    ], capture_output=True, text=True)
    
    print(result.stdout)
    
    if result.stderr:
        print(f"Error: {result.stderr}")

if __name__ == "__main__":
    main()

