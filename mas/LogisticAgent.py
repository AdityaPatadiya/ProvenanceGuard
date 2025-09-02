import json
import redis
import time
import logging
from datetime import datetime
import math

class LogisticsAgent:
    def __init__(self, log_file='../logs/logistics_agent.log'):
        self.redis_client = None
        self.pubsub = None
        self.warehouses = {
            "warehouse_amsterdam": {"location": [52.3676, 4.9041], "capacity": 100, "available": True},
            "warehouse_berlin": {"location": [52.5200, 13.4050], "capacity": 80, "available": True},
            "warehouse_paris": {"location": [48.8566, 2.3522], "capacity": 120, "available": True},
            "warehouse_brussels": {"location": [50.8503, 4.3517], "capacity": 60, "available": True}
        }
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
        """Calculate distance between two coordinates (simplified)"""
        # Simple Euclidean distance for simulation
        return math.sqrt((loc1[0] - loc2[0])**2 + (loc1[1] - loc2[1])**2)
    
    def find_nearest_warehouse(self, current_location):
        """Find the nearest available warehouse"""
        available_warehouses = {name: data for name, data in self.warehouses.items() 
                               if data['available']}
        
        if not available_warehouses:
            self.logger.warning("No available warehouses found!")
            return None
            
        # Find the closest warehouse
        nearest = min(available_warehouses.items(), 
                     key=lambda item: self.calculate_distance(current_location, item[1]['location']))
        
        self.logger.info(f"Nearest warehouse: {nearest[0]} at {nearest[1]['location']}")
        return nearest[0]
    
    def handle_temperature_alert(self, alert_data):
        """Handle temperature breach alerts"""
        pallet_id = alert_data['pallet_id']
        temperature = alert_data['temperature']
        location = alert_data['location']
        
        self.logger.warning(f"Handling temperature alert for {pallet_id}: {temperature}°C at {location}")
        
        # Find nearest warehouse
        warehouse = self.find_nearest_warehouse(location)
        
        if warehouse:
            # Create reroute command
            reroute_command = {
                'type': 'reroute',
                'pallet_id': pallet_id,
                'warehouse': warehouse,
                'timestamp': datetime.now().isoformat(),
                'reason': f'Temperature breach: {temperature}°C'
            }
            
            # Publish reroute command
            self.redis_client.publish('commands', json.dumps(reroute_command))
            self.logger.info(f"Issued reroute command for {pallet_id} to {warehouse}")
        else:
            self.logger.error(f"Could not find available warehouse for {pallet_id}")
    
    def handle_spoilage_alert(self, alert_data):
        """Handle goods spoilage alerts"""
        pallet_id = alert_data['pallet_id']
        location = alert_data['location']
        
        self.logger.critical(f"Handling spoilage alert for {pallet_id} at {location}")
        
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
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        channel = message['channel'].decode()
                        
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
                                
                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.error(f"Error processing message: {e}")
                
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