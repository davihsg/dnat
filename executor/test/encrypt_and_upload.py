#!/usr/bin/env python3
"""
Encrypts a Python file and uploads the key to SCONE CAS.
"""

import os
import sys
import base64
import subprocess
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

CAS_URL = "scone-cas.cf"

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
    
    # Save encrypted file (nonce + ciphertext)
    enc_path = filepath + ".enc"
    with open(enc_path, 'wb') as f:
        f.write(nonce + ciphertext)
    
    key_b64 = base64.b64encode(key).decode()
    
    print(f"Encrypted: {enc_path}")
    print(f"Key (base64): {key_b64}")
    
    # Generate session file with the key
    session_content = f"""name: dnat-test
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
    
    print(f"Session file generated: session.yaml")
    
    # Upload to CAS using Docker
    print(f"Uploading session to CAS ({CAS_URL})...")
    cwd = os.getcwd()
    result = subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{cwd}:/work",
        "-w", "/work",
        "registry.scontain.com/sconecuratedimages/sconecli:latest",
        "scone", "session", "create", "session.yaml", "--cas", CAS_URL
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Session uploaded successfully!")
        print(result.stdout)
    else:
        print(f"Upload failed: {result.stderr}")
        sys.exit(1)

if __name__ == "__main__":
    main()

