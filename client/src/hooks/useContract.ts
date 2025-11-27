import { useReadContract, useWriteContract, useWaitForTransactionReceipt } from "wagmi";
import { useChainId } from "wagmi";
import { contractABI, getContractAddress } from "@/config/contract";
import { parseEther } from "viem";

/**
 * Hook for reading contract data
 */
export function useContractRead<T = any>(
  functionName: string,
  args?: readonly unknown[]
) {
  const chainId = useChainId();
  const address = getContractAddress(chainId);

  return useReadContract({
    address,
    abi: contractABI,
    functionName: functionName as any,
    args: args as any,
    query: {
      enabled: !!address,
    },
  }) as { data: T; isLoading: boolean; error: Error | null };
}

/**
 * Hook for writing to contract
 */
export function useContractWrite() {
  const chainId = useChainId();
  const address = getContractAddress(chainId);

  const { writeContract, data: hash, isPending, error } = useWriteContract();

  const write = async (
    functionName: string,
    args?: readonly unknown[],
    value?: bigint
  ) => {
    if (!address) {
      throw new Error("Contract not deployed on this network");
    }

    return writeContract({
      address,
      abi: contractABI,
      functionName: functionName as any,
      args: args as any,
      value: value,
    });
  };

  return {
    write,
    hash,
    isPending,
    error,
  };
}

/**
 * Hook for waiting for transaction receipt
 */
export function useWaitForTransaction(hash: `0x${string}` | undefined) {
  return useWaitForTransactionReceipt({
    hash,
  });
}

/**
 * Hook to get next asset ID
 */
export function useNextAssetId() {
  return useContractRead<bigint>("nextAssetId");
}

/**
 * Hook to get asset details
 */
export function useAsset(assetId: bigint | number | undefined) {
  return useContractRead<
    [
      number,
      `0x${string}`,
      string,
      string,
      `0x${string}`,
      bigint,
      `0x${string}`,
      boolean
    ]
  >("getAsset", assetId !== undefined ? [BigInt(assetId)] : undefined);
}

/**
 * Hook to check access rights using encrypted hashes
 */
export function useHasAccess(
  user: `0x${string}` | undefined,
  encryptedDatasetHash: string | undefined,
  encryptedApplicationHash: string | undefined
) {
  return useContractRead<boolean>(
    "hasAccess",
    user && encryptedDatasetHash && encryptedApplicationHash
      ? [user, encryptedDatasetHash, encryptedApplicationHash]
      : undefined
  );
}

/**
 * Hook to check access rights using asset IDs (legacy)
 */
export function useHasAccessByIds(
  user: `0x${string}` | undefined,
  datasetId: bigint | number | undefined,
  applicationId: bigint | number | undefined
) {
  return useContractRead<boolean>(
    "hasAccessByIds",
    user && datasetId !== undefined && applicationId !== undefined
      ? [user, BigInt(datasetId), BigInt(applicationId)]
      : undefined
  );
}

