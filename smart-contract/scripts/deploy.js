const hre = require("hardhat");
const fs = require("fs");
const path = require("path");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);
  console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString());

  // Deploy the contract
  const DnatMarketplace = await hre.ethers.getContractFactory("DnatMarketplace");
  const marketplace = await DnatMarketplace.deploy();

  await marketplace.waitForDeployment();
  const address = await marketplace.getAddress();

  console.log("DnatMarketplace deployed to:", address);

  // Save deployment info
  const deploymentInfo = {
    network: hre.network.name,
    chainId: hre.network.config.chainId,
    contractAddress: address,
    deployer: deployer.address,
    deployedAt: new Date().toISOString(),
  };

  // Create deployments directory if it doesn't exist
  const deploymentsDir = path.join(__dirname, "..", "deployments");
  if (!fs.existsSync(deploymentsDir)) {
    fs.mkdirSync(deploymentsDir, { recursive: true });
  }

  // Save deployment info to file
  const deploymentFile = path.join(deploymentsDir, `${hre.network.name}.json`);
  fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));

  // Also save ABI for client use
  const contractArtifact = await hre.artifacts.readArtifact("DnatMarketplace");
  const abiFile = path.join(deploymentsDir, "DnatMarketplace.abi.json");
  fs.writeFileSync(abiFile, JSON.stringify(contractArtifact.abi, null, 2));

  console.log("Deployment info saved to:", deploymentFile);
  console.log("ABI saved to:", abiFile);
  console.log("\nContract address:", address);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });

