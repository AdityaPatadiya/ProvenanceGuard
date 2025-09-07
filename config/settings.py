"""
Global configuration settings for ProvenanceGuard project.
Centralized here to avoid hardcoding values in multiple files.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env if available
load_dotenv()

# ------------------------
# Simulator Configuration
# ------------------------
SIMULATION_SPEED = int(os.getenv("SIMULATION_SPEED", 1))  # seconds between updates
PALLET_ID = os.getenv("PALLET_ID", "PALLET_001")
ORIGIN = [52.5200, 13.4050]       # Berlin
DESTINATION = [52.3676, 4.9041]   # Amsterdam
IDEAL_TEMP = float(os.getenv("IDEAL_TEMP", 4.0))   # °C
MAX_TEMP = float(os.getenv("MAX_TEMP", 8.0))       # °C

# ------------------------
# Redis / Broker Settings
# ------------------------
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_CHANNEL = os.getenv("REDIS_CHANNEL", "sensor_data")

# ------------------------
# Blockchain Settings
# ------------------------
BLOCKCHAIN_RPC = os.getenv("BLOCKCHAIN_RPC", "http://127.0.0.1:7545")
CONTRACT_PATH = os.getenv("CONTRACT_PATH", "blockchain/contracts/Provenance.sol")
DEPLOYED_CONTRACT_ADDRESS = os.getenv("DEPLOYED_CONTRACT_ADDRESS", "")

# ------------------------
# Dashboard / API Settings
# ------------------------
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 5000))
DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() in ("true", "1", "yes")

# ------------------------
# Security / Secrets
# ------------------------
PRIVATE_KEY = os.getenv("PRIVATE_KEY", "")
