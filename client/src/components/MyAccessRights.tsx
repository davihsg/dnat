"use client";

import { useState, useEffect } from "react";
import {
  Box,
  Typography,
  Paper,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Chip,
  CircularProgress,
  Skeleton,
} from "@mui/material";
import { useAccount } from "wagmi";
import { formatAddress } from "@/utils/formatting";
import { useAccessPurchases } from "@/hooks/useAccessPurchases";
import { useAsset } from "@/hooks/useContract";
import Link from "next/link";

interface PurchaseRowProps {
  datasetId: bigint;
  applicationId: bigint;
}

function PurchaseRow({ datasetId, applicationId }: PurchaseRowProps) {
  const { data: dataset, isLoading: loadingDataset } = useAsset(datasetId);
  const { data: application, isLoading: loadingApplication } = useAsset(applicationId);

  if (loadingDataset || loadingApplication) {
    return (
      <TableRow>
        <TableCell><Skeleton width={60} /></TableCell>
        <TableCell><Skeleton width={150} /></TableCell>
        <TableCell><Skeleton width={60} /></TableCell>
        <TableCell><Skeleton width={150} /></TableCell>
        <TableCell><Skeleton width={100} /></TableCell>
      </TableRow>
    );
  }

  // Parse manifest URIs to get names (simplified - in production parse the actual manifest)
  const datasetName = dataset ? `Dataset #${datasetId.toString()}` : "Unknown";
  const appName = application ? `App #${applicationId.toString()}` : "Unknown";

  return (
    <TableRow hover>
      <TableCell>
        <Chip label={datasetId.toString()} size="small" color="primary" />
      </TableCell>
      <TableCell>{datasetName}</TableCell>
      <TableCell>
        <Chip label={applicationId.toString()} size="small" color="secondary" />
      </TableCell>
      <TableCell>{appName}</TableCell>
      <TableCell>
        <Button
          variant="contained"
          size="small"
          color="success"
          component={Link}
          href={`/execute?datasetId=${datasetId}&applicationId=${applicationId}`}
        >
          Execute
        </Button>
      </TableCell>
    </TableRow>
  );
}

export default function MyAccessRights() {
  const { address, isConnected } = useAccount();
  const { purchases, isLoading, error } = useAccessPurchases();

  if (!isConnected) {
    return (
      <Paper sx={{ p: 4 }}>
        <Alert severity="info">Please connect your wallet to view your access rights</Alert>
      </Paper>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        My Access Rights
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Access rights for address: {address && formatAddress(address)}
      </Typography>

      {isLoading ? (
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading access rights: {error.message}
        </Alert>
      ) : purchases.length === 0 ? (
      <Paper sx={{ p: 4, textAlign: "center" }}>
        <Alert severity="info">
            You haven't purchased any access rights yet.
        </Alert>
          <Button
            variant="contained"
            component={Link}
            href="/purchase"
            sx={{ mt: 2 }}
          >
            Purchase Access
          </Button>
      </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Dataset ID</TableCell>
                <TableCell>Dataset</TableCell>
                <TableCell>App ID</TableCell>
                <TableCell>Application</TableCell>
                <TableCell>Action</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {purchases.map((purchase, index) => (
                <PurchaseRow
                  key={`${purchase.datasetId}-${purchase.applicationId}-${index}`}
                  datasetId={purchase.datasetId}
                  applicationId={purchase.applicationId}
                />
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
}
