"use client";

import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Chip,
  IconButton,
  Paper,
  Divider,
  Tooltip,
  CircularProgress,
  Alert,
} from "@mui/material";
import { ContentCopy, Check } from "@mui/icons-material";
import { useState, useEffect } from "react";
import { formatEth, formatAddress, formatAssetType, formatHash } from "@/utils/formatting";
import { Asset } from "@/hooks/useAssets";
import { fetchFromIPFS, parseYAML } from "@/utils/ipfsUtils";

interface AssetDetailModalProps {
  asset: Asset | null;
  open: boolean;
  onClose: () => void;
}

export default function AssetDetailModal({ asset, open, onClose }: AssetDetailModalProps) {
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [manifest, setManifest] = useState<Record<string, any> | null>(null);
  const [isLoadingManifest, setIsLoadingManifest] = useState(false);
  const [manifestError, setManifestError] = useState<string | null>(null);

  // Fetch manifest when modal opens
  useEffect(() => {
    if (open && asset?.manifestUri) {
      setIsLoadingManifest(true);
      setManifestError(null);
      
      fetchFromIPFS(asset.manifestUri)
        .then((yamlContent) => {
          try {
            const parsed = parseYAML(yamlContent);
            setManifest(parsed);
          } catch (error) {
            console.error("Error parsing YAML:", error);
            setManifestError("Failed to parse manifest");
          }
        })
        .catch((error) => {
          console.error("Error fetching manifest:", error);
          // For now, random IPFS URIs won't work, so this is expected
          setManifestError("Manifest not found on IPFS. This may be a placeholder URI.");
        })
        .finally(() => {
          setIsLoadingManifest(false);
        });
    } else {
      setManifest(null);
      setManifestError(null);
    }
  }, [open, asset?.manifestUri]);

  const handleCopy = async (text: string, field: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  const CopyButton = ({ text, field, label }: { text: string; field: string; label: string }) => (
    <Box sx={{ display: "flex", alignItems: "center", gap: 1, mb: 1 }}>
      <Typography variant="body2" sx={{ flex: 1, fontFamily: "monospace", wordBreak: "break-all" }}>
        <strong>{label}:</strong> {text}
      </Typography>
      <Tooltip title={copiedField === field ? "Copied!" : "Copy"}>
        <IconButton
          size="small"
          onClick={() => handleCopy(text, field)}
          sx={{ color: copiedField === field ? "success.main" : "inherit" }}
        >
          {copiedField === field ? <Check fontSize="small" /> : <ContentCopy fontSize="small" />}
        </IconButton>
      </Tooltip>
    </Box>
  );

  if (!asset) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <Typography variant="h5">
            Asset #{asset.id} - {formatAssetType(asset.assetType)}
          </Typography>
          <Chip
            label={asset.active ? "Active" : "Inactive"}
            color={asset.active ? "success" : "default"}
          />
        </Box>
      </DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2 }}>
          {/* Manifest/Description Section */}
          {isLoadingManifest && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <CircularProgress size={20} />
                <Typography variant="body2">Loading manifest from IPFS...</Typography>
              </Box>
            </Paper>
          )}

          {manifestError && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
              <Alert severity="info" sx={{ mb: 0 }}>
                {manifestError}
              </Alert>
            </Paper>
          )}

          {manifest && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
              <Typography variant="h6" gutterBottom>
                Asset Description
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {manifest.name && (
                <Typography variant="h6" color="primary" gutterBottom>
                  {manifest.name}
                </Typography>
              )}
              {manifest.description && (
                <Typography variant="body1" paragraph sx={{ whiteSpace: "pre-wrap" }}>
                  {manifest.description}
                </Typography>
              )}
              <Box sx={{ mt: 2, display: "flex", flexWrap: "wrap", gap: 2 }}>
                {manifest.version && (
                  <Chip label={`Version: ${manifest.version}`} size="small" />
                )}
                {manifest.author && (
                  <Chip label={`Author: ${manifest.author}`} size="small" />
                )}
                {manifest.framework && (
                  <Chip label={`Framework: ${manifest.framework}`} size="small" />
                )}
                {manifest.dependencies && (
                  <Chip label={`Dependencies: ${manifest.dependencies}`} size="small" />
                )}
              </Box>
            </Paper>
          )}

          <Paper sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
            <Typography variant="h6" gutterBottom>
              Basic Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <CopyButton text={asset.owner} field="owner" label="Owner Address" />
            <CopyButton text={asset.contentHash} field="contentHash" label="Content Hash" />
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2">
                <strong>Price:</strong> {formatEth(asset.price)} ETH
              </Typography>
            </Box>
          </Paper>

          <Paper sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
            <Typography variant="h6" gutterBottom>
              IPFS References
            </Typography>
            <Divider sx={{ mb: 2 }} />
            <CopyButton text={asset.encryptedUri} field="encryptedUri" label="Encrypted URI" />
            <CopyButton text={asset.manifestUri} field="manifestUri" label="Manifest URI" />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontSize: "0.75rem" }}>
              Note: Full description and manifest details are stored on IPFS. Fetch the manifest from the URI above to view complete information.
            </Typography>
          </Paper>

          {asset.bloomFilter && asset.bloomFilter !== "0x" && (
            <Paper sx={{ p: 2, mb: 2, bgcolor: "background.default" }}>
              <Typography variant="h6" gutterBottom>
                Bloom Filter
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <CopyButton text={asset.bloomFilter} field="bloomFilter" label="Bloom Filter" />
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1, fontSize: "0.75rem" }}>
                This dataset has a Bloom filter for whitelisted applications.
              </Typography>
            </Paper>
          )}

          {!manifest && !isLoadingManifest && !manifestError && (
            <Paper sx={{ p: 2, bgcolor: "info.light", color: "info.contrastText" }}>
              <Typography variant="body2">
                <strong>Note:</strong> The manifest will be automatically fetched from IPFS when available.
              </Typography>
            </Paper>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Close</Button>
        <Button
          variant="contained"
          component="a"
          href={`/purchase?datasetId=${asset.assetType === 0 ? asset.id : ""}&applicationId=${asset.assetType === 1 ? asset.id : ""}`}
        >
          Use in Purchase
        </Button>
      </DialogActions>
    </Dialog>
  );
}

