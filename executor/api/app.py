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
import sys
import json
import subprocess
import tempfile
import logging
from flask import Flask, request, jsonify
from flask_cors import CORS
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Disable buffering
sys.stdout.reconfigure(line_buffering=True)

app = Flask(__name__)
CORS(app)

# Local key storage (for testing - in production, keys come from CAS after attestation)
KEY_STORE = {}

# Configuration
BLOCKCHAIN_RPC = os.environ.get("BLOCKCHAIN_RPC", "http://localhost:8545")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
IPFS_GATEWAY = os.environ.get("IPFS_GATEWAY", "http://localhost:8080/ipfs")
ENCLAVE_PATH = os.environ.get("ENCLAVE_PATH", "/app/enclave")

# CAS Configuration
CAS_URL = os.environ.get("CAS_URL", "scone-cas.cf")
CAS_CERT = os.environ.get("CAS_CERT", "/app/certs/client.crt")
CAS_KEY = os.environ.get("CAS_KEY", "/app/certs/client.key")

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


def run_in_enclave(dataset_data: bytes, app_data: bytes, dataset_key: str, app_key: str, params: dict = None) -> dict:
    """
    Run the application over the dataset inside the SGX enclave.
    
    In the full implementation, this would:
    1. Send encrypted data to enclave
    2. Enclave fetches keys from CAS
    3. Enclave decrypts, re-encrypts with K_AD
    4. Second enclave runs execution
    5. Returns results
    
    For now, we pass keys directly (in production, CAS provides them after attestation).
    """
    # Create temp files for the encrypted data
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as dataset_file:
        dataset_file.write(dataset_data)
        dataset_path = dataset_file.name
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".enc") as app_file:
        app_file.write(app_data)
        app_path = app_file.name
    
    try:
        # Set up environment with keys (in production, CAS injects these)
        env = os.environ.copy()
        env["DATASET_KEY"] = dataset_key
        env["APP_KEY"] = app_key
        
        result = subprocess.run(
            [
                "python3", f"{ENCLAVE_PATH}/execute.py",
                "--dataset", dataset_path,
                "--application", app_path,
                "--params", json.dumps(params or {})
            ],
            capture_output=True,
            text=True,
            timeout=300,
            env=env
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


@app.route("/cas/upload", methods=["POST"])
def cas_upload():
    """
    Upload a session to CAS.
    
    Request body:
    {
        "sessionName": "dnat-dataset-abc123",
        "sessionYAML": "name: dnat-dataset-abc123\n..."
    }
    """
    try:
        data = request.json
        session_name = data.get("sessionName")
        session_yaml = data.get("sessionYAML")
        
        logger.info(f"[CAS] Upload request for session: {session_name}")
        
        if not session_yaml:
            logger.error("[CAS] Error: Missing sessionYAML")
            return jsonify({"success": False, "error": "Missing sessionYAML"}), 400
        
        logger.info(f"[CAS] Session YAML length: {len(session_yaml)} bytes")
        logger.info(f"[CAS] CAS URL: {CAS_URL}")
        logger.info(f"[CAS] Cert path: {CAS_CERT} (exists: {os.path.exists(CAS_CERT)})")
        logger.info(f"[CAS] Key path: {CAS_KEY} (exists: {os.path.exists(CAS_KEY)})")
        
        if not os.path.exists(CAS_CERT):
            logger.error(f"[CAS] Error: Certificate not found at {CAS_CERT}")
            return jsonify({"success": False, "error": f"Certificate not found: {CAS_CERT}"}), 500
        
        if not os.path.exists(CAS_KEY):
            logger.error(f"[CAS] Error: Key not found at {CAS_KEY}")
            return jsonify({"success": False, "error": f"Key not found: {CAS_KEY}"}), 500
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(session_yaml)
            yaml_path = f.name
        
        logger.info(f"[CAS] Saved session to temp file: {yaml_path}")
        
        # Upload to CAS using curl
        cmd = [
            "curl", "-k", "-s",
            "--cert", CAS_CERT,
            "--key", CAS_KEY,
            "--data-binary", f"@{yaml_path}",
            "-X", "POST",
            f"https://{CAS_URL}:8081/session"
        ]
        logger.info(f"[CAS] Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        os.unlink(yaml_path)
        
        logger.info(f"[CAS] curl exit code: {result.returncode}")
        logger.info(f"[CAS] curl stdout: {result.stdout}")
        logger.info(f"[CAS] curl stderr: {result.stderr}")
        
        response_text = result.stdout
        if "hash" in response_text or "Created Session" in response_text:
            logger.info(f"[CAS] Success! Session uploaded: {session_name}")
            
            # Also store key locally for testing (extract from session YAML)
            # Parse the key from the YAML
            import re
            key_match = re.search(r'value:\s*"([^"]+)"', session_yaml)
            ipfs_match = re.search(r'dnat-(dataset|application)-(\w+)', session_name)
            if key_match and ipfs_match:
                asset_type = ipfs_match.group(1)
                ipfs_hash = ipfs_match.group(2)
                KEY_STORE[ipfs_hash] = {
                    "key": key_match.group(1),
                    "type": asset_type,
                    "sessionName": session_name
                }
                logger.info(f"[CAS] Stored key locally for {asset_type} {ipfs_hash}")
            
            return jsonify({"success": True, "sessionName": session_name, "response": response_text})
        else:
            logger.error(f"[CAS] Failed! Response: {response_text}")
            return jsonify({"success": False, "error": response_text or result.stderr or "Unknown error"}), 500
            
    except Exception as e:
        logger.exception(f"[CAS] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


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
    import traceback
    
    try:
        data = request.json
        logger.info(f"[EXEC] Received request: {data}")
        
        dataset_id = int(data.get("datasetId"))
        application_id = int(data.get("applicationId"))
        user_address = data.get("userAddress")
        params = data.get("params", {})
        
        logger.info(f"[EXEC] Parsed: dataset={dataset_id}, app={application_id}, user={user_address}")
        logger.info(f"[EXEC] Config: BLOCKCHAIN_RPC={BLOCKCHAIN_RPC}")
        logger.info(f"[EXEC] Config: CONTRACT_ADDRESS={CONTRACT_ADDRESS}")
        logger.info(f"[EXEC] Config: IPFS_GATEWAY={IPFS_GATEWAY}")
        
        # Step 1: Fetch asset info from blockchain
        logger.info("[EXEC] Step 1: Fetching asset info from blockchain...")
        try:
            dataset_info = get_asset_info(dataset_id)
            logger.info(f"[EXEC] Dataset info: {dataset_info}")
        except Exception as e:
            logger.error(f"[EXEC] Error fetching dataset info: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to fetch dataset info: {e}"}), 500
        
        try:
            app_info = get_asset_info(application_id)
            print(f"[EXEC] App info: {app_info}")
        except Exception as e:
            print(f"[EXEC] Error fetching app info: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to fetch app info: {e}"}), 500
        
        if not dataset_info["active"]:
            print("[EXEC] Error: Dataset is not active")
            return jsonify({"success": False, "error": "Dataset is not active"}), 400
        if not app_info["active"]:
            print("[EXEC] Error: Application is not active")
            return jsonify({"success": False, "error": "Application is not active"}), 400
        
        # Step 2: Check access rights
        print("[EXEC] Step 2: Checking access rights...")
        print(f"[EXEC] hasAccess({user_address}, {dataset_info['encryptedUri']}, {app_info['encryptedUri']})")
        has_access = check_access(
            user_address,
            dataset_info["encryptedUri"],
            app_info["encryptedUri"]
        )
        print(f"[EXEC] Access result: {has_access}")
        
        if not has_access:
            print("[EXEC] Error: User does not have access")
            return jsonify({
                "success": False,
                "error": "User does not have access to this dataset-application combination"
            }), 403
        
        # Step 3: Fetch encrypted assets from IPFS
        print(f"[EXEC] Step 3: Fetching from IPFS...")
        print(f"[EXEC] Dataset URI: {dataset_info['encryptedUri']}")
        try:
            dataset_data = fetch_from_ipfs(dataset_info["encryptedUri"])
            print(f"[EXEC] Dataset fetched: {len(dataset_data)} bytes")
        except Exception as e:
            print(f"[EXEC] Error fetching dataset from IPFS: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to fetch dataset from IPFS: {e}"}), 500
        
        print(f"[EXEC] App URI: {app_info['encryptedUri']}")
        try:
            app_data = fetch_from_ipfs(app_info["encryptedUri"])
            print(f"[EXEC] App fetched: {len(app_data)} bytes")
        except Exception as e:
            print(f"[EXEC] Error fetching app from IPFS: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to fetch app from IPFS: {e}"}), 500
        
        # Step 4: Get decryption keys from local store
        print("[EXEC] Step 4: Getting decryption keys...")
        dataset_cid = dataset_info["encryptedUri"].replace("ipfs://", "")[:16]
        app_cid = app_info["encryptedUri"].replace("ipfs://", "")[:16]
        
        print(f"[EXEC] Looking for dataset key with prefix: {dataset_cid}")
        print(f"[EXEC] Looking for app key with prefix: {app_cid}")
        print(f"[EXEC] Available keys: {list(KEY_STORE.keys())}")
        
        dataset_key_info = KEY_STORE.get(dataset_cid)
        app_key_info = KEY_STORE.get(app_cid)
        
        if not dataset_key_info:
            print(f"[EXEC] Error: Dataset key not found for {dataset_cid}")
            return jsonify({"success": False, "error": f"Dataset key not found. Please re-register the dataset."}), 500
        
        if not app_key_info:
            print(f"[EXEC] Error: App key not found for {app_cid}")
            return jsonify({"success": False, "error": f"Application key not found. Please re-register the application."}), 500
        
        dataset_key = dataset_key_info["key"]
        app_key = app_key_info["key"]
        print(f"[EXEC] Keys found!")
        
        # Step 5: Run in SGX enclave
        print("[EXEC] Step 5: Running in SGX enclave...")
        result = run_in_enclave(dataset_data, app_data, dataset_key, app_key, params)
        print(f"[EXEC] Enclave result: {result}")
        
        # Step 6: Return results
        print("[EXEC] Step 6: Returning results")
        return jsonify({
            "success": result["success"],
            "output": result.get("output"),
            "error": result.get("error"),
            "executionTime": None,
        })
        
    except Exception as e:
        print(f"[EXEC] Unhandled exception: {e}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

