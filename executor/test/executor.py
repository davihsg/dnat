#!/usr/bin/env python3
import os
import sys

print("Hello from SGX enclave!")

# Get secret from CAS
key_b64 = os.environ.get('CODE_KEY')
if key_b64:
    print(f"Secret received from CAS: {key_b64[:20]}...")
else:
    print("No secret found in environment")
    sys.exit(1)

# Read encrypted file
enc_path = '/data/hello.py.enc'
print(f"Reading encrypted file: {enc_path}")
try:
    with open(enc_path, 'rb') as f:
        data = f.read()
    print(f"Read {len(data)} bytes")
except Exception as e:
    print(f"Error reading file: {e}")
    sys.exit(1)

# Decrypt
print("Importing cryptography...")
try:
    import base64
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    print("Import successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

try:
    key = base64.b64decode(key_b64)
    nonce = data[:12]
    ciphertext = data[12:]
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    print("Decrypted successfully!")
    print("-" * 40)
    print(plaintext.decode())
    print("-" * 40)
except Exception as e:
    print(f"Decryption error: {e}")
    sys.exit(1)

