#!/bin/bash
# Run the Executor API outside of Docker

cd "$(dirname "$0")/api"

# Environment variables
export PORT=8081
export DEBUG=true
export BLOCKCHAIN_RPC="http://localhost:8545"
export CONTRACT_ADDRESS="${CONTRACT_ADDRESS:-0x5FbDB2315678afecb367f032d93F642f64180aa3}"
export IPFS_GATEWAY="http://localhost:8080/ipfs"
export ENCLAVE_IMAGE="dnat-enclave"

# SCONE configuration
export SCONE_CAS_ADDR="${SCONE_CAS_ADDR:-scone-cas.cf}"
export SCONE_LAS_ADDR="${SCONE_LAS_ADDR:-localhost}"
export MRENCLAVE="${MRENCLAVE:-faf69aa120d1cbec7941677e28dbb740d10b98095941da7117a9a579ca767df4}"  # Optional: restrict to specific enclave hash

# CAS certificate paths
export CAS_CERT="../certs/client.crt"
export CAS_KEY="../certs/client.key"

echo "Starting Executor API on port $PORT"
echo "Blockchain RPC: $BLOCKCHAIN_RPC"
echo "IPFS Gateway: $IPFS_GATEWAY"
echo "Enclave Image: $ENCLAVE_IMAGE"
echo "SCONE CAS: $SCONE_CAS_ADDR"
echo "SCONE LAS: $SCONE_LAS_ADDR"
echo "MRENCLAVE: ${MRENCLAVE:-<not set - permissive mode>}"

python3 app.py

