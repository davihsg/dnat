import { formatUnits } from "viem";

/**
 * Format wei value to ether string with limited decimals
 * If value is very small, shows more precision or Wei
 */
export function formatEth(value: bigint | string | number, decimals: number = 3): string {
  const bigIntValue = typeof value === "bigint" ? value : BigInt(value.toString());
  
  // If value is 0, return "0"
  if (bigIntValue === BigInt(0)) {
    return "0";
  }
  
  const formatted = formatUnits(bigIntValue, 18);
  const parts = formatted.split(".");
  
  // If integer part is 0 and we have decimals, check if we need more precision
  if (parts[0] === "0" && parts[1]) {
    // Find first non-zero digit
    const firstNonZero = parts[1].search(/[1-9]/);
    if (firstNonZero !== -1 && firstNonZero >= decimals) {
      // Show more precision for very small amounts
      return formatted.slice(0, firstNonZero + decimals + 1);
    }
  }
  
  // Limit to specified decimal places
  if (parts.length === 1) return formatted;
  return `${parts[0]}.${parts[1].slice(0, decimals)}`;
}

/**
 * Format wei value, showing Wei if amount is very small
 */
export function formatPrice(value: bigint | string | number): string {
  const bigIntValue = typeof value === "bigint" ? value : BigInt(value.toString());
  
  if (bigIntValue === BigInt(0)) {
    return "0 ETH";
  }
  
  // If less than 0.001 ETH, show in Wei
  const oneMilliEth = BigInt("1000000000000000"); // 0.001 ETH in Wei
  if (bigIntValue < oneMilliEth) {
    return `${bigIntValue.toString()} Wei`;
  }
  
  return `${formatEth(bigIntValue)} ETH`;
}

/**
 * Format address to shortened version (0x1234...5678)
 */
export function formatAddress(address: string | undefined): string {
  if (!address) return "";
  return `${address.slice(0, 6)}...${address.slice(-4)}`;
}

/**
 * Format asset type enum to string
 */
export function formatAssetType(assetType: number): string {
  return assetType === 0 ? "Dataset" : "Application";
}

/**
 * Format bytes32 hash to shortened hex string
 */
export function formatHash(hash: string): string {
  if (!hash) return "";
  return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
}

