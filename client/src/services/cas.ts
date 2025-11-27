/**
 * SCONE CAS (Configuration and Attestation Service) Client
 * 
 * This service uploads encryption keys to CAS when registering assets.
 * The Executor can then retrieve these keys after SGX attestation.
 */

// CAS API endpoint
const CAS_URL = process.env.NEXT_PUBLIC_CAS_URL || "https://scone-cas.cf:8081";

// Client certificate paths (for CAS authentication)
// In production, these would be securely stored
const CERT_PATH = process.env.NEXT_PUBLIC_CAS_CERT_PATH || "/certs/client.crt";
const KEY_PATH = process.env.NEXT_PUBLIC_CAS_KEY_PATH || "/certs/client.key";

export interface CASSessionConfig {
  sessionName: string;
  encryptionKey: string;  // Base64-encoded key
  assetType: "dataset" | "application";
  assetId?: string;
  ipfsHash: string;
}

/**
 * Generate a unique session name for an asset
 */
export function generateSessionName(assetType: string, ipfsHash: string): string {
  const timestamp = Date.now();
  const hashPrefix = ipfsHash.slice(0, 8);
  return `dnat-${assetType}-${hashPrefix}-${timestamp}`;
}

/**
 * Create a CAS session YAML for storing the encryption key
 */
export function createSessionYAML(config: CASSessionConfig): string {
  return `name: ${config.sessionName}
version: "0.3.10"

security:
  attestation:
    tolerate: [debug-mode, hyperthreading, insecure-igpu, outdated-tcb, software-hardening-needed]
    ignore_advisories: "*"

services:
  - name: executor
    command: python /app/enclave/execute.py

secrets:
  - name: ${config.assetType.toUpperCase()}_KEY
    kind: ascii
    value: "${config.encryptionKey}"
`;
}

/**
 * Upload encryption key to CAS
 * 
 * Note: In a browser environment, we can't directly make requests to CAS
 * due to CORS and certificate requirements. Instead, we'll call the
 * Executor API which will handle the CAS upload server-side.
 */
export async function uploadKeyToCAS(config: CASSessionConfig): Promise<{
  success: boolean;
  sessionName?: string;
  error?: string;
}> {
  const EXECUTOR_API_URL = process.env.NEXT_PUBLIC_EXECUTOR_URL || "http://localhost:8082";
  
  try {
    const response = await fetch(`${EXECUTOR_API_URL}/cas/upload-key`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        sessionName: config.sessionName,
        encryptionKey: config.encryptionKey,
        assetType: config.assetType,
        ipfsHash: config.ipfsHash,
      }),
    });

    const result = await response.json();

    if (!response.ok) {
      return {
        success: false,
        error: result.error || `CAS upload failed: ${response.status}`,
      };
    }

    return {
      success: true,
      sessionName: result.sessionName,
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
 * This stores the key in localStorage - NOT secure for production!
 */
export function storeKeyLocally(ipfsHash: string, encryptionKey: string): void {
  const keys = JSON.parse(localStorage.getItem("dnat_keys") || "{}");
  keys[ipfsHash] = {
    key: encryptionKey,
    timestamp: Date.now(),
  };
  localStorage.setItem("dnat_keys", JSON.stringify(keys));
}

/**
 * Retrieve key from local storage
 */
export function getKeyLocally(ipfsHash: string): string | null {
  const keys = JSON.parse(localStorage.getItem("dnat_keys") || "{}");
  return keys[ipfsHash]?.key || null;
}

