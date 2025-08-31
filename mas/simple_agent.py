import json
import redis
import time

class SimpleProductAgent:
    def __init__(self, threshold=8.0):
        self.threshold = threshold
        self.redis_client = None
        self.pubsub = None
        
    def connect_to_redis(self):
        """Connect to Redis server"""
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
            self.pubsub = self.redis_client.pubsub()
            self.pubsub.subscribe('sensor_data')
            print("Connected to Redis and subscribed to 'sensor_data' channel")
            return True
        except redis.ConnectionError:
            print("ERROR: Could not connect to Redis")
            return False
            
    def run(self):
        """Main loop to process messages"""
        if not self.connect_to_redis():
            return
            
        print(f"Listening for temperature above {self.threshold}°C")
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

                        print(f"[{pallet_id}] Temp: {temperature}°C, Status: {status}")

                        # Check for temperature breach
                        if temperature > self.threshold:
                            print(f"🚨 ALERT: Temperature breach! {temperature}°C > {self.threshold}°C")

                        # Check if goods are spoiled
                        if status == "SPOILED":
                            print("❌ GOODS HAVE SPOILED! Taking action...")
                            # Here you would add code to handle the spoilage

                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error processing message: {e}")
                
                # Small delay to prevent CPU overuse
                time.sleep(0.1)
                
        except KeyboardInterrupt:
            print("Stopping agent...")
        finally:
            if self.pubsub:
                self.pubsub.close()

if __name__ == "__main__":
    agent = SimpleProductAgent(threshold=8.0)
    agent.run()