import { HardhatUserConfig } from "hardhat/config";
import "@nomicfoundation/hardhat-toolbox";

const config: HardhatUserConfig = {
  solidity: "0.8.20",   // You can set 0.8.28 if you want
  networks: {
    localhost: {
      url: "http://127.0.0.1:8545",   // hardhat node
    },
  },
};

export default config;
