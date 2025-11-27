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

# Configuration
BLOCKCHAIN_RPC = os.environ.get("BLOCKCHAIN_RPC", "http://localhost:8545")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS", "0x5FbDB2315678afecb367f032d93F642f64180aa3")
IPFS_GATEWAY = os.environ.get("IPFS_GATEWAY", "http://localhost:8080/ipfs")
ENCLAVE_PATH = os.environ.get("ENCLAVE_PATH", "/app/enclave")

# CAS Configuration
CAS_URL = os.environ.get("SCONE_CAS_ADDR", "scone-cas.cf")
CAS_CERT = os.environ.get("CAS_CERT", "/app/certs/client.crt")
CAS_KEY = os.environ.get("CAS_KEY", "/app/certs/client.key")
MRENCLAVE = os.environ.get("MRENCLAVE", "")

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
        logger.error(f"Access check failed: {e}")
        return False


def create_execution_session(dataset_session: str, app_session: str, execution_id: str) -> tuple[bool, str]:
    """
    Create a CAS session for execution that imports keys from asset sessions.
    
    According to SCONE CAS docs, secrets can be imported from other sessions:
    https://sconedocs.github.io/CAS_session_lang_0_3/#secret-sharing
    
    Returns (success, session_name or error).
    """
    session_name = f"dnat-executor"
    
    # Upload to CAS
    try:
        if not os.path.exists(CAS_CERT) or not os.path.exists(CAS_KEY):
            return False, f"CAS certificates not found: {CAS_CERT}, {CAS_KEY}"
        
        # First, try to get the existing session hash (for updates)
        predecessor_hash = None
        get_cmd = [
            "curl", "-k", "-s",
            "--cert", CAS_CERT,
            "--key", CAS_KEY,
            f"https://{CAS_URL}:8081/session/{session_name}"
        ]
        
        get_result = subprocess.run(get_cmd, capture_output=True, text=True, timeout=30)
        if get_result.returncode == 0 and "hash" in get_result.stdout:
            try:
                existing = json.loads(get_result.stdout)
                predecessor_hash = existing.get("hash")
                logger.info(f"[CAS] Found existing session, predecessor hash: {predecessor_hash}")
            except json.JSONDecodeError:
                pass
        
        # Build session YAML that imports keys from asset sessions
        mrenclave_line = f"    mrenclaves: [{MRENCLAVE}]" if MRENCLAVE else ""
        predecessor_line = f"predecessor: {predecessor_hash}" if predecessor_hash else ""
        
        session_yaml = f"""name: {session_name}
version: "0.3.10"
{predecessor_line}

security:
  attestation:
    tolerate: [debug-mode, hyperthreading, insecure-igpu, outdated-tcb, software-hardening-needed]
    ignore_advisories: "*"

services:
  - name: executor
{mrenclave_line}
    command: python /app/execute.py
    environment:
      DATASET_KEY: "$$SCONE::DATASET_KEY$$"
      APP_KEY: "$$SCONE::APP_KEY$$"

secrets:
  - name: DATASET_KEY
    kind: ascii
    import:
      session: {dataset_session}
      secret: DATASET_KEY
  - name: APP_KEY
    kind: ascii
    import:
      session: {app_session}
      secret: APPLICATION_KEY
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(session_yaml)
            yaml_path = f.name
        
        cmd = [
            "curl", "-k", "-s",
            "--cert", CAS_CERT,
            "--key", CAS_KEY,
            "--data-binary", f"@{yaml_path}",
            "-X", "POST",
            f"https://{CAS_URL}:8081/session"
        ]
        
        logger.info(f"[CAS] Creating/updating execution session: {session_name}")
        logger.info(f"[CAS] Importing DATASET_KEY from: {dataset_session}")
        logger.info(f"[CAS] Importing APP_KEY from: {app_session}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        os.unlink(yaml_path)
        
        logger.info(f"[CAS] Response: {result.stdout}")
        
        if "hash" in result.stdout or "Created Session" in result.stdout:
            return True, session_name
        else:
            return False, result.stdout or result.stderr or "Unknown error"
            
    except Exception as e:
        logger.exception(f"[CAS] Error creating execution session: {e}")
        return False, str(e)


def run_in_enclave(dataset_data: bytes, app_data: bytes, session_name: str, params: dict = None) -> dict:
    """
    Run the application over the dataset inside the SGX enclave.
    
    Spawns a Docker container with the SCONE-enabled image.
    The enclave:
    1. Receives encrypted data
    2. Gets keys from SCONE CAS (injected after attestation)
    3. Decrypts and runs the application
    4. Returns results
    """
    # Create temp directory for data exchange
    data_dir = tempfile.mkdtemp()
    dataset_path = os.path.join(data_dir, "dataset.enc")
    app_path = os.path.join(data_dir, "application.enc")
    params_path = os.path.join(data_dir, "params.json")
    
    # Write data to temp files
    with open(dataset_path, 'wb') as f:
        f.write(dataset_data)
    with open(app_path, 'wb') as f:
        f.write(app_data)
    with open(params_path, 'w') as f:
        json.dump(params or {}, f)
    
    try:
        # Spawn Docker container with SCONE enclave
        enclave_image = os.environ.get("ENCLAVE_IMAGE", "dnat-enclave")
        cas_url = os.environ.get("SCONE_CAS_ADDR", "scone-cas.cf")
        las_addr = os.environ.get("SCONE_LAS_ADDR", "localhost")
        
        # SCONE_CONFIG_ID = <session_name>/<service_name>
        scone_config_id = f"{session_name}/executor"
        
        cmd = [
            "docker", "run", "--rm",
            "--device=/dev/sgx_enclave:/dev/sgx_enclave",
            "--device=/dev/sgx_provision:/dev/sgx_provision",
            "--network=host",
            "-v", f"{data_dir}:/data:ro",
            "-e", f"SCONE_CAS_ADDR={cas_url}",
            "-e", f"SCONE_LAS_ADDR={las_addr}",
            "-e", f"SCONE_CONFIG_ID={scone_config_id}",
            "-e", "SCONE_MODE=HW",
            "-e", "SCONE_LOG=3",
            "-e", "SCONE_ALLOW_DLOPEN=2",
            enclave_image,
            "python", "/app/execute.py"
        ]
        
        logger.info(f"[ENCLAVE] Running: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        logger.info(f"[ENCLAVE] Exit code: {result.returncode}")
        logger.info(f"[ENCLAVE] Stdout: {result.stdout}")
        if result.stderr:
            logger.info(f"[ENCLAVE] Stderr: {result.stderr}")
        
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
        logger.exception(f"[ENCLAVE] Error: {e}")
        return {
            "success": False,
            "error": str(e),
        }
    finally:
        # Clean up temp files
        import shutil
        shutil.rmtree(data_dir, ignore_errors=True)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/cas/upload", methods=["POST"])
def cas_upload():
    """
    Upload a session to CAS (creates or updates).
    
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
        
        # First, check if session already exists (get predecessor hash)
        predecessor_hash = None
        if session_name:
            get_cmd = [
                "curl", "-k", "-s",
                "--cert", CAS_CERT,
                "--key", CAS_KEY,
                f"https://{CAS_URL}:8081/session/{session_name}"
            ]
            get_result = subprocess.run(get_cmd, capture_output=True, text=True, timeout=30)
            if get_result.returncode == 0 and "hash" in get_result.stdout:
                try:
                    existing = json.loads(get_result.stdout)
                    predecessor_hash = existing.get("hash")
                    logger.info(f"[CAS] Found existing session, predecessor hash: {predecessor_hash}")
                except json.JSONDecodeError:
                    pass
        
        # If predecessor exists, insert it into the YAML after version line
        if predecessor_hash:
            lines = session_yaml.split('\n')
            new_lines = []
            for line in lines:
                new_lines.append(line)
                if line.startswith('version:'):
                    new_lines.append(f'predecessor: {predecessor_hash}')
            session_yaml = '\n'.join(new_lines)
            logger.info(f"[CAS] Updated session YAML with predecessor")
        
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
            return jsonify({"success": True, "sessionName": session_name, "response": response_text})
        else:
            logger.error(f"[CAS] Failed! Response: {response_text}")
            return jsonify({"success": False, "error": response_text or result.stderr or "Unknown error"}), 500
            
    except Exception as e:
        logger.exception(f"[CAS] Exception: {e}")
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
            logger.info(f"[EXEC] App info: {app_info}")
        except Exception as e:
            logger.error(f"[EXEC] Error fetching app info: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to fetch app info: {e}"}), 500
        
        if not dataset_info["active"]:
            logger.error("[EXEC] Error: Dataset is not active")
            return jsonify({"success": False, "error": "Dataset is not active"}), 400
        if not app_info["active"]:
            logger.error("[EXEC] Error: Application is not active")
            return jsonify({"success": False, "error": "Application is not active"}), 400
        
        # Step 2: Check access rights
        logger.info("[EXEC] Step 2: Checking access rights...")
        logger.info(f"[EXEC] hasAccess({user_address}, {dataset_info['encryptedUri']}, {app_info['encryptedUri']})")
        has_access = check_access(
            user_address,
            dataset_info["encryptedUri"],
            app_info["encryptedUri"]
        )
        logger.info(f"[EXEC] Access result: {has_access}")
        
        if not has_access:
            logger.error("[EXEC] Error: User does not have access")
            return jsonify({
                "success": False,
                "error": "User does not have access to this dataset-application combination"
            }), 403
        
        # Step 3: Fetch encrypted assets from IPFS
        logger.info(f"[EXEC] Step 3: Fetching from IPFS...")
        logger.info(f"[EXEC] Dataset URI: {dataset_info['encryptedUri']}")
        try:
            dataset_data = fetch_from_ipfs(dataset_info["encryptedUri"])
            logger.info(f"[EXEC] Dataset fetched: {len(dataset_data)} bytes")
        except Exception as e:
            logger.error(f"[EXEC] Error fetching dataset from IPFS: {e}")
            traceback.print_exc()
            return jsonify({"success": False, "error": f"Failed to fetch dataset from IPFS: {e}"}), 500
        
        logger.info(f"[EXEC] App URI: {app_info['encryptedUri']}")
        try:
            app_data = fetch_from_ipfs(app_info["encryptedUri"])
            logger.info(f"[EXEC] App fetched: {len(app_data)} bytes")
        except Exception as e:
            logger.error(f"[EXEC] Error fetching app from IPFS: {e}")
            return jsonify({"success": False, "error": f"Failed to fetch app from IPFS: {e}"}), 500
        
        # Step 4: Derive CAS session names from IPFS hashes
        logger.info("[EXEC] Step 4: Deriving CAS session names...")
        dataset_cid = dataset_info["encryptedUri"].replace("ipfs://", "")[:16]
        app_cid = app_info["encryptedUri"].replace("ipfs://", "")[:16]
        
        # Session names match what client created during registration
        dataset_session = f"dnat-dataset-{dataset_cid}"
        app_session = f"dnat-application-{app_cid}"
        
        logger.info(f"[EXEC] Dataset session: {dataset_session}")
        logger.info(f"[EXEC] App session: {app_session}")
        
        # Step 5: Create execution session that imports keys from asset sessions
        logger.info("[EXEC] Step 5: Creating execution session in CAS...")
        import time
        execution_id = str(int(time.time()))
        
        success, result_or_error = create_execution_session(dataset_session, app_session, execution_id)
        if not success:
            return jsonify({"success": False, "error": f"Failed to create CAS session: {result_or_error}"}), 500
        
        session_name = result_or_error
        logger.info(f"[EXEC] Execution session created: {session_name}")
        
        # Step 6: Run in SGX enclave
        logger.info("[EXEC] Step 6: Running in SGX enclave...")
        result = run_in_enclave(dataset_data, app_data, session_name, params)
        logger.info(f"[EXEC] Enclave result: {result}")
        
        # Step 7: Return results
        logger.info("[EXEC] Step 7: Returning results")
        return jsonify({
            "success": result["success"],
            "output": result.get("output"),
            "error": result.get("error"),
            "executionTime": None,
        })
        
    except Exception as e:
        logger.exception(f"[EXEC] Unhandled exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    debug = os.environ.get("DEBUG", "false").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)

