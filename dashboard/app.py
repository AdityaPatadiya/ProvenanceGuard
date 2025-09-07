# dashboard/app.py
from flask import Flask, render_template, jsonify
import redis
from datetime import datetime

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/api/status')
def get_status():
    """Get current system status"""
    try:
        # Get recent alerts (this would be more sophisticated in real implementation)
        return jsonify({
            'timestamp': datetime.now().isoformat(),
            'active_shipments': 1,
            'temperature_alerts': 5,
            'spoilage_events': 2,
            'system_status': 'operational'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
