import asyncio
import json
import redis
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour

class ProductAgent(Agent):
    def __init__(self, jid: str, password: str, threshold: float = 8.0):
        super().__init__(jid, password)
        self.temperature_threshold = threshold

    class SensorBehaviour(CyclicBehaviour):
        def __init__(self, agent, threshold):
            super().__init__()
            self.agent = agent
            self.threshold = threshold

        async def on_start(self):
            # Connect to Redis
            print("Connecting to Redis...")
            try:
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
                self.pubsub = self.redis_client.pubsub()
                self.pubsub.subscribe('sensor_data')
                print(f"Subscribed to 'sensor_data' channel. Listening for temperature above {self.threshold}°C")
            except Exception as e:
                print(f"Redis connection error: {e}")

        async def run(self):
            try:
                message = self.pubsub.get_message(timeout=1.0)
                if message and message['type'] == 'message':
                    try:
                        data = json.loads(message['data'])
                        pallet_id = data['pallet_id']
                        temperature = data['temperature']
                        print(f"[{pallet_id}] Current Temp: {temperature}°C")

                        if temperature > self.threshold:
                            print(f"🚨 ALERT: Temperature breach detected! {temperature}°C is above {self.threshold}°C")
                            
                    except (json.JSONDecodeError, KeyError) as e:
                        print(f"Error processing message: {e}")
            except Exception as e:
                print(f"Error in run loop: {e}")
                
            await asyncio.sleep(0.1)

    async def setup(self):
        sensor_behaviour = self.SensorBehaviour(self, self.temperature_threshold)
        self.add_behaviour(sensor_behaviour)

async def main():
    # Create agent with proper configuration to handle self-signed certs
    agent = ProductAgent("product_agent@localhost", "password", threshold=8.0)
    
    # Try to disable SSL verification - this might work in newer SPADE versions
    try:
        # This is a common approach in newer SPADE versions
        import ssl
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        agent.ssl_context = ssl_context
    except:
        pass  # If this doesn't work, we'll try another approach
        
    try:
        await agent.start()
        print("Agent started successfully!")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"Failed to start agent: {e}")
        # Try option 4 - let's generate and use the certificate
        print("Trying to use Prosody's certificate...")
        await use_prosody_certificate()

async def use_prosody_certificate():
    """Try to use Prosody's certificate for connection"""
    try:
        # Find and use Prosody's certificate
        import ssl
        ssl_context = ssl.create_default_context()
        
        # Try to load Prosody's certificate (common locations)
        cert_paths = [
            "/var/lib/prosody/localhost.crt",
            "/etc/prosody/certs/localhost.crt"
        ]
        
        for cert_path in cert_paths:
            try:
                ssl_context.load_verify_locations(cert_path)
                print(f"Using certificate from {cert_path}")
                
                # Create agent with this context
                agent = ProductAgent("product_agent@localhost", "password", threshold=8.0)
                agent.ssl_context = ssl_context

                await agent.start()
                print("Agent started successfully with certificate!")
                return
            except FileNotFoundError:
                continue
                
        print("Could not find Prosody certificate. Please generate one:")
        print("sudo prosodyctl cert generate localhost")
        
    except Exception as e:
        print(f"Certificate approach also failed: {e}")

if __name__ == "__main__":
    asyncio.run(main())
