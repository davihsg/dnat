import { getContractAddress } from "@/config/contract";
import { contractABI } from "@/config/contract";
import { createPublicClient, http } from "viem";
import { hardhat, localhost, sepolia, polygon, mainnet } from "viem/chains";
import { supportedChains } from "@/config/chains";

/**
 * Get chain configuration for viem
 */
function getChainForViem(chainId: number) {
  if (chainId === 31337 || chainId === 1337) return localhost;
  if (chainId === 11155111) return sepolia;
  if (chainId === 137) return polygon;
  if (chainId === 1) return mainnet;
  return hardhat;
}

/**
 * Search for asset ID by encrypted URI hash
 */
export async function findAssetIdByHash(
  encryptedHash: string,
  chainId: number
): Promise<number | null> {
  const contractAddress = getContractAddress(chainId);
  if (!contractAddress) {
    throw new Error("Contract not deployed on this network");
  }

  // Normalize hash
  let normalizedHash = encryptedHash.trim();
  if (!normalizedHash.startsWith("ipfs://")) {
    normalizedHash = `ipfs://${normalizedHash}`;
  }

  // Create public client for reading
  const chain = getChainForViem(chainId);
  const rpcUrl = supportedChains.find(c => c.id === chainId)?.rpcUrls?.default?.http?.[0] || "http://localhost:8545";
  
  const publicClient = createPublicClient({
    chain,
    transport: http(rpcUrl),
  });

  try {
    // Get next asset ID to know how many to search
    const nextId = await publicClient.readContract({
      address: contractAddress,
      abi: contractABI,
      functionName: "nextAssetId",
    });

    const maxId = Number(nextId);
    if (maxId === 0) return null;

    // Search through assets (limit to first 100 for performance)
    const searchLimit = Math.min(100, maxId);
    for (let id = 1; id <= searchLimit; id++) {
      try {
        const asset = await publicClient.readContract({
          address: contractAddress,
          abi: contractABI,
          functionName: "getAsset",
          args: [BigInt(id)],
        });

        if (asset[2] === normalizedHash) {
          // Found matching encryptedUri
          return id;
        }
      } catch (error) {
        // Asset might not exist, continue searching
        continue;
      }
    }

    return null;
  } catch (error) {
    console.error("Error searching for asset:", error);
    throw error;
  }
}

