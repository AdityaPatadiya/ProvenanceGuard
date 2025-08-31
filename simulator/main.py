import time
import json
import redis # Or use pika for RabbitMQ, or just print for simplest version
from data_simulator import PalletSimulator
from scenarios.default_scenario import run_default_scenario

# Configuration
SIMULATION_SPEED = 1  # Seconds between updates
PALLET_ID = "PALLET_001"
ORIGIN = [52.5200, 13.4050]  # Berlin
DESTINATION = [52.3676, 4.9041]  # Amsterdam

def main():
    # Connect to Redis to publish data (Agents will subscribe to this)
    # For a simpler version, just print the JSON and have agents read it.
    r = redis.Redis(host='localhost', port=6379, db=0)

    print("Initializing Pallet Simulator...")
    pallet = PalletSimulator(PALLET_ID, ORIGIN, DESTINATION)

    step_count = 0
    try:
        while pallet.status not in ["DELIVERED", "SPOILED"]:
            # Run the scenario logic to update conditions
            run_default_scenario(pallet, step_count)

            # Get the current sensor data
            data_packet = pallet.update()

            # Publish the data to a channel for agents to listen to
            r.publish('sensor_data', json.dumps(data_packet))
            # Alternatively, for simplest setup: print(json.dumps(data_packet))

            print(f"Step {step_count}: {data_packet}")

            step_count += 1
            time.sleep(SIMULATION_SPEED)

        print(f"Simulation ended. Final status: {pallet.status}")

    except KeyboardInterrupt:
        print("Simulation stopped by user.")

if __name__ == "__main__":
    main()
