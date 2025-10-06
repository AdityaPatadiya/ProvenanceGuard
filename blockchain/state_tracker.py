import redis
import json
from datetime import datetime

class PalletStateTracker:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=1)  # use db=1 to separate from main messaging

    def update_pallet(self, pallet_id, **fields):
        """Update or create pallet state"""
        try:
            key = f"pallet:{pallet_id}"
            fields["last_updated"] = datetime.now().isoformat()
            self.redis_client.hset(key, mapping=fields)
        except Exception as e:
            print(f"[StateTracker] Error updating pallet {pallet_id}: {e}")

    def get_pallet(self, pallet_id):
        """Fetch current state"""
        key = f"pallet:{pallet_id}"
        data = self.redis_client.hgetall(key)
        return {k.decode(): v.decode() for k, v in data.items()}

    def get_all_pallets(self):
        """Return all pallet states"""
        pallets = []
        for key in self.redis_client.keys("pallet:*"):
            data = self.redis_client.hgetall(key)
            pallets.append({k.decode(): v.decode() for k, v in data.items()})
        return pallets
    
    def print_all_states(self):
        for pallet in self.get_all_pallets():
            print(json.dumps(pallet, indent=2))
