import json
import redis
import time
import logging
from datetime import datetime


class SimpleProductAgent:
    def __init__(self, threshold=8.0, log_file='../logs/supply_chain.log'):
        self.threshold = threshold
        self.redis_client = None
        self.pubsub = None
        self.setup_logging(log_file)

    def setup_logging(self, log_file):
        """Set up logging to file"""
        # Create a logger
        self.logger = logging.getLogger('SupplyChainAgent')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler which logs even debug messages
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        
        # Create console handler with a higher log level
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        # Add the handlers to the logger
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
        
        self.logger.info("Supply Chain Agent initialized")

    def connect_to_redis(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe('sensor_data')
            self.logger.info("Connected to Redis and subscribed to 'sensor_data' channel")  # <-- Log
            return True
        except redis.ConnectionError:
            self.logger.error("Could not connect to Redis")  # <-- Log error
            return False

    # Add this method to your SimpleProductAgent class
    def handle_temperature_breach(self, pallet_id, temperature, location):
        """Enhanced with detailed logging"""
        log_data = {
            'pallet_id': pallet_id,
            'temperature': temperature,
            'location': location,
            'threshold': self.threshold,
            'timestamp': datetime.now().isoformat()
        }

        self.logger.warning(f"Temperature breach detected: {log_data}")

        if temperature > 10:  # Critical breach
            self.logger.critical(f"EMERGENCY: {pallet_id} at critical temperature {temperature}°C")
            print("🆘 EMERGENCY: Initiating immediate reroute!")

        elif temperature > self.threshold:
            self.logger.warning(f"Standard breach: {pallet_id} at {temperature}°C")
            print("⚠️  WARNING: Notifying logistics")

    def initiate_reroute(self, pallet_id, current_location):
        """Simulate finding the nearest warehouse"""
        # This is a simple simulation - in real life, you'd use GPS coordinates
        warehouses = {
            "warehouse_1": [52.3676, 4.9041],  # Amsterdam
            "warehouse_2": [52.5200, 13.4050],  # Berlin
        }

        # Find closest warehouse (simple distance calculation)
        closest_warehouse = min(warehouses, key=lambda wh: 
            abs(warehouses[wh][0] - current_location[0]) + 
            abs(warehouses[wh][1] - current_location[1])
        )

        print(f"📦 Rerouting {pallet_id} to {closest_warehouse}")
        # TODO: Actually communicate this to the logistics system

    def notify_logistics(self, pallet_id, temperature, location):
        """Simulate notifying a logistics system"""
        print(f"📧 Sent alert to logistics team: {pallet_id} at {temperature}°C")

    # Add this method to your SimpleProductAgent class
    def send_alert(self, alert_type, data):
        """Send alert to LogisticsAgent"""
        alert_data = {
            'type': alert_type,
            'pallet_id': data['pallet_id'],
            'temperature': data.get('temperature'),
            'location': data.get('location', 'Unknown'),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            self.redis_client.publish('alerts', json.dumps(alert_data))
            self.logger.info(f"Sent {alert_type} alert for {data['pallet_id']}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")

    def run(self):
        """Main loop to process messages"""
        if not self.connect_to_redis():
            return

        self.logger.info(f"Listening for temperature above {self.threshold}°C")  # <-- Log
        print("Press Ctrl+C to stop...")

        try:
            while True:
                # Check for new messages
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        pallet_id = data['pallet_id']
                        temperature = data['temperature']
                        status = data.get('status', 'UNKNOWN')

                        # Log the regular temperature reading
                        self.logger.info(f"[{pallet_id}] Temp: {temperature}°C, Status: {status}")
                        print(f"[{pallet_id}] Temp: {temperature}°C, Status: {status}")

                        # Check for temperature breach
                        if temperature > self.threshold:
                            self.logger.warning(f"Temperature breach: {temperature}°C > threshold {self.threshold}°C")
                            print(f"🚨 ALERT: Temperature breach! {temperature}°C > {self.threshold}°C")
                            # Send alert to LogisticsAgent
                            self.send_alert('temperature_breach', {
                                'pallet_id': pallet_id,
                                'temperature': temperature,
                                'location': data.get('location', 'Unknown')
                            })

                        # Check if goods are spoiled
                        if status == "SPOILED":
                            self.logger.critical(f"GOODS SPOILED: {pallet_id}")
                            print("❌ GOODS HAVE SPOILED! Taking action...")
                            # Send alert to LogisticsAgent
                            self.send_alert('spoilage', {
                                'pallet_id': pallet_id,
                                'location': data.get('location', 'Unknown')
                            })

                    except (json.JSONDecodeError, KeyError) as e:
                        self.logger.error(f"Error processing message: {e}")  # <-- Log error
                        print(f"Error processing message: {e}")

                time.sleep(0.1)

        except KeyboardInterrupt:
            self.logger.info("Agent stopped by user")  # <-- Log
            print("Stopping agent...")
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")  # <-- Log unexpected errors
            print(f"Unexpected error: {e}")
        finally:
            if self.pubsub:
                self.pubsub.close()
            self.logger.info("Agent shutdown complete")  # <-- Log


if __name__ == "__main__":
    agent = SimpleProductAgent(threshold=8.0)
    agent.run()
