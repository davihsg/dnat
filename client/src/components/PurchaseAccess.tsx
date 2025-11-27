"use client";

import { useState, useEffect } from "react";
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
} from "@mui/material";
import { useAccount, useChainId } from "wagmi";
import { useContractWrite, useWaitForTransaction, useAsset } from "@/hooks/useContract";
import { getErrorMessage } from "@/utils/errors";
import { formatEth, formatPrice } from "@/utils/formatting";
import { findAssetIdByHash } from "@/utils/assetSearch";

export default function PurchaseAccess() {
  const { address } = useAccount();
  const chainId = useChainId();
  const [datasetHash, setDatasetHash] = useState("");
  const [applicationHash, setApplicationHash] = useState("");
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const [applicationId, setApplicationId] = useState<number | null>(null);
  const [isSearchingDataset, setIsSearchingDataset] = useState(false);
  const [isSearchingApplication, setIsSearchingApplication] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Search for dataset by hash
  useEffect(() => {
    const searchDataset = async () => {
      if (!datasetHash || datasetHash.trim() === "") {
        setDatasetId(null);
        setSearchError(null);
        return;
      }

      setIsSearchingDataset(true);
      setSearchError(null);

      try {
        const foundId = await findAssetIdByHash(datasetHash, chainId);
        if (foundId !== null) {
          // Verify it's actually a dataset by checking the asset
          // We'll verify when we fetch the asset data below
          setDatasetId(foundId);
        } else {
          setDatasetId(null);
          setSearchError("Dataset with this hash not found");
        }
      } catch (error) {
        console.error("Error searching for dataset:", error);
        setSearchError("Error searching for dataset");
        setDatasetId(null);
      } finally {
        setIsSearchingDataset(false);
      }
    };

    const timer = setTimeout(searchDataset, 800); // Debounce
    return () => clearTimeout(timer);
  }, [datasetHash, chainId]);

  // Search for application by hash
  useEffect(() => {
    const searchApplication = async () => {
      if (!applicationHash || applicationHash.trim() === "") {
        setApplicationId(null);
        return;
      }

      setIsSearchingApplication(true);

      try {
        const foundId = await findAssetIdByHash(applicationHash, chainId);
        if (foundId !== null) {
          setApplicationId(foundId);
        } else {
          setApplicationId(null);
          if (!searchError) setSearchError("Application with this hash not found");
        }
      } catch (error) {
        console.error("Error searching for application:", error);
        setApplicationId(null);
      } finally {
        setIsSearchingApplication(false);
      }
    };

    const timer = setTimeout(searchApplication, 800); // Debounce
    return () => clearTimeout(timer);
  }, [applicationHash, chainId]);

  // Get asset details for price calculation
  const datasetAsset = useAsset(datasetId !== null ? datasetId : undefined);
  const applicationAsset = useAsset(applicationId !== null ? applicationId : undefined);

  // Verify asset types match
  useEffect(() => {
    if (datasetAsset.data && datasetAsset.data[0] !== 0) {
      setSearchError("Hash does not correspond to a dataset");
      setDatasetId(null);
    }
    if (applicationAsset.data && applicationAsset.data[0] !== 1) {
      setSearchError("Hash does not correspond to an application");
      setApplicationId(null);
    }
  }, [datasetAsset.data, applicationAsset.data]);

  // Prices are in Wei (bigint), formatEth will convert to ETH for display
  const datasetPrice = datasetAsset.data?.[5] || BigInt(0);
  const applicationPrice = applicationAsset.data?.[5] || BigInt(0);
  const totalPrice = datasetPrice + applicationPrice;

  const { write, hash, isPending, error } = useContractWrite();
  const { isLoading: isConfirming, isSuccess } = useWaitForTransaction(hash);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!datasetId || !applicationId) {
      alert("Please provide both dataset and application hashes");
      return;
    }

    if (!address) {
      alert("Please connect your wallet");
      return;
    }

    try {
      await write("purchaseAccess", [datasetId, applicationId], totalPrice);
    } catch (err) {
      console.error("Error purchasing access:", err);
    }
  };

  const isProcessing = isPending || isConfirming;
  const canSubmit = datasetId !== null && applicationId !== null && !isProcessing;

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Purchase Access
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Enter the encrypted dataset and application hashes (IPFS CIDs) to purchase access rights
      </Typography>

      <Box component="form" onSubmit={handleSubmit} sx={{ mt: 2 }}>
        <TextField
          fullWidth
          label="Dataset Hash (Encrypted IPFS CID)"
          value={datasetHash}
          onChange={(e) => setDatasetHash(e.target.value)}
          required
          sx={{ mb: 2 }}
          placeholder="ipfs://Qm... or Qm..."
          helperText="Paste the encrypted dataset hash (IPFS CID)"
          InputProps={{
            endAdornment: isSearchingDataset && <CircularProgress size={20} />,
          }}
        />

        {datasetId && datasetAsset.data && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Dataset found: Asset #{datasetId} - Price: {formatPrice(datasetAsset.data[5])}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Application Hash (Encrypted IPFS CID)"
          value={applicationHash}
          onChange={(e) => setApplicationHash(e.target.value)}
          required
          sx={{ mb: 2 }}
          placeholder="ipfs://Qm... or Qm..."
          helperText="Paste the encrypted application hash (IPFS CID)"
          InputProps={{
            endAdornment: isSearchingApplication && <CircularProgress size={20} />,
          }}
        />

        {applicationId && applicationAsset.data && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Application found: Asset #{applicationId} - Price: {formatPrice(applicationAsset.data[5])}
          </Alert>
        )}

        {searchError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {searchError}
          </Alert>
        )}

        {datasetId && applicationId && datasetAsset.data && applicationAsset.data && (
          <Box sx={{ mb: 2, p: 2, bgcolor: "background.paper", borderRadius: 1 }}>
            <Typography variant="body2" color="text.secondary">
              Dataset Price: {formatPrice(datasetPrice)}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Application Price: {formatPrice(applicationPrice)}
            </Typography>
            <Typography variant="h6" sx={{ mt: 1 }}>
              Total: {formatPrice(totalPrice)}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: "block" }}>
              Total in Wei: {totalPrice.toString()}
            </Typography>
          </Box>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {getErrorMessage(error)}
          </Alert>
        )}

        {isSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Access purchased successfully! Transaction: {hash}
          </Alert>
        )}

        <Button
          type="submit"
          variant="contained"
          fullWidth
          disabled={!canSubmit || isSearchingDataset || isSearchingApplication}
          sx={{ mt: 2 }}
        >
          {isProcessing ? (
            <>
              <CircularProgress size={20} sx={{ mr: 1 }} />
              {isPending ? "Confirming..." : "Processing..."}
            </>
          ) : (
            `Purchase Access${datasetId && applicationId ? ` (${formatPrice(totalPrice)})` : ""}`
          )}
        </Button>
      </Box>
    </Paper>
  );
}
