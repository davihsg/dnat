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
export SCONE_CONFIG_ID="${SCONE_CONFIG_ID:-}"  # Format: <session_name>/<service_name>

# CAS certificate paths
export CAS_CERT="../certs/client.crt"
export CAS_KEY="../certs/client.key"

echo "Starting Executor API on port $PORT"
echo "Blockchain RPC: $BLOCKCHAIN_RPC"
echo "IPFS Gateway: $IPFS_GATEWAY"
echo "Enclave Image: $ENCLAVE_IMAGE"
echo "SCONE CAS: $SCONE_CAS_ADDR"
echo "SCONE LAS: $SCONE_LAS_ADDR"
echo "SCONE Config ID: $SCONE_CONFIG_ID"

if [ -z "$SCONE_CONFIG_ID" ]; then
    echo "WARNING: SCONE_CONFIG_ID not set. Set it to <session_name>/<service_name>"
fi

python3 app.py

