#!/usr/bin/env python3
"""
Executor: retrieves key from CAS (via SCONE), decrypts code, runs it.
"""

import os
import sys
import base64
import tempfile
import subprocess
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def main():
    # Key is injected by SCONE from CAS after attestation
    key_b64 = os.environ.get('CODE_KEY')
    enc_path = os.environ.get('ENCRYPTED_CODE', '/data/hello.py.enc')
    
    if not key_b64:
        print("ERROR: CODE_KEY not found. CAS attestation may have failed.")
        sys.exit(1)
    
    # Read encrypted file
    with open(enc_path, 'rb') as f:
        data = f.read()
    
    nonce = data[:12]
    ciphertext = data[12:]
    
    # Decrypt
    key = base64.b64decode(key_b64)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    
    print("Decrypted code successfully. Executing...")
    print("-" * 40)
    
    # Execute
    with tempfile.NamedTemporaryFile(mode='wb', suffix='.py', delete=False) as f:
        f.write(plaintext)
        temp_path = f.name
    
    try:
        subprocess.run([sys.executable, temp_path])
    finally:
        os.unlink(temp_path)

if __name__ == "__main__":
    main()

