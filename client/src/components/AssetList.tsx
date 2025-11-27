"use client";

import { useState, useMemo } from "react";
import {
  Box,
  Typography,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Alert,
  Paper,
} from "@mui/material";
import { useAssetIds } from "@/hooks/useAssets";
import { useAsset } from "@/hooks/useContract";
import { assetFromContractData } from "@/hooks/useAssets";
import AssetCard from "./AssetCard";

// Component to fetch and display a single asset
function AssetItem({ assetId, filter }: { assetId: number; filter: "all" | "datasets" | "applications" }) {
  const { data, isLoading } = useAsset(assetId);
  
  if (isLoading) return null;
  if (!data) return null;
  
  const asset = assetFromContractData(assetId, data);
  
  // Apply filter
  if (filter === "datasets" && asset.assetType !== 0) return null;
  if (filter === "applications" && asset.assetType !== 1) return null;
  
  return (
    <Grid item xs={12} sm={6} md={4}>
      <AssetCard asset={asset} />
    </Grid>
  );
}

export default function AssetList() {
  const [filter, setFilter] = useState<"all" | "datasets" | "applications">("all");
  const { assetIds, isLoading, error } = useAssetIds();

  // Limit to first 20 assets to avoid too many requests
  const displayedIds = useMemo(() => assetIds.slice(0, 20), [assetIds]);

  return (
    <Box>
      <Box sx={{ display: "flex", justifyContent: "space-between", mb: 3 }}>
        <Typography variant="h4">Browse Assets</Typography>
        <FormControl sx={{ minWidth: 200 }}>
          <InputLabel>Filter</InputLabel>
          <Select
            value={filter}
            onChange={(e) => setFilter(e.target.value as any)}
            label="Filter"
          >
            <MenuItem value="all">All Assets</MenuItem>
            <MenuItem value="datasets">Datasets Only</MenuItem>
            <MenuItem value="applications">Applications Only</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {isLoading && (
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading assets: {error?.message || "Unknown error"}
        </Alert>
      )}

      {!isLoading && !error && displayedIds.length === 0 && (
        <Paper sx={{ p: 4, textAlign: "center" }}>
          <Typography variant="h6" color="text.secondary">
            No assets found
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Be the first to register an asset!
          </Typography>
        </Paper>
      )}

      {!isLoading && displayedIds.length > 0 && (
        <Grid container spacing={3}>
          {displayedIds.map((id) => (
            <AssetItem key={id} assetId={id} filter={filter} />
          ))}
        </Grid>
      )}
    </Box>
  );
}
