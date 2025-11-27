"use client";

import { ReactNode, useState, useEffect } from "react";
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  Menu,
  MenuItem,
  Chip,
} from "@mui/material";
import Link from "next/link";
import { useAccount, useDisconnect, useConnect, useChainId, useSwitchChain, useBalance } from "wagmi";
import { formatAddress, formatEth } from "@/utils/formatting";
import { supportedChains } from "@/config/chains";
import NetworkWarning from "./NetworkWarning";

// Extend Window interface for ethereum
declare global {
  interface Window {
    ethereum?: any;
  }
}

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  const { address, isConnected, connector } = useAccount();
  const { disconnect } = useDisconnect();
  const { connect, connectors, isPending: isConnecting, error: connectError } = useConnect();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();
  const { data: balance, isLoading: isLoadingBalance } = useBalance({
    address: address,
  });

  // Get account name from MetaMask
  const [accountName, setAccountName] = useState<string | null>(null);

  useEffect(() => {
    const getAccountName = async () => {
      if (!address || !isConnected) {
        setAccountName(null);
        return;
      }

      try {
        // Try to get account label from MetaMask's internal state
        if (typeof window !== "undefined" && window.ethereum) {
          // MetaMask stores account labels in _metamask.state.accounts
          const ethereum = window.ethereum as any;
          if (ethereum._metamask) {
            try {
              // Access MetaMask's internal state
              const metamaskState = ethereum._metamask.state;
              if (metamaskState?.accounts) {
                const accounts = metamaskState.accounts;
                const accountKey = address.toLowerCase();
                const accountInfo = accounts[accountKey];
                if (accountInfo?.label) {
                  setAccountName(accountInfo.label);
                  return;
                }
              }
            } catch (e) {
              // Ignore errors accessing internal state
            }
          }

          // Alternative: Try to get from MetaMask's state via request
          // MetaMask might expose this through wallet_getPermissions or similar
          try {
            // This is a workaround - MetaMask doesn't officially expose account labels
            // But we can try to access the internal state
            const provider = ethereum;
            if (provider && provider._metamask) {
              const state = provider._metamask.state;
              if (state?.accounts) {
                const accountKey = address.toLowerCase();
                const account = state.accounts[accountKey];
                if (account?.label) {
                  setAccountName(account.label);
                  return;
                }
              }
            }
          } catch (e) {
            // Ignore errors
          }
        }

        // If we can't get the label, set to null (will show connector name as fallback)
        setAccountName(null);
      } catch (error) {
        console.error("Error getting account name:", error);
        setAccountName(null);
      }
    };

    getAccountName();
  }, [address, isConnected]);

  const handleConnect = async () => {
    try {
      // Check if MetaMask is installed
      if (typeof window !== "undefined" && !window.ethereum) {
        alert("MetaMask is not installed. Please install MetaMask extension to continue.");
        window.open("https://metamask.io/download/", "_blank");
        return;
      }

      // Try to find MetaMask connector
      let metaMaskConnector = connectors.find((c) => c.id === "metaMask");
      if (!metaMaskConnector) {
        metaMaskConnector = connectors.find((c) => c.id === "io.metamask");
      }
      if (!metaMaskConnector) {
        // Try the first available connector
        metaMaskConnector = connectors[0];
      }
      
      if (metaMaskConnector) {
        console.log("Connecting with connector:", metaMaskConnector.id);
        console.log("Available connectors:", connectors.map(c => ({ id: c.id, name: c.name })));
        await connect({ connector: metaMaskConnector });
      } else {
        console.error("No connectors available. Available connectors:", connectors.map(c => c.id));
        alert("No wallet connectors found. Please install MetaMask extension.");
      }
    } catch (error) {
      console.error("Error connecting wallet:", error);
      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      alert(`Failed to connect wallet: ${errorMessage}`);
    }
  };

  const handleDisconnect = () => {
    disconnect();
  };

  const handleNetworkSwitch = (targetChainId: number) => {
    switchChain({ chainId: targetChainId });
  };

  const currentChain = supportedChains.find((c) => c.id === chainId);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 0, mr: 4 }}>
            <Link href="/" style={{ textDecoration: "none", color: "inherit" }}>
              DNAT Marketplace
            </Link>
          </Typography>
          <Box sx={{ flexGrow: 1, display: "flex", gap: 2 }}>
            <Button color="inherit" component={Link} href="/">
              Browse
            </Button>
            <Button color="inherit" component={Link} href="/register">
              Register Asset
            </Button>
            <Button color="inherit" component={Link} href="/purchase">
              Purchase Access
            </Button>
            <Button color="inherit" component={Link} href="/my-access">
              My Access
            </Button>
          </Box>
          <Box sx={{ display: "flex", gap: 2, alignItems: "center" }}>
            {currentChain && (
              <Chip
                label={currentChain.name}
                size="small"
                color={
                  chainId === 1
                    ? "error"
                    : chainId === 31337 || chainId === 1337
                    ? "success"
                    : "secondary"
                }
                sx={{ color: "white", fontWeight: "bold" }}
              />
            )}
            {chainId === 1 && (
              <Chip
                label="⚠️ MAINNET"
                size="small"
                color="error"
                sx={{ color: "white", fontWeight: "bold", animation: "pulse 2s infinite" }}
              />
            )}
            {isConnected && address ? (
              <>
                {/* Account Name */}
                {(accountName || connector?.name) && (
                  <Chip 
                    label={accountName || connector?.name || "Account"} 
                    size="small"
                    sx={{ 
                      backgroundColor: "rgba(255, 255, 255, 0.2)",
                      color: "white",
                      fontWeight: "medium"
                    }} 
                  />
                )}
                {/* Account Address */}
                <Chip 
                  label={formatAddress(address)} 
                  color="primary"
                  sx={{ fontWeight: "medium" }}
                />
                {/* Balance */}
                {balance && (
                  <Chip
                    label={
                      isLoadingBalance 
                        ? "Loading..." 
                        : `${formatEth(balance.value)} ${balance.symbol}`
                    }
                    size="small"
                    sx={{
                      backgroundColor: "rgba(255, 255, 255, 0.15)",
                      color: "white",
                      fontWeight: "medium",
                      minWidth: "80px",
                    }}
                  />
                )}
                <Button color="inherit" onClick={handleDisconnect}>
                  Disconnect
                </Button>
              </>
            ) : (
              <>
                <Button 
                  color="inherit" 
                  onClick={handleConnect}
                  disabled={isConnecting}
                >
                  {isConnecting ? "Connecting..." : "Connect Wallet"}
                </Button>
                {connectError && (
                  <Chip 
                    label="Connection Error" 
                    color="error" 
                    size="small"
                    sx={{ color: "white" }}
                  />
                )}
              </>
            )}
          </Box>
        </Toolbar>
      </AppBar>
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4, flex: 1 }}>
        <NetworkWarning />
        {children}
      </Container>
      <Box
        component="footer"
        sx={{
          py: 2,
          px: 2,
          mt: "auto",
          backgroundColor: (theme) =>
            theme.palette.mode === "light"
              ? theme.palette.grey[200]
              : theme.palette.grey[800],
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="body2" color="text.secondary" align="center">
            DNAT Marketplace - Confidential Data & Application Marketplace
          </Typography>
        </Container>
      </Box>
    </Box>
  );
}

