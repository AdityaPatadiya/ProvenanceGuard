# ProvenanceGuard

## Blockchain-Powered Supply Chain Monitoring & Autonomous Logistics System

ProvenanceGuard is an end-to-end multi-agent supply chain automation system that integrates IoT simulation, multi-agent intelligence, blockchain immutability, and logistics decision-making.
It provides real-time pallet monitoring, automated rerouting, and tamper-proof record-keeping using a Hardhat-based smart contract.

## Key Features
### 1. Real-Time IoT Monitoring

- Python simulator streams pallet temperature & GPS.

- Detects temperature breaches & spoilage events automatically.

### 2. Multi-Agent System

- `SimpleProductAgent` → Detects anomalies, sends alerts.

- `LogisticsAgent` → Reroutes pallets, updates warehouse status, and logs all actions.

- `BlockchainRecorder` → Stores breach events on smart contract / mock chain.

### 3. Blockchain Integration

- Deploys a Solidity smart contract using Hardhat.

- Records:

  - temperature breaches

  - pallet IDs

  - on-chain timestamps

  - transaction hashes

### 4. Close Feedback Loop

- Redis channels connect all agents:

  - `sensor_data`

  - `alerts`

  - `commands`

  - `events`

### 5. Local Logging System

- All agents log to separate files under /logs/.

- Each action (alert, reroute, blockchain record) is logged.



## System Architecture
```
         ┌───────────────── IoT Simulator ─────────────────┐
         │  Generates temperature + GPS for each pallet     │
         └──────────────────────┬───────────────────────────┘
                                │  sensor_data
                                ▼
                   ┌────────────────────────────┐
                   │    SimpleProductAgent       │
                   │  - Detects breaches         │
                   │  - Sends alerts (Redis)     │
                   └─────────────┬──────────────┘
                         alerts   │
                                 ▼
                   ┌────────────────────────────┐
                   │      LogisticsAgent         │
                   │  - Reroute decisions        │
                   │  - Warehouse selection      │
                   │  - Sends commands           │
                   └──────────────┬─────────────┘
                          commands│
                                 ▼
   ┌─────────────────────────────────────────────────────┐
   │               BlockchainRecorder                     │
   │  - Real mode → Hardhat smart contract                │
   │  - Simulation mode → mock chain                      │
   │  - Publishes blockchain confirmation (events)        │
   └───────────────────────┬─────────────────────────────┘
                           │ events
                           ▼
              Agents update internal state tracker
```

## Folder Structure
```
ProvenanceGuard/
│
├── blockchain/
│   ├── contracts/Provenence.sol
│   ├── artifacts/...
│   ├── integration.py
│   └── state_tracker.py
│
├── mas/
│   ├── agents/
│   │   ├── SimpleProductAgent.py
│   │   ├── LogisticsAgent.py
│   │   └── ...
│   └── simulator/
│       └── data_simulator.py
│
├── config/
│   └── logging_config.py
│
├── logs/
│   ├── supply_chain.log
│   ├── logistics_agent.log
│   └── blockchain_recorder.log
│
├── scripts/
│   └── deploy.js
│
├── README.md
└── requirements.txt
```

## Tech Stack
| Layer                     | Technology                 |
| ------------------------- | -------------------------- |
| Blockchain                | Solidity, Hardhat, Web3.py |
| Messaging                 | Redis Pub/Sub              |
| Backend Agents            | Python                     |
| Simulation                | IoT Data Generator         |
| Logging                   | Python Logging Module      |
| Smart Contract Deployment | Hardhat Node + TypeScript  |

## Installation & Setup
### 1. Clone the Repository
```
git clone https://github.com/yourusername/ProvenanceGuard.git
cd ProvenanceGuard
```

### 2. Install Python Dependencies
```
python3 -m venv venv
pip install -r requirements.txt
```
### 3. Install Hardhat & Node Depedencies
```
cd blockchain
npm install
```


## Smart Contract Setup
### 4. Start the Local Hardhat Node
```
npx hardhat node
```

### 5. Deploy Smart Contract
Open a new terminal and run: 
```
npx hardhat run scripts/deploy.js --network localhost
```

copy the deployed contract address into:
```
blockchain/integration.py
```

### 6. Start the actual Project:
```
source venv/bin/activate
python3 run_all.py
```

Agents will now:
✔ detect anomalies
✔ reroute pallets
✔ record everything on-chain
✔ broadcast feedback events
✔ update internal tracker


## Logs (Auto-Generated)
Logs stored under `/logs/`:

supply_chain.log → SimpleProductAgent

logistics_agent.log → LogisticsAgent

blockchain_recorder.log → BlockchainRecorder


## Smart Contract (Provenence.sol)

Supports:

- recordBreach(palletId, temperature)

- On-chain event emission

- Transparent audit trail

## Future Improvements

Add AI anomaly prediction (LSTM or Prophet)

Build dashboard using React or Streamlit

Expand to multiple pallets and trucks

Add GPS-based geofencing and automated SLA alerts

Replace Hardhat with Polygon PoS or Base Sepolia testnet



