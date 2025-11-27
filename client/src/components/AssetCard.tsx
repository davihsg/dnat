"use client";

import { useState } from "react";
import {
  Card,
  CardContent,
  Typography,
  Chip,
  Box,
  Button,
  CardActionArea,
} from "@mui/material";
import { formatEth, formatAddress, formatAssetType, formatHash } from "@/utils/formatting";
import Link from "next/link";
import { Asset } from "@/hooks/useAssets";
import AssetDetailModal from "./AssetDetailModal";

interface AssetCardProps {
  asset: Asset;
}

export default function AssetCard({ asset }: AssetCardProps) {
  const [detailOpen, setDetailOpen] = useState(false);

  return (
    <>
      <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
        <CardActionArea
          onClick={() => setDetailOpen(true)}
          sx={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "stretch" }}
        >
          <CardContent sx={{ flex: 1, width: "100%" }}>
            <Box sx={{ display: "flex", justifyContent: "space-between", mb: 2 }}>
              <Typography variant="h6" component="div">
                Asset #{asset.id}
              </Typography>
              <Chip
                label={formatAssetType(asset.assetType)}
                color={asset.assetType === 0 ? "primary" : "secondary"}
                size="small"
              />
            </Box>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Owner: {formatAddress(asset.owner)}
            </Typography>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Price: {formatEth(asset.price)} ETH
            </Typography>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Content Hash: {formatHash(asset.contentHash)}
            </Typography>

            <Typography variant="body2" color="text.secondary" gutterBottom>
              Encrypted URI: {asset.encryptedUri.substring(0, 30)}...
            </Typography>

            <Box sx={{ display: "flex", gap: 1, mt: 2 }}>
              <Chip
                label={asset.active ? "Active" : "Inactive"}
                color={asset.active ? "success" : "default"}
                size="small"
              />
              {asset.bloomFilter && asset.bloomFilter !== "0x" && (
                <Chip label="Has Bloom Filter" size="small" />
              )}
            </Box>

            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: "block" }}>
              Click to view details
            </Typography>
          </CardContent>
        </CardActionArea>
        <Box sx={{ p: 2, pt: 0 }}>
          <Button
            variant="outlined"
            size="small"
            fullWidth
            component={Link}
            href={`/purchase?datasetId=${asset.assetType === 0 ? asset.id : ""}&applicationId=${asset.assetType === 1 ? asset.id : ""}`}
            onClick={(e) => e.stopPropagation()}
          >
            Use in Purchase
          </Button>
        </Box>
      </Card>
      <AssetDetailModal
        asset={asset}
        open={detailOpen}
        onClose={() => setDetailOpen(false)}
      />
    </>
  );
}

