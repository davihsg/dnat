"use client";

import { useEffect, useState } from "react";
import { useAccount, usePublicClient } from "wagmi";
import { useChainId } from "wagmi";
import { getContractAddress, contractABI } from "@/config/contract";
import { parseAbiItem } from "viem";

export interface AccessPurchase {
  datasetId: bigint;
  applicationId: bigint;
  user: `0x${string}`;
  datasetPrice: bigint;
  applicationPrice: bigint;
  blockNumber: bigint;
  transactionHash: `0x${string}`;
}

/**
 * Hook to fetch AccessPurchased events for the current user
 */
export function useAccessPurchases() {
  const { address } = useAccount();
  const chainId = useChainId();
  const publicClient = usePublicClient();
  const [purchases, setPurchases] = useState<AccessPurchase[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchPurchases() {
      if (!address || !publicClient) {
        setPurchases([]);
        setIsLoading(false);
        return;
      }

      const contractAddress = getContractAddress(chainId);
      if (!contractAddress) {
        setError(new Error("Contract not deployed on this network"));
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        setError(null);

        // Fetch AccessPurchased events for the current user
        const logs = await publicClient.getLogs({
          address: contractAddress,
          event: parseAbiItem(
            "event AccessPurchased(uint256 indexed datasetId, uint256 indexed applicationId, address indexed user, uint256 datasetPrice, uint256 applicationPrice)"
          ),
          args: {
            user: address,
          },
          fromBlock: 0n,
          toBlock: "latest",
        });

        const parsedPurchases: AccessPurchase[] = logs.map((log) => ({
          datasetId: log.args.datasetId!,
          applicationId: log.args.applicationId!,
          user: log.args.user!,
          datasetPrice: log.args.datasetPrice!,
          applicationPrice: log.args.applicationPrice!,
          blockNumber: log.blockNumber,
          transactionHash: log.transactionHash,
        }));

        setPurchases(parsedPurchases);
      } catch (err) {
        console.error("Error fetching purchases:", err);
        setError(err instanceof Error ? err : new Error("Failed to fetch purchases"));
      } finally {
        setIsLoading(false);
      }
    }

    fetchPurchases();
  }, [address, chainId, publicClient]);

  return {
    purchases,
    isLoading,
    error,
    refetch: () => {
      setIsLoading(true);
    },
  };
}

