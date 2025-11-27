"use client";

import {
  Box,
  Typography,
  Paper,
  Alert,
} from "@mui/material";
import { useAccount } from "wagmi";
import { formatAddress } from "@/utils/formatting";

export default function MyAccessRights() {
  const { address, isConnected } = useAccount();

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

      <Paper sx={{ p: 4, textAlign: "center" }}>
        <Alert severity="info">
          Access rights viewing is simplified in this implementation.
          In production, use event logs or an indexer to efficiently query access rights.
        </Alert>
        <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
          To check access for a specific dataset-application pair, use the contract's hasAccess function.
        </Typography>
      </Paper>
    </Box>
  );
}
