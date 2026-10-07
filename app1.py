from flask import Flask, render_template, jsonify
import random
import time

app = Flask(__name__)

@app.route('/')
def dashboard():
    # Serves the main centralized monitoring dashboard
    return render_template('index.html')

@app.route('/api/telemetry')
def get_telemetry():
    # Simulates AI-driven network telemetry and Zero-Trust metrics
    vlan_traffic = {
        'Student VLAN': random.randint(3000, 4500),
        'Faculty VLAN': random.randint(200, 400),
        'IoT VLAN': random.randint(800, 1200),
        'Admin VLAN': random.randint(50, 100),
        'Guest VLAN': random.randint(100, 300)
    }
    
    return jsonify({
        'timestamp': time.strftime("%H:%M:%S"),
        'active_identities': random.randint(4800, 5000), # Targeting the 5,000 user capacity
        'ai_threats_blocked': random.randint(0, 15),
        'network_health': random.randint(94, 100),
        'vlan_data': vlan_traffic,
        'recent_alerts': [
            {"type": "IDS/IPS", "message": "Unauthorized access attempt blocked on ERP System"},
            {"type": "MFA", "message": "Failed biometric prompt from Guest VLAN"},
            {"type": "IoT", "message": "Smart Classroom AP anomaly detected and isolated"}
        ]
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)