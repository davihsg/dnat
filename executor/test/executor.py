#!/usr/bin/env python3
"""
DNAT Executor - Decrypts and runs code inside SGX enclave.
Key is retrieved from SCONE CAS after attestation.
"""
import os
import base64
from Crypto.Cipher import AES

# Get decryption key from CAS (injected after attestation)
key_b64 = os.environ.get('CODE_KEY')
key = base64.b64decode(key_b64)

# Read and decrypt the code
with open('/data/hello.py.enc', 'rb') as f:
    data = f.read()

nonce = data[:12]
ciphertext = data[12:-16]
tag = data[-16:]

cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
code = cipher.decrypt_and_verify(ciphertext, tag).decode()

# Execute
print("=" * 40)
print("Executing decrypted code in SGX enclave:")
print("=" * 40)
exec(code)
print("=" * 40)

