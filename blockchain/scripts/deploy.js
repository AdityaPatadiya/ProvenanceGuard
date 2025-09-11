const { ethers } = require("hardhat");

async function main() {
  // Get the contract factory
  const Provenance = await ethers.getContractFactory("Provenance");

  // Deploy
  const provenance = await Provenance.deploy();

  // Wait until it's mined
  await provenance.waitForDeployment();

  console.log(`Provenance deployed to: ${await provenance.getAddress()}`);
}

// Run
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
