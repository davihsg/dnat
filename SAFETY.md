# Network Safety Guide

## ⚠️ IMPORTANT: Network Safety

This application is configured for **development and testing**. Here's what you need to know:

## Safe Networks (No Real Money)

### ✅ Localhost (Chain ID: 31337) - RECOMMENDED FOR DEVELOPMENT
- **Safe**: Uses test ETH from your local Hardhat node
- **No cost**: Transactions don't use real money
- **Default**: This is the default network for development
- **Setup**: Requires running `npx hardhat node` locally

### ✅ Hardhat (Chain ID: 1337)
- **Safe**: Local test network
- **No cost**: Test ETH only

### ✅ Sepolia Testnet (Chain ID: 11155111)
- **Safe**: Ethereum testnet
- **No cost**: Free test ETH from faucets
- **Note**: Still uses your MetaMask account, but with test tokens

## ⚠️ Production Networks (REAL MONEY)

### ❌ Ethereum Mainnet (Chain ID: 1)
- **DANGER**: Uses real ETH
- **Cost**: Transactions cost real money
- **Warning**: The app will show a red warning if you're on mainnet

### ⚠️ Polygon Mainnet (Chain ID: 137)
- **DANGER**: Uses real MATIC tokens
- **Cost**: Transactions cost real money

## How to Check Your Current Network

1. **Look at the top bar**: The network name is displayed as a chip
2. **Check MetaMask**: The network name appears in MetaMask
3. **Look for warnings**: A red warning banner appears if you're on mainnet

## How to Switch to Localhost (Safe for Testing)

1. **In MetaMask**:
   - Click the network dropdown (top of MetaMask)
   - Select "Localhost 8545" or "Add Network"
   - If adding manually:
     - Network Name: `Localhost 8545`
     - RPC URL: `http://127.0.0.1:8545`
     - Chain ID: `31337`
     - Currency Symbol: `ETH`

2. **Make sure Hardhat node is running**:
   ```bash
   cd smart-contract
   npx hardhat node
   ```

3. **Import test account** (optional):
   - Hardhat provides test accounts with test ETH
   - You can import them into MetaMask using the private keys shown in the Hardhat output

## Safety Features Added

- ✅ **Network Warning Banner**: Shows a red warning if connected to mainnet
- ✅ **Network Indicator**: Color-coded chip showing current network
- ✅ **Default to Localhost**: Application defaults to localhost for development

## Best Practices

1. **For Development**: Always use Localhost (31337)
2. **For Testing**: Use Sepolia testnet if you need a public testnet
3. **Never use Mainnet** for development/testing
4. **Use a separate MetaMask account** for testing if possible
5. **Double-check the network** before signing any transactions

## What Happens if You're on Mainnet?

If you're connected to Ethereum Mainnet:
- ⚠️ A red warning banner will appear at the top of the page
- ⚠️ The network chip will be red
- ⚠️ Transactions will cost real ETH
- ⚠️ The contract address on mainnet is likely not deployed (defaults to 0x0)

**Always switch to Localhost before testing!**

