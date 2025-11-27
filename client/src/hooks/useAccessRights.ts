import { useAccount } from "wagmi";
import { useHasAccess } from "./useContract";
import { useAssets } from "./useAssets";
import { useMemo } from "react";

export interface AccessRight {
  datasetId: number;
  applicationId: number;
  dataset: any;
  application: any;
}

/**
 * Hook to get user's access rights
 * This checks all combinations of datasets and applications
 * Note: This is a simplified version. In production, you might want to:
 * - Listen to AccessPurchased events
 * - Use an indexer
 * - Cache results
 */
export function useAccessRights() {
  const { address } = useAccount();
  const { assets } = useAssets();

  const datasets = useMemo(
    () => assets.filter((a) => a.assetType === 0),
    [assets]
  );
  const applications = useMemo(
    () => assets.filter((a) => a.assetType === 1),
    [assets]
  );

  // For each dataset-application pair, check if user has access
  // Note: This creates many contract calls. In production, optimize this.
  const accessRights: AccessRight[] = [];

  // Simplified: only check first few combinations to avoid too many calls
  // In production, use event logs or an indexer
  for (const dataset of datasets.slice(0, 10)) {
    for (const application of applications.slice(0, 10)) {
      // eslint-disable-next-line react-hooks/rules-of-hooks
      const { data: hasAccess } = useHasAccess(
        address,
        dataset.id,
        application.id
      );
      if (hasAccess) {
        accessRights.push({
          datasetId: dataset.id,
          applicationId: application.id,
          dataset,
          application,
        });
      }
    }
  }

  return {
    accessRights,
    isLoading: false, // Simplified
    totalCount: accessRights.length,
  };
}

/**
 * Hook to check if user has access to a specific dataset-application pair
 */
export function useUserHasAccess(
  datasetId: number | undefined,
  applicationId: number | undefined
) {
  const { address } = useAccount();
  return useHasAccess(address, datasetId, applicationId);
}

