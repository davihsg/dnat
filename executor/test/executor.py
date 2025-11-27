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
print("Importing pycryptodome...")
try:
    import base64
    from Crypto.Cipher import AES
    print("Import successful")
except Exception as e:
    print(f"Import error: {e}")
    sys.exit(1)

try:
    key = base64.b64decode(key_b64)
    nonce = data[:12]
    ciphertext = data[12:-16]  # Last 16 bytes are the tag
    tag = data[-16:]
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    plaintext = cipher.decrypt_and_verify(ciphertext, tag)
    print("Decrypted successfully!")
except Exception as e:
    print(f"Decryption error: {e}")
    sys.exit(1)

# Execute the decrypted code
print("-" * 40)
print("Executing decrypted code:")
print("-" * 40)
try:
    exec(plaintext.decode())
except Exception as e:
    print(f"Execution error: {e}")
    sys.exit(1)
print("-" * 40)
print("Execution complete!")

