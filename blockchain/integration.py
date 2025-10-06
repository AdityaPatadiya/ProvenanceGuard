import logging
import hashlib
import random
from datetime import datetime
from web3 import Web3
import json
import os
import redis

from config.logging_config import LogConfigure


class BlockchainRecorder:
    def __init__(self, simulation_mode=False, redis_enabled=True, log_file='../../logs/blockchain_recorder.log'):
        self.logger = logging.getLogger('BlockchainRecorder')
        self.simulation_mode = simulation_mode
        self.mock_chain = []
        self.redis_enabled = redis_enabled
        self.redis_client = None
        self.logger = logging.getLogger('BlockchainRecorder')
        self.setup_logger = LogConfigure().setup_logging(log_file, self.logger)

        if self.redis_enabled:
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.logger.info("Redis Connected for blockchain feedback")
            except Exception as e:
                self.logger.warning(f"Redis-blockchain connection failed: {e}")

        if simulation_mode:
            self.logger.info("Blockchain recorder initialized in simulation mode")
        else:
            self.logger.info("Blockchain recorder initialized in production mode")

            # Connect to local Hardhat node
            self.w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
            if not self.w3.is_connected():
                raise ConnectionError("⚠️ Could not connect to Hardhat node at http://127.0.0.1:8545")

            # Use first Hardhat account
            self.w3.eth.default_account = self.w3.eth.accounts[0]

            # Load ABI
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            abi_path = os.path.join(
                project_root, "blockchain", "artifacts", "contracts", "Provenence.sol", "Provenance.json"
            )
            with open(abi_path) as f:
                contract_json = json.load(f)
                self.abi = contract_json["abi"]

            # Replace with your deployed contract address
            self.contract_address = Web3.to_checksum_address(
                "0x5FbDB2315678afecb367f032d93F642f64180aa3"
            )

            # Initialize contract
            self.contract = self.w3.eth.contract(
                address=self.contract_address, abi=self.abi
            )

    # ---------------------------
    # Redis Feedback Publisher
    # ---------------------------
    def _publish_feedback(self, pallet_id, tx_hash, event_type="blockchain_recorded"):
        """Publish feedback to Redis channel"""
        if not self.redis_enabled or not self.redis_client:
            return

        try:
            feedback = {
                "type": event_type,
                "pallet_id": pallet_id,
                "tx_hash": tx_hash,
                "timestamp": datetime.now().isoformat()
            }
            self.redis_client.publish("events", json.dumps(feedback))
            self.logger.info(f"Published blockchain feedback for {pallet_id}")
        except Exception as e:
            self.logger.error(f"Error to publish blockchain feedback: {e}")

    # ---------------------------
    # Blockchain Recording
    # ---------------------------
    def record_temperature_breach(self, pallet_id, temperature, location):
        """Record a temperature breach on blockchain"""
        if self.simulation_mode:
            return self._record_simulation(pallet_id, temperature, location)
        else:
            return self._record_real_blockchain(pallet_id, temperature, location)

    def _record_simulation(self, pallet_id, temperature, location):
        """Simulate blockchain recording"""
        try:
            block_data = {
                'type': 'temperature_breach',
                'pallet_id': pallet_id,
                'temperature': temperature,
                'location': location,
                'timestamp': datetime.now().isoformat(),
                'block_hash': self._generate_mock_hash(),
                'previous_hash': self._get_last_hash(),
                'status': 'recorded'
            }

            self.mock_chain.append(block_data)

            self.logger.info(
                f"SIMULATION: Recorded temperature breach - "
                f"Pallet: {pallet_id}, Temp: {temperature}°C, "
                f"Block Hash: {block_data['block_hash']}"
            )

            tx_hash = block_data['block_hash']
            self._publish_feedback(pallet_id, tx_hash)
            return tx_hash

        except Exception as e:
            self.logger.error(f"Failed to record temperature breach: {e}")
            return None

    def _record_real_blockchain(self, pallet_id, temperature, location):
        """Record on real blockchain via Hardhat node"""
        try:
            tx_hash = self.contract.functions.recordBreach(
                str(pallet_id),
                int(temperature)
            ).transact()

            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

            tx_hex = receipt.transactionHash.hex()
            self.logger.info(
                f"REAL: Recorded breach for pallet {pallet_id}, temp {temperature}°C → tx {tx_hex}"
            )

            self._publish_feedback(pallet_id, tx_hex)
            return tx_hex

        except Exception as e:
            self.logger.error(f"Blockchain tx failed: {e}")
            return None

    def _generate_mock_hash(self):
        """Generate a mock hash for simulation"""
        data = str(random.random()) + str(datetime.now())
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def _get_last_hash(self):
        """Get the hash of the last block in the chain"""
        if not self.mock_chain:
            return "0" * 16  # Genesis block
        return self.mock_chain[-1]['block_hash']

    def get_chain_data(self):
        """Get all recorded data for debugging or display"""
        return self.mock_chain
