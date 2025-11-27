/**
 * Extract CID from IPFS URI
 * Supports formats: ipfs://Qm..., ipfs:///Qm..., /ipfs/Qm..., or just Qm...
 */
export function extractCID(ipfsUri: string): string {
  // Remove ipfs:// prefix
  let cid = ipfsUri.replace(/^ipfs:\/\//, "").replace(/^\/ipfs\//, "");
  
  // If it still has /ipfs/ prefix, remove it
  cid = cid.replace(/^\/ipfs\//, "");
  
  return cid;
}

/**
 * Convert IPFS URI to HTTP gateway URL
 * Supports formats: ipfs://Qm..., ipfs:///Qm..., /ipfs/Qm...
 */
export function ipfsUriToGatewayUrl(ipfsUri: string, gateway: string = "http://localhost:8080/ipfs/"): string {
  const cid = extractCID(ipfsUri);
  return `${gateway}${cid}`;
}

/**
 * Fetch content from IPFS
 */
export async function fetchFromIPFS(ipfsUri: string): Promise<string> {
  const url = ipfsUriToGatewayUrl(ipfsUri);
  
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch from IPFS: ${response.statusText}`);
    }
    return await response.text();
  } catch (error) {
    throw new Error(`Error fetching from IPFS: ${error instanceof Error ? error.message : "Unknown error"}`);
  }
}

/**
 * Parse YAML-like string to object (simplified parser)
 * For production, use a proper YAML parser like 'js-yaml'
 */
export function parseYAML(yaml: string): Record<string, any> {
  const result: Record<string, any> = {};
  const lines = yaml.split("\n");
  let currentKey = "";
  let currentValue = "";
  let indentLevel = 0;
  
  for (const line of lines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    
    const match = trimmed.match(/^([^:]+):\s*(.*)$/);
    if (match) {
      const [, key, value] = match;
      if (value) {
        // Simple value
        result[key.trim()] = value.trim().replace(/^["']|["']$/g, "");
      } else {
        // Key with nested value
        currentKey = key.trim();
        result[currentKey] = {};
      }
    } else if (trimmed.startsWith("-")) {
      // Array item
      const value = trimmed.replace(/^-\s*/, "").replace(/^["']|["']$/g, "");
      if (!result[currentKey]) result[currentKey] = [];
      result[currentKey].push(value);
    } else {
      // Continuation of previous value
      if (currentKey && result[currentKey]) {
        result[currentKey] += " " + trimmed.replace(/^["']|["']$/g, "");
      }
    }
  }
  
  return result;
}

