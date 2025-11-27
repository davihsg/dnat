# DNAT Marketplace Setup Guide

## Prerequisites

- Node.js (v18 or higher)
- npm or yarn
- MetaMask browser extension

## Setup Instructions

### 1. Smart Contract Setup

```bash
cd smart-contract
npm install
```

### 2. Deploy Contract

Start a local Hardhat node in one terminal:
```bash
cd smart-contract
npx hardhat node
```

In another terminal, deploy the contract:
```bash
cd smart-contract
npx hardhat run scripts/deploy.js --network localhost
```

Copy the deployed contract address from the output and update `client/src/config/contract.ts`:
```typescript
export const contractAddresses: Record<number, `0x${string}`> = {
  31337: "0x...", // Paste your deployed address here
  // ...
};
```

### 3. Client Setup

```bash
cd client
npm install
```

### 4. Run Client

```bash
cd client
npm run dev
```

The application will be available at `http://localhost:3000`

## Development Workflow

1. Start Hardhat node: `cd smart-contract && npx hardhat node`
2. Deploy contract: `cd smart-contract && npx hardhat run scripts/deploy.js --network localhost`
3. Update contract address in `client/src/config/contract.ts`
4. Start client: `cd client && npm run dev`
5. Connect MetaMask to localhost:8545 (Chain ID: 31337)
6. Import test accounts from Hardhat node into MetaMask

## Network Configuration

The application supports multiple EVM chains:
- Localhost (31337) - for development
- Hardhat (31337) - for testing
- Sepolia - Ethereum testnet
- Polygon - Mainnet
- Ethereum Mainnet

Switch networks using the network selector in the UI or MetaMask.

## Notes

- Contract ABI is defined in `client/src/config/contract.ts`
- For production, import ABI from `smart-contract/deployments/DnatMarketplace.abi.json`
- Asset fetching is limited to 20 assets to avoid too many contract calls
- In production, consider using multicall or an indexer for better performance

