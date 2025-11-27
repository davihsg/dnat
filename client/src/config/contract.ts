// Contract addresses per network
// Update these after deploying the contract to each network
export const contractAddresses: Record<number, `0x${string}`> = {
  // Localhost / Hardhat
  31337: "0x5FbDB2315678afecb367f032d93F642f64180aa3", // Update after deployment
  // Sepolia
  11155111: "0x0000000000000000000000000000000000000000", // Update after deployment
  // Polygon
  137: "0x0000000000000000000000000000000000000000", // Update after deployment
  // Ethereum Mainnet
  1: "0x0000000000000000000000000000000000000000", // Update after deployment
};

/**
 * Get contract address for a given chain ID
 */
export function getContractAddress(chainId: number): `0x${string}` | undefined {
  return contractAddresses[chainId];
}

// Contract ABI - will be imported from smart-contract deployments
// For now, we'll define it here. In production, import from the deployment artifacts
export const contractABI = [
  {
    inputs: [
      { internalType: "uint8", name: "assetType", type: "uint8" },
      { internalType: "string", name: "encryptedUri", type: "string" },
      { internalType: "string", name: "manifestUri", type: "string" },
      { internalType: "bytes32", name: "contentHash", type: "bytes32" },
      { internalType: "uint256", name: "price", type: "uint256" },
      { internalType: "bytes", name: "bloomFilter", type: "bytes" },
    ],
    name: "registerAsset",
    outputs: [{ internalType: "uint256", name: "id", type: "uint256" }],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [
      { internalType: "uint256", name: "assetId", type: "uint256" },
      { internalType: "uint256", name: "newPrice", type: "uint256" },
      { internalType: "bool", name: "newActive", type: "bool" },
    ],
    name: "updateAsset",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [{ internalType: "uint256", name: "assetId", type: "uint256" }],
    name: "revokeAsset",
    outputs: [],
    stateMutability: "nonpayable",
    type: "function",
  },
  {
    inputs: [
      { internalType: "uint256", name: "datasetId", type: "uint256" },
      { internalType: "uint256", name: "applicationId", type: "uint256" },
    ],
    name: "purchaseAccess",
    outputs: [],
    stateMutability: "payable",
    type: "function",
  },
  {
    inputs: [
      { internalType: "address", name: "user", type: "address" },
      { internalType: "string", name: "encryptedDatasetHash", type: "string" },
      { internalType: "string", name: "encryptedApplicationHash", type: "string" },
    ],
    name: "hasAccess",
    outputs: [{ internalType: "bool", name: "", type: "bool" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "address", name: "user", type: "address" },
      { internalType: "uint256", name: "datasetId", type: "uint256" },
      { internalType: "uint256", name: "applicationId", type: "uint256" },
    ],
    name: "hasAccessByIds",
    outputs: [{ internalType: "bool", name: "", type: "bool" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [{ internalType: "uint256", name: "assetId", type: "uint256" }],
    name: "getAsset",
    outputs: [
      { internalType: "uint8", name: "assetType", type: "uint8" },
      { internalType: "address", name: "owner", type: "address" },
      { internalType: "string", name: "encryptedUri", type: "string" },
      { internalType: "string", name: "manifestUri", type: "string" },
      { internalType: "bytes32", name: "contentHash", type: "bytes32" },
      { internalType: "uint256", name: "price", type: "uint256" },
      { internalType: "bytes", name: "bloomFilter", type: "bytes" },
      { internalType: "bool", name: "active", type: "bool" },
    ],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [],
    name: "nextAssetId",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
  {
    inputs: [
      { internalType: "uint256", name: "", type: "uint256" },
      { internalType: "uint256", name: "", type: "uint256" },
      { internalType: "address", name: "", type: "address" },
    ],
    name: "accessRights",
    outputs: [{ internalType: "bool", name: "", type: "bool" }],
    stateMutability: "view",
    type: "function",
  },
  {
    anonymous: false,
    inputs: [
      { indexed: true, internalType: "uint256", name: "id", type: "uint256" },
      { indexed: false, internalType: "uint8", name: "assetType", type: "uint8" },
      { indexed: true, internalType: "address", name: "owner", type: "address" },
      { indexed: false, internalType: "string", name: "encryptedUri", type: "string" },
      { indexed: false, internalType: "string", name: "manifestUri", type: "string" },
      { indexed: false, internalType: "bytes32", name: "contentHash", type: "bytes32" },
      { indexed: false, internalType: "uint256", name: "price", type: "uint256" },
      { indexed: false, internalType: "bool", name: "hasBloomFilter", type: "bool" },
    ],
    name: "AssetRegistered",
    type: "event",
  },
  {
    anonymous: false,
    inputs: [
      { indexed: true, internalType: "uint256", name: "datasetId", type: "uint256" },
      { indexed: true, internalType: "uint256", name: "applicationId", type: "uint256" },
      { indexed: true, internalType: "address", name: "user", type: "address" },
      { indexed: false, internalType: "uint256", name: "datasetPrice", type: "uint256" },
      { indexed: false, internalType: "uint256", name: "applicationPrice", type: "uint256" },
    ],
    name: "AccessPurchased",
    type: "event",
  },
] as const;

