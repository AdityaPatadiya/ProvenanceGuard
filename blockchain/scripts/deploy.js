async function main() {
  const Provenance = await ethers.getContractFactory("Provenance");
  const provenance = await Provenance.deploy();

  await provenance.deployed();

  console.log(`Provenance deployed to: ${provenance.address}`);
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
