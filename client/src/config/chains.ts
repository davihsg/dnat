import { hardhat, localhost, sepolia, polygon, mainnet } from "viem/chains";

/**
 * Supported EVM chains configuration
 * Easy to add new chains by importing from viem/chains
 */
export const supportedChains = [
  {
    ...localhost,
    name: "Localhost",
    rpcUrls: {
      default: {
        http: ["http://127.0.0.1:8545"],
      },
    },
  },
  hardhat,
  sepolia,
  polygon,
  mainnet,
];

/**
 * Get chain by ID
 */
export function getChainById(chainId: number) {
  return supportedChains.find((chain) => chain.id === chainId);
}

/**
 * Default chain (localhost for development)
 */
export const defaultChain = localhost;

