import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { WagmiProviderWrapper } from "@/providers/WagmiProvider";
import Layout from "@/components/Layout";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "DNAT Marketplace",
  description: "Confidential Data & Application Marketplace",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <WagmiProviderWrapper>
          <Layout>{children}</Layout>
        </WagmiProviderWrapper>
      </body>
    </html>
  );
}

