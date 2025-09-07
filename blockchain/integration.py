import logging
import hashlib
import random
from datetime import datetime

class BlockchainRecorder:
    def __init__(self, simulation_mode=True):
        self.logger = logging.getLogger('BlockchainRecorder')
        self.simulation_mode = simulation_mode
        self.mock_chain = []

        if simulation_mode:
            self.logger.info("Blockchain recorder initialized in simulation mode")
        else:
            self.logger.info("Blockchain recorder initialized in production mode")

    def record_temperature_breach(self, pallet_id, temperature, location):
        """Record a temperature breach on blockchain"""
        if self.simulation_mode:
            return self._record_simulation(pallet_id, temperature, location)
        else:
            return self._record_real_blockchain(pallet_id, temperature, location)

    def _record_simulation(self, pallet_id, temperature, location):
        """Simulate blockchain recording - always return string"""
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

            # Return as string (not bytes)
            return block_data['block_hash']

        except Exception as e:
            self.logger.error(f"Failed to record temperature breach: {e}")
            return None

    def _record_real_blockchain(self, pallet_id, temperature, location):
        """Record on real blockchain - return hex string instead of bytes"""
        self.logger.warning("Real blockchain recording not implemented yet")
        # When implementing real blockchain, return hex string instead of bytes
        # Example: return tx_hash.hex() instead of tx_hash
        return f"real_tx_{pallet_id}_{datetime.now().timestamp()}"

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
