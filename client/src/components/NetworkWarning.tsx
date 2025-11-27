"use client";

import { Alert, AlertTitle, Box } from "@mui/material";
import { useChainId } from "wagmi";

export default function NetworkWarning() {
  const chainId = useChainId();

  // Show warning if on mainnet (Chain ID 1)
  if (chainId === 1) {
    return (
      <Alert severity="error" sx={{ mb: 3 }}>
        <AlertTitle>⚠️ WARNING: Connected to Ethereum Mainnet</AlertTitle>
        You are connected to Ethereum Mainnet with real ETH. This application is for
        development/testing. Switch to Localhost (Chain ID: 31337) or a testnet to avoid
        spending real money.
      </Alert>
    );
  }

  // Show info if on localhost
  if (chainId === 31337 || chainId === 1337) {
    return (
      <Alert severity="success" sx={{ mb: 3 }}>
        <AlertTitle>✓ Connected to Local Test Network</AlertTitle>
        You are on a local test network. Transactions use test ETH and do not cost real money.
        This is safe for testing.
      </Alert>
    );
  }

  // Show warning for other networks (testnets are generally safe, but be cautious)
  if (chainId !== 1 && chainId !== 31337 && chainId !== 1337) {
    return (
      <Alert severity="warning" sx={{ mb: 3 }}>
        <AlertTitle>Network: Chain ID {chainId}</AlertTitle>
        You are connected to a test network. Transactions may use test tokens.
      </Alert>
    );
  }

  return null;
}

