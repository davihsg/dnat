"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { WagmiProvider } from "wagmi";
import { createConfig, http } from "wagmi";
import { mainnet, sepolia, polygon, hardhat, localhost } from "wagmi/chains";
import { metaMask } from "wagmi/connectors";
import { ReactNode, useState } from "react";

// Create a custom localhost chain config
const localhostChain = {
  ...localhost,
  id: 31337,
  name: "Localhost",
  nativeCurrency: {
    decimals: 18,
    name: "Ether",
    symbol: "ETH",
  },
  rpcUrls: {
    default: {
      http: ["http://127.0.0.1:8545"],
    },
  },
} as const;

// Configure wagmi with supported chains
// NOTE: localhostChain is first, so it's the default
// For safety, mainnet is last - users should explicitly switch to it
const config = createConfig({
  chains: [localhostChain, hardhat, sepolia, polygon, mainnet],
  connectors: [
    metaMask({
      dappMetadata: {
        name: "DNAT Marketplace",
        url: typeof window !== "undefined" ? window.location.origin : "",
      },
      // Prefer localhost for development
      preferDesktop: false,
    }),
  ],
  transports: {
    [localhostChain.id]: http(),
    [hardhat.id]: http(),
    [sepolia.id]: http(),
    [polygon.id]: http(),
    [mainnet.id]: http(),
  },
  ssr: true,
});

export function WagmiProviderWrapper({ children }: { children: ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <WagmiProvider config={config}>
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    </WagmiProvider>
  );
}

