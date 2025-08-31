import json
import time
import numpy as np
from datetime import datetime, timedelta

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
        self.cooling_unit_efficiency = 0.97  ##### SCENARIO FLAG #####
        self.is_moving = True       ##### SCENARIO FLAG #####

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
