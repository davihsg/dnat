#!/usr/bin/env python3
"""
DNAT Executor API

This service receives execution requests from the client and orchestrates
the SGX enclave execution flow:

1. Receive execution request (datasetId, applicationId, userAddress)
2. Fetch asset info from blockchain (IPFS URIs)
3. Fetch encrypted assets from IPFS
4. Send to SGX enclave for decryption and execution
5. Return results to client
"""

import os
import json
import subprocess
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS
from web3 import Web3

app = Flask(__name__)
CORS(app)

# Configuration
BLOCKCHAIN_RPC = os.environ.get("BLOCKCHAIN_RPC", "http://localhost:8545")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
IPFS_GATEWAY = os.environ.get("IPFS_GATEWAY", "http://localhost:8080/ipfs")
ENCLAVE_PATH = os.environ.get("ENCLAVE_PATH", "/app/enclave")
CAS_URL = os.environ.get("CAS_URL", "scone-cas.cf")
CAS_CERT_PATH = os.environ.get("CAS_CERT_PATH", "/certs/client.crt")
CAS_KEY_PATH = os.environ.get("CAS_KEY_PATH", "/certs/client.key")

# In-memory key store (for testing when CAS is not available)
# In production, keys should ONLY be stored in CAS
key_store = {}

# Contract ABI (minimal - just what we need)
CONTRACT_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "assetId", "type": "uint256"}],
        "name": "getAsset",
        "outputs": [
            {"internalType": "uint8", "name": "assetType", "type": "uint8"},
            {"internalType": "address", "name": "owner", "type": "address"},
            {"internalType": "string", "name": "encryptedUri", "type": "string"},
            {"internalType": "string", "name": "manifestUri", "type": "string"},
            {"internalType": "bytes32", "name": "contentHash", "type": "bytes32"},
            {"internalType": "uint256", "name": "price", "type": "uint256"},
            {"internalType": "bytes", "name": "bloomFilter", "type": "bytes"},
            {"internalType": "bool", "name": "active", "type": "bool"},
        ],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"internalType": "address", "name": "user", "type": "address"},
            {"internalType": "string", "name": "encryptedDatasetHash", "type": "string"},
            {"internalType": "string", "name": "encryptedApplicationHash", "type": "string"},
        ],
        "name": "hasAccess",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function",
    },
]

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RPC))
contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=CONTRACT_ABI)


def fetch_from_ipfs(ipfs_uri: str) -> bytes:
    """Fetch content from IPFS given an IPFS URI."""
    import requests
    
    # Convert ipfs:// URI to gateway URL
    if ipfs_uri.startswith("ipfs://"):
        cid = ipfs_uri[7:]
    else:
        cid = ipfs_uri
    
    url = f"{IPFS_GATEWAY}/{cid}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content


def get_asset_info(asset_id: int) -> dict:
    """Fetch asset information from the blockchain."""
    result = contract.functions.getAsset(asset_id).call()
    return {
        "assetType": result[0],
        "owner": result[1],
        "encryptedUri": result[2],
        "manifestUri": result[3],
        "contentHash": result[4].hex(),
        "price": result[5],
        "bloomFilter": result[6].hex(),
        "active": result[7],
    }


def check_access(user: str, dataset_uri: str, app_uri: str) -> bool:
    """Check if user has access to run app on dataset."""
    try:
        return contract.functions.hasAccess(user, dataset_uri, app_uri).call()
    except Exception as e:
        print(f"Access check failed: {e}")
        return False


def run_in_enclave(dataset_data: bytes, app_data: bytes, params: dict = None) -> dict:
    """
    Run the application over the dataset inside the SGX enclave.
    
    In the full implementation, this would:
    1. Send encrypted data to enclave
    2. Enclave fetches keys from CAS
    3. Enclave decrypts, re-encrypts with K_AD
    4. Second enclave runs execution
    5. Returns results
    
    For now, we simulate this by calling the enclave script directly.
    """
    # Create temp files for the encrypted data
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as dataset_file:
        dataset_file.write(dataset_data)
        dataset_path = dataset_file.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as app_file:
        app_file.write(app_data)
        app_path = app_file.name
    
    try:
        # In production, this would call the SCONE enclave
        # For now, we'll use a subprocess that simulates the enclave behavior
        result = subprocess.run(
            [
                "python3", f"{ENCLAVE_PATH}/execute.py",
                "--dataset", dataset_path,
                "--application", app_path,
                "--params", json.dumps(params or {})
            ],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        return {
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr if result.returncode != 0 else None,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Execution timed out after 5 minutes",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        # Clean up temp files
        os.unlink(dataset_path)
        os.unlink(app_path)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/cas/upload-key", methods=["POST"])
def upload_key_to_cas():
    """
    Upload an encryption key to SCONE CAS.
    
    Request body:
    {
        "sessionName": "dnat-dataset-abc123-1234567890",
        "encryptionKey": "base64-encoded-key",
        "assetType": "dataset" | "application",
        "ipfsHash": "Qm..."
    }
    """
    try:
        data = request.json
        session_name = data.get("sessionName")
        encryption_key = data.get("encryptionKey")
        asset_type = data.get("assetType")
        ipfs_hash = data.get("ipfsHash")
        
        if not all([session_name, encryption_key, asset_type, ipfs_hash]):
            return jsonify({"success": False, "error": "Missing required fields"}), 400
        
        print(f"Uploading key to CAS: session={session_name}, type={asset_type}")
        
        # Generate CAS session YAML
        key_name = f"{asset_type.upper()}_KEY"
        session_yaml = f"""name: {session_name}
version: "0.3.10"

security:
  attestation:
    tolerate: [debug-mode, hyperthreading, insecure-igpu, outdated-tcb, software-hardening-needed]
    ignore_advisories: "*"

services:
  - name: executor
    command: python /app/enclave/execute.py
    environment:
      {key_name}: "$$SCONE::{key_name}$$"

secrets:
  - name: {key_name}
    kind: ascii
    value: "{encryption_key}"
"""
        
        # Try to upload to CAS
        import requests
        try:
            # Check if certificates exist
            if os.path.exists(CAS_CERT_PATH) and os.path.exists(CAS_KEY_PATH):
                response = requests.post(
                    f"https://{CAS_URL}:8081/session",
                    data=session_yaml,
                    cert=(CAS_CERT_PATH, CAS_KEY_PATH),
                    verify=False,
                    timeout=30
                )
                
                if response.ok or "Created Session" in response.text:
                    print(f"Key uploaded to CAS successfully: {session_name}")
                    return jsonify({
                        "success": True,
                        "sessionName": session_name,
                        "casResponse": response.text
                    })
                else:
                    print(f"CAS upload failed: {response.text}")
                    # Fall back to local storage
            else:
                print("CAS certificates not found, using local storage")
        except Exception as cas_error:
            print(f"CAS connection error: {cas_error}")
        
        # Fallback: store key locally (for testing only!)
        key_store[ipfs_hash] = {
            "key": encryption_key,
            "assetType": asset_type,
            "sessionName": session_name,
        }
        print(f"Key stored locally for: {ipfs_hash}")
        
        return jsonify({
            "success": True,
            "sessionName": session_name,
            "warning": "Key stored locally (CAS not available)"
        })
        
    except Exception as e:
        print(f"Error uploading key: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/cas/get-key/<ipfs_hash>", methods=["GET"])
def get_key(ipfs_hash):
    """
    Get encryption key for an asset (from local store for testing).
    In production, keys are fetched by the enclave from CAS after attestation.
    """
    if ipfs_hash in key_store:
        return jsonify({
            "success": True,
            "key": key_store[ipfs_hash]["key"],
            "assetType": key_store[ipfs_hash]["assetType"],
        })
    return jsonify({"success": False, "error": "Key not found"}), 404


@app.route("/execute", methods=["POST"])
def execute():
    """
    Execute an application over a dataset.
    
    Request body:
    {
        "datasetId": "1",
        "applicationId": "2",
        "userAddress": "0x...",
        "params": {...}  // optional
    }
    """
    try:
        data = request.json
        dataset_id = int(data.get("datasetId"))
        application_id = int(data.get("applicationId"))
        user_address = data.get("userAddress")
        params = data.get("params", {})
        
        print(f"Execution request: dataset={dataset_id}, app={application_id}, user={user_address}")
        
        # Step 1: Fetch asset info from blockchain
        print("Fetching asset info from blockchain...")
        dataset_info = get_asset_info(dataset_id)
        app_info = get_asset_info(application_id)
        
        if not dataset_info["active"]:
            return jsonify({"success": False, "error": "Dataset is not active"}), 400
        if not app_info["active"]:
            return jsonify({"success": False, "error": "Application is not active"}), 400
        
        # Step 2: Check access rights
        print("Checking access rights...")
        has_access = check_access(
            user_address,
            dataset_info["encryptedUri"],
            app_info["encryptedUri"]
        )
        
        if not has_access:
            return jsonify({
                "success": False,
                "error": "User does not have access to this dataset-application combination"
            }), 403
        
        # Step 3: Fetch encrypted assets from IPFS
        print(f"Fetching dataset from IPFS: {dataset_info['encryptedUri']}")
        dataset_data = fetch_from_ipfs(dataset_info["encryptedUri"])
        
        print(f"Fetching application from IPFS: {app_info['encryptedUri']}")
        app_data = fetch_from_ipfs(app_info["encryptedUri"])
        
        # Step 4: Run in SGX enclave
        print("Running in SGX enclave...")
        result = run_in_enclave(dataset_data, app_data, params)
        
        # Step 5: Return results
        return jsonify({
            "success": result["success"],
            "output": result.get("output"),
            "error": result.get("error"),
            "executionTime": None,  # TODO: measure execution time
        })
        
    except Exception as e:
        print(f"Execution error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

