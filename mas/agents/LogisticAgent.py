import json
import redis
import time
import logging
import os
import sys
from datetime import datetime

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
appended_path = sys.path.append(project_root)

# Now you can import from the blockchain package
from blockchain.integration import BlockchainRecorder


class LogisticsAgent:
    def __init__(self, log_file='../../logs/logistics_agent.log'):
        self.redis_client = None
        self.pubsub = None
        self.warehouses = {
            "warehouse_amsterdam": {"location": [52.3676, 4.9041], "capacity": 100, "available": True},
            "warehouse_berlin": {"location": [52.5200, 13.4050], "capacity": 80, "available": True},
            "warehouse_paris": {"location": [48.8566, 2.3522], "capacity": 120, "available": True},
            "warehouse_brussels": {"location": [50.8503, 4.3517], "capacity": 60, "available": True}
        }
        self.blockchain_recorder = BlockchainRecorder()
        self.setup_logging(log_file)

    def setup_logging(self, log_file):
        """Set up logging to file"""
        self.logger = logging.getLogger('LogisticsAgent')
        self.logger.setLevel(logging.INFO)

        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        self.logger.addHandler(fh)
        self.logger.addHandler(ch)

        self.logger.info("Logistics Agent initialized")

    def connect_to_redis(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe('alerts')  # Subscribe to alerts channel
            self.pubsub.subscribe('logistics_commands')  # Subscribe to commands channel
            self.logger.info("Connected to Redis and subscribed to channels")
            return True
        except redis.ConnectionError:
            self.logger.error("Could not connect to Redis")
            return False

    def calculate_distance(self, loc1, loc2):
        """
        Calculate simplified distance between two coordinates.
        In a real implementation, you would use a proper geospatial library.

        Args:
            loc1 (list): [lat1, lon1]
            loc2 (list): [lat2, lon2]

        Returns:
            float: Distance between the points
        """
        try:
            # Simple Euclidean distance for demonstration
            # In production, use Haversine formula for real distances
            lat_diff = loc1[0] - loc2[0]
            lon_diff = loc1[1] - loc2[1]
            return (lat_diff**2 + lon_diff**2)**0.5
        except (IndexError, TypeError) as e:
            self.logger.error(f"Error calculating distance: {e}")
            raise ValueError("Invalid coordinate format")

    def find_nearest_warehouse(self, current_location):
        """
        Find the nearest available warehouse to the current location.

        Args:
            current_location (list): [latitude, longitude] of the current position

        Returns:
            str: Name of the nearest available warehouse, or None if none available
        """
        try:
            available_warehouses = {
                name: data for name, data in self.warehouses.items() 
                if data['available'] and data['capacity'] > 0
            }

            if not available_warehouses:
                self.logger.warning("No available warehouses with capacity")
                return None

            # Calculate distances to all available warehouses
            distances = {}
            for name, data in available_warehouses.items():
                try:
                    warehouse_loc = data['location']
                    distance = self.calculate_distance(current_location, warehouse_loc)
                    distances[name] = distance
                except (KeyError, TypeError) as e:
                    self.logger.error(f"Error calculating distance to {name}: {e}")
                    continue

            if not distances:
                self.logger.error("Could not calculate distances to any warehouse")
                return None

            # Find the nearest warehouse
            nearest_warehouse = min(distances.items(), key=lambda x: x[1])[0]
            self.logger.info(
                f"Selected {nearest_warehouse} at distance {distances[nearest_warehouse]:.2f} units"
            )

            return nearest_warehouse

        except Exception as e:
            self.logger.error(f"Error in find_nearest_warehouse: {e}")
            return None

    def handle_temperature_alert(self, alert_data):
        """
        Handle temperature breach alerts by finding the nearest available warehouse
        and issuing a reroute command.

        Args:
            alert_data (dict): The alert data containing pallet information
        """
        try:
            # Extract data with defensive programming to handle missing keys
            pallet_id = alert_data.get('pallet_id', 'UNKNOWN_PALLET')
            temperature = alert_data.get('temperature', 0)
            location = alert_data.get('location', {})
            timestamp = alert_data.get('timestamp', datetime.now().isoformat())

            # Log the received alert
            self.logger.warning(
                f"Processing temperature alert for {pallet_id}: "
                f"{temperature}°C at location {location}"
            )

            # Validate required data
            if pallet_id == 'UNKNOWN_PALLET':
                self.logger.error("Alert missing pallet ID")
                return

            if not isinstance(location, dict) or 'lat' not in location or 'lon' not in location:
                self.logger.error(f"Invalid location data for {pallet_id}: {location}")
                return

            # Convert location to coordinates
            try:
                current_location = [float(location['lat']), float(location['lon'])]
            except (ValueError, TypeError) as e:
                self.logger.error(f"Invalid coordinate format for {pallet_id}: {e}")
                return

            # Find the nearest available warehouse
            warehouse = self.find_nearest_warehouse(current_location)

            if not warehouse:
                self.logger.error(f"No available warehouse found for {pallet_id}")

                # Send a failure notification
                failure_alert = {
                    'type': 'reroute_failed',
                    'pallet_id': pallet_id,
                    'reason': 'No available warehouses',
                    'timestamp': timestamp,
                    'original_alert': alert_data
                }
                self.redis_client.publish('alerts', json.dumps(failure_alert))
                return

            # Create reroute command
            reroute_command = {
                'type': 'reroute',
                'pallet_id': pallet_id,
                'warehouse': warehouse,
                'original_location': location,
                'new_location': self.warehouses[warehouse]['location'],
                'temperature': temperature,
                'timestamp': timestamp,
                'reason': f'Temperature breach: {temperature}°C'
            }

            # Publish reroute command
            try:
                self.redis_client.publish('commands', json.dumps(reroute_command))
                self.logger.info(
                    f"Issued reroute command for {pallet_id} to {warehouse} "
                    f"at {self.warehouses[warehouse]['location']}"
                )

                tx_hash = self.blockchain_recorder.record_temperature_breach(pallet_id, temperature, location)
                if tx_hash:
                    self.logger.info(f"Temperature breach recorded on blockchain: {tx_hash}")
                else:
                    self.logger.warning("Failed to record temperature breach on blockchain")

                # Record success in log with all relevant details
                success_log = {
                    'event': 'reroute_commanded',
                    'pallet_id': pallet_id,
                    'from_location': location,
                    'to_warehouse': warehouse,
                    'to_location': self.warehouses[warehouse]['location'],
                    'temperature': temperature,
                    'timestamp': timestamp
                }
                self.logger.info(f"Reroute details: {json.dumps(success_log)}")

            except Exception as e:
                self.logger.error(f"Failed to publish reroute command for {pallet_id}: {e}")

        except KeyError as e:
            self.logger.error(f"Missing key in alert data for {pallet_id}: {e}")
            self.logger.debug(f"Problematic alert data: {alert_data}")

        except Exception as e:
            self.logger.error(f"Unexpected error handling temperature alert for {pallet_id}: {e}")
            self.logger.debug(f"Alert data: {alert_data}")

        except Exception as e:
            self.logger.error(f"Error handling temperature alert: {e}")
            # Log the full alert data for debugging
            self.logger.debug(f"Alert data that caused error: {alert_data}")

    def handle_spoilage_alert(self, alert_data):
        """Handle goods spoilage alerts"""
        try:
            pallet_id = alert_data.get('pallet_id', 'UNKNOWN_PALLET')
            location = alert_data.get('location', {})

            # Convert location to a string for logging
            if isinstance(location, dict):
                loc_str = f"lat: {location.get('lat', 'unknown')}, lon: {location.get('lon', 'unknown')}"
            else:
                loc_str = str(location)

            self.logger.critical(f"Handling spoilage alert for {pallet_id} at {loc_str}")

            # Create disposal command
            disposal_command = {
                'type': 'dispose',
                'pallet_id': pallet_id,
                'timestamp': datetime.now().isoformat(),
                'reason': 'Goods spoiled'
            }

            # Publish disposal command
            self.redis_client.publish('commands', json.dumps(disposal_command))
            self.logger.info(f"Issued disposal command for {pallet_id}")

        except Exception as e:
            self.logger.error(f"Error handling spoilage alert: {e}")
            self.logger.debug(f"Alert data that caused error: {alert_data}")

    def handle_warehouse_status(self, command_data):
        """Handle warehouse status updates"""
        warehouse = command_data.get('warehouse')
        status = command_data.get('status')

        if warehouse in self.warehouses:
            self.warehouses[warehouse]['available'] = status
            status_text = "available" if status else "unavailable"
            self.logger.info(f"Updated {warehouse} status to {status_text}")
        else:
            self.logger.warning(f"Unknown warehouse: {warehouse}")

    def run(self):
        """Main loop to process messages"""
        if not self.connect_to_redis():
            return

        self.logger.info("Logistics Agent started. Listening for alerts...")
        print("Logistics Agent running. Press Ctrl+C to stop...")

        try:
            while True:
                # Check for new messages
                message = self.pubsub.get_message(timeout=1.0)
                print(f"message: {message}")
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        channel = message['channel'].decode()

                        self.logger.debug(f"Received message on channel {channel}: {data}")

                        if channel == 'alerts':
                            alert_type = data.get('type')

                            if alert_type == 'temperature_breach':
                                self.handle_temperature_alert(data)
                            elif alert_type == 'spoilage':
                                self.handle_spoilage_alert(data)
                            else:
                                self.logger.warning(f"Unknown alert type: {alert_type}")

                        elif channel == 'logistics_commands':
                            command_type = data.get('type')

                            if command_type == 'warehouse_status':
                                self.handle_warehouse_status(data)
                            else:
                                self.logger.warning(f"Unknown command type: {command_type}")

                    except (json.JSONDecodeError) as e:
                        self.logger.error(f"Error processing message: {e}")
                    except (KeyError) as e:
                        self.logger.error(f"KeyError occure: {channel}")

                time.sleep(0.1)

        except KeyboardInterrupt:
            self.logger.info("Logistics Agent stopped by user")
            print("Stopping Logistics Agent...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            print(f"Unexpected error: {e}")
        finally:
            if self.pubsub:
                self.pubsub.close()
            self.logger.info("Logistics Agent shutdown complete")

if __name__ == "__main__":
    agent = LogisticsAgent()
    agent.run()
