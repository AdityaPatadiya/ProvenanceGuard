# mas/send_command.py
import json
import redis
import sys

def send_warehouse_status(warehouse, status):
    """Send warehouse status update"""
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    command = {
        'type': 'warehouse_status',
        'warehouse': warehouse,
        'status': status,
        'timestamp': '2023-10-05T12:00:00Z'
    }
    
    r.publish('logistics_commands', json.dumps(command))
    print(f"Sent status update: {warehouse} = {status}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python send_command.py <warehouse_name> <true/false>")
        sys.exit(1)
        
    warehouse = sys.argv[1]
    status = sys.argv[2].lower() == 'true'
    
    send_warehouse_status(warehouse, status)
