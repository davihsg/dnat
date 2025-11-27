import { useNextAssetId } from "./useContract";
import { useMemo } from "react";

export interface Asset {
  id: number;
  assetType: number; // 0 = Dataset, 1 = Application
  owner: `0x${string}`;
  encryptedUri: string;
  manifestUri: string;
  contentHash: `0x${string}`;
  price: bigint;
  bloomFilter: `0x${string}`;
  active: boolean;
}

/**
 * Hook to get asset IDs
 * Components should use useAsset(id) to fetch individual assets
 * This avoids hooks-in-loops issues
 */
export function useAssetIds() {
  const { data: nextAssetId, isLoading, error } = useNextAssetId();

  const assetIds = useMemo(() => {
    if (!nextAssetId) return [];
    const ids: number[] = [];
    for (let i = 1; i <= Number(nextAssetId); i++) {
      ids.push(i);
    }
    return ids;
  }, [nextAssetId]);

  return {
    assetIds,
    isLoading,
    error,
    totalCount: assetIds.length,
  };
}

/**
 * Hook to filter asset IDs by type
 * Note: This requires fetching each asset to check its type
 * In production, use multicall or an indexer for better performance
 */
export function useAssetIdsByType(assetType: 0 | 1 | null = null) {
  const { assetIds, isLoading, error, totalCount } = useAssetIds();
  
  // Return all IDs - components will filter by fetching and checking type
  // This is a limitation - in production use multicall or indexer
  return {
    assetIds,
    isLoading,
    error,
    totalCount,
  };
}

/**
 * Hook to get datasets only
 * Returns asset IDs - components should fetch individually
 */
export function useDatasets() {
  const { assetIds, isLoading, error, totalCount } = useAssetIds();
  
  return {
    assetIds, // Components will need to fetch and filter
    isLoading,
    error,
    totalCount,
    // Helper to check if an ID is a dataset (requires fetching)
    isDataset: async (id: number) => {
      // This would need to fetch the asset - simplified for now
      return true;
    },
  };
}

/**
 * Hook to get applications only
 * Returns asset IDs - components should fetch individually
 */
export function useApplications() {
  const { assetIds, isLoading, error, totalCount } = useAssetIds();
  
  return {
    assetIds, // Components will need to fetch and filter
    isLoading,
    error,
    totalCount,
  };
}

/**
 * Helper to convert asset data from contract to Asset interface
 */
export function assetFromContractData(
  id: number,
  data: [
    number,
    `0x${string}`,
    string,
    string,
    `0x${string}`,
    bigint,
    `0x${string}`,
    boolean
  ]
): Asset {
  return {
    id,
    assetType: data[0],
    owner: data[1],
    encryptedUri: data[2],
    manifestUri: data[3],
    contentHash: data[4],
    price: data[5],
    bloomFilter: data[6],
    active: data[7],
  };
}
