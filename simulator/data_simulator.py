import json
import numpy as np
from datetime import datetime

class PalletSimulator:
    """Simulates a pallet of perishable goods with IoT sensors."""

    def __init__(self, pallet_id, origin, destination, ideal_temp=4.0, max_temp=8.0):
        self.pallet_id = pallet_id
        self.current_location = origin  # [latitude, longitude]
        self.destination = destination  # [latitude, longitude]
        self.ideal_temp = ideal_temp
        self.max_temp = max_temp
        self.current_temp = ideal_temp
        self.status = "IN_TRANSIT"  # e.g., IN_TRANSIT, IN_WAREHOUSE, DELIVERED, SPOILED
        self.route = self._calculate_route(origin, destination)
        self.current_route_index = 0
        self.external_temp = 25.0  # Assume outside is warm
        self.cooling_unit_efficiency = 0.97
        self.is_moving = True

    def __repr__(self):
        """Debug-friendly string representation of the pallet state."""
        return (f"<PalletSimulator id={self.pallet_id} "
                f"status={self.status} "
                f"location=({round(self.current_location[0], 4)}, {round(self.current_location[1], 4)}) "
                f"temp={round(self.current_temp, 2)}°C>")

    def _calculate_route(self, origin, destination):
        """Generates a simple linear route for demo purposes."""
        # This is a simplified model. For a real project, use a routing API like OSRM.
        steps = 100  # Number of steps in the journey
        lat_steps = np.linspace(origin[0], destination[0], steps)
        lon_steps = np.linspace(origin[1], destination[1], steps)
        return list(zip(lat_steps, lon_steps))

    def update(self):
        """Advance the simulation by one step."""
        # Update Location
        if self.is_moving and self.current_route_index < len(self.route) - 1:
            self.current_route_index += 1
            self.current_location = self.route[self.current_route_index]
        else:
            self.is_moving = False

        # Simulate Temperature based on movement and cooling efficiency
        if self.is_moving:
            # Cooler can mostly keep up while moving
            temp_influence = (self.external_temp - self.ideal_temp) * (1 - self.cooling_unit_efficiency)
        else:
            # Cooler is less effective when stopped (e.g., traffic)
            temp_influence = (self.external_temp - self.ideal_temp) * (1 - (self.cooling_unit_efficiency * 0.5))

        self.current_temp += temp_influence * np.random.uniform(0.1, 0.3)  # Add some randomness

        # Check for spoilage
        if self.current_temp > self.max_temp:
            self.status = "SPOILED"

        # Check for delivery
        if self.current_route_index >= len(self.route) - 1:
            self.status = "DELIVERED"
            self.is_moving = False
        elif self.current_temp > self.max_temp:
            self.status = "SPOILED"

        return self._generate_data_packet()

    def _generate_data_packet(self):
        """Returns a JSON packet mimicking IoT sensor data."""
        return {
            "pallet_id": self.pallet_id,
            "timestamp": datetime.utcnow().isoformat() + 'Z',
            "location": {
                "lat": self.current_location[0],
                "lon": self.current_location[1]
            },
            "temperature": round(self.current_temp, 2),
            "status": self.status
        }

    def apply_scenario(self, cooling_efficiency, is_moving):
        """Allows external scenario scripts to change conditions."""
        self.cooling_unit_efficiency = cooling_efficiency
        self.is_moving = is_moving

    def process_commands(self):
        """Check for and process commands from Redis"""
        try:
            message = self.command_pubsub.get_message()
            if message and message['type'] == 'message':
                command = json.loads(message['data'])

                if command['type'] == 'reroute' and command['pallet_id'] == self.id:
                    new_destination = self.warehouses[command['warehouse']]['location']
                    self.logger.info(f"Rerouting to {command['warehouse']} at {new_destination}")
                    self.destination = new_destination
                    self._calculate_route()  # Recalculate route

                elif command['type'] == 'dispose' and command['pallet_id'] == self.id:
                    self.logger.warning("Disposal command received - goods will be disposed")
                    self.status = "AWAITING_DISPOSAL"

        except Exception as e:
            self.logger.error(f"Error processing command: {e}")
