/**
 * SCONE CAS (Configuration and Attestation Service) Client
 * 
 * Uploads encryption keys directly to scone-cas.cf when registering assets.
 * The Executor retrieves these keys after SGX attestation during execution.
 */

const CAS_URL = process.env.NEXT_PUBLIC_CAS_URL || "https://scone-cas.cf:8081";

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

/**
 * Create a CAS session YAML for storing the encryption key
 */
export function createSessionYAML(config: CASSessionConfig): string {
  const keyName = `${config.assetType.toUpperCase()}_KEY`;
  return `name: ${config.sessionName}
version: "0.3.10"

security:
  attestation:
    tolerate: [debug-mode, hyperthreading, insecure-igpu, outdated-tcb, software-hardening-needed]
    ignore_advisories: "*"

services:
  - name: executor
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
 * Upload encryption key to CAS (scone-cas.cf)
 */
export async function uploadKeyToCAS(config: CASSessionConfig): Promise<{
  success: boolean;
  sessionName?: string;
  error?: string;
}> {
  try {
    const sessionYAML = createSessionYAML(config);
    
    const response = await fetch(`${CAS_URL}/session`, {
      method: "POST",
      body: sessionYAML,
    });

    const result = await response.text();

    if (result.includes("Created Session") || result.includes("hash")) {
      return {
        success: true,
        sessionName: config.sessionName,
      };
    }

    return {
      success: false,
      error: result,
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

