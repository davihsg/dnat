import { create, IPFSHTTPClient } from "ipfs-http-client";

// IPFS client instance (singleton)
let ipfsClient: IPFSHTTPClient | null = null;

/**
 * Get or create IPFS client instance
 */
export function getIPFSClient(): IPFSHTTPClient {
  if (!ipfsClient) {
    // Connect to local IPFS node
    const ipfsApiUrl = process.env.NEXT_PUBLIC_IPFS_API_URL || "http://localhost:5001";
    console.log("Initializing IPFS client with URL:", ipfsApiUrl);
    
    // Create IPFS client with proper configuration
    ipfsClient = create({ 
      url: ipfsApiUrl,
      // Add timeout and retry configuration
      timeout: 30000, // 30 seconds
    });
  }
  return ipfsClient;
}

/**
 * Upload file/blob to IPFS and return CID
 */
export async function uploadToIPFS(data: Blob | File | string): Promise<string> {
  const client = getIPFSClient();
  
  try {
    // Convert string to Blob if needed
    let blob: Blob;
    if (typeof data === "string") {
      blob = new Blob([data], { type: "text/plain" });
    } else {
      blob = data;
    }

    // Add to IPFS
    const result = await client.add(blob, {
      pin: true, // Pin the content
    });

    return result.cid.toString();
  } catch (error) {
    console.error("Error uploading to IPFS:", error);
    throw new Error(
      `Failed to upload to IPFS: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
}

/**
 * Upload file and return CID with IPFS URI format
 */
export async function uploadFileToIPFS(file: File | Blob): Promise<string> {
  const cid = await uploadToIPFS(file);
  return `ipfs://${cid}`;
}

/**
 * Fetch content from IPFS using CID or IPFS URI
 */
export async function fetchFromIPFS(cidOrUri: string): Promise<Uint8Array> {
  const client = getIPFSClient();
  
  try {
    // Remove ipfs:// prefix if present
    const cleanCid = cidOrUri.replace(/^ipfs:\/\//, "");
    
    const chunks: Uint8Array[] = [];
    for await (const chunk of client.cat(cleanCid)) {
      chunks.push(chunk);
    }
    
    // Concatenate all chunks
    const totalLength = chunks.reduce((sum, chunk) => sum + chunk.length, 0);
    const result = new Uint8Array(totalLength);
    let offset = 0;
    for (const chunk of chunks) {
      result.set(chunk, offset);
      offset += chunk.length;
    }
    
    return result;
  } catch (error) {
    console.error("Error fetching from IPFS:", error);
    throw new Error(
      `Failed to fetch from IPFS: ${error instanceof Error ? error.message : "Unknown error"}`
    );
  }
}

/**
 * Check if IPFS node is available
 */
export async function checkIPFSConnection(): Promise<boolean> {
  try {
    const client = getIPFSClient();
    const version = await client.version();
    console.log("IPFS connection successful, version:", version);
    return true;
  } catch (error) {
    console.error("IPFS connection failed:", error);
    // Try direct HTTP check as fallback
    try {
      const apiUrl = process.env.NEXT_PUBLIC_IPFS_API_URL || "http://localhost:5001";
      const response = await fetch(`${apiUrl}/api/v0/version`);
      if (response.ok) {
        console.log("IPFS HTTP check successful");
        return true;
      }
    } catch (httpError) {
      console.error("IPFS HTTP check also failed:", httpError);
    }
    return false;
  }
}

