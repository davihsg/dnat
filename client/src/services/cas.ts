/**
 * SCONE CAS (Configuration and Attestation Service) Client
 * 
 * Uploads encryption keys to CAS via Executor (which has the certificates).
 */

const EXECUTOR_URL = process.env.NEXT_PUBLIC_EXECUTOR_URL || "http://localhost:8081";

export interface CASSessionConfig {
  sessionName: string;
  encryptionKey: string;  // Base64-encoded key
  assetType: "dataset" | "application";
  ipfsHash: string;
}

/**
 * Generate a session name for an asset (based on IPFS hash for tracking)
 */
export function generateSessionName(assetType: string, ipfsHash: string): string {
  const hashPrefix = ipfsHash.slice(0, 16);
  return `dnat-${assetType}-${hashPrefix}`;
}

// MREnclave of the executor enclave (get from: SCONE_HASH=1 docker run <image>)
const MRENCLAVE = process.env.NEXT_PUBLIC_MRENCLAVE || "";

/**
 * Create a CAS session YAML for storing the encryption key
 */
function createSessionYAML(config: CASSessionConfig): string {
  const keyName = `${config.assetType.toUpperCase()}_KEY`;
  
  // If MREnclave is set, use strict attestation; otherwise permissive for testing
  const mrenclaveSection = MRENCLAVE 
    ? `    mrenclaves: [${MRENCLAVE}]`
    : `    # MREnclave not set - permissive mode for testing`;
  
  return `name: ${config.sessionName}
version: "0.3.10"

security:
  attestation:
    tolerate: [debug-mode, hyperthreading, insecure-igpu, outdated-tcb, software-hardening-needed]
    ignore_advisories: "*"

services:
  - name: executor
${mrenclaveSection}
    command: python /app/enclave/execute.py
    environment:
      ${keyName}: "$$SCONE::${keyName}$$"

secrets:
  - name: ${keyName}
    kind: ascii
    value: "${config.encryptionKey}"
`;
}

/**
 * Upload encryption key to CAS via Executor
 */
export async function uploadKeyToCAS(config: CASSessionConfig): Promise<{
  success: boolean;
  sessionName?: string;
  error?: string;
}> {
  try {
    const sessionYAML = createSessionYAML(config);
    
    const response = await fetch(`${EXECUTOR_URL}/cas/upload`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        sessionName: config.sessionName,
        sessionYAML: sessionYAML,
      }),
    });

    const result = await response.json();
    return {
      success: result.success,
      sessionName: config.sessionName,
      error: result.error,
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to upload key to CAS",
    };
  }
}

/**
 * Store key locally (fallback when CAS is not available)
 */
export function storeKeyLocally(ipfsHash: string, encryptionKey: string, sessionName: string): void {
  const keys = JSON.parse(localStorage.getItem("dnat_keys") || "{}");
  keys[ipfsHash] = {
    key: encryptionKey,
    sessionName: sessionName,
  };
  localStorage.setItem("dnat_keys", JSON.stringify(keys));
}

/**
 * Retrieve key from local storage
 */
export function getKeyLocally(ipfsHash: string): { key: string; sessionName: string } | null {
  const keys = JSON.parse(localStorage.getItem("dnat_keys") || "{}");
  return keys[ipfsHash] || null;
}

