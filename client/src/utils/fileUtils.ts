/**
 * Calculate SHA-256 hash of a file
 */
export async function calculateFileHash(file: File): Promise<string> {
  const arrayBuffer = await file.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const hashHex = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
  return `0x${hashHex}`;
}

/**
 * Generate a random IPFS-like CID (simplified - not a real CID)
 * Format: ipfs://Qm[random 44 base58 chars]
 */
export function generateRandomIPFSUri(): string {
  // Generate a random hex string that looks like a CID
  const randomHex = Array.from(crypto.getRandomValues(new Uint8Array(32)))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  // Use a prefix that looks like IPFS CID (Qm is common for v0 CIDs)
  return `ipfs://Qm${randomHex.substring(0, 44)}`;
}

/**
 * Read file as ArrayBuffer
 */
export async function readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as ArrayBuffer);
    reader.onerror = reject;
    reader.readAsArrayBuffer(file);
  });
}

