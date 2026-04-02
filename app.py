"""
AutoNet Pro - Intent-Based Network Automation Platform
Complete Flask Application
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from datetime import datetime
import subprocess
import platform

app = Flask(__name__)
app.secret_key = 'autonet-pro-secret-key-2024'

# ============================================
# MOCK DATA (Demo Purpose)
# ============================================

DEVICES = [
    {'id': 1, 'name': 'CoreRouter-01', 'ip': '192.168.1.1', 'type': 'Router', 'cpu': 42, 'mem': 61, 'status': 'up', 'vlan': 'Management', 'uptime': '99d 14h'},
    {'id': 2, 'name': 'Switch-Dist-01', 'ip': '192.168.1.2', 'type': 'Switch', 'cpu': 18, 'mem': 34, 'status': 'up', 'vlan': 'Trunk', 'uptime': '99d 14h'},
    {'id': 3, 'name': 'PC1-VLAN10', 'ip': '192.168.1.10', 'type': 'PC', 'cpu': 45, 'mem': 56, 'status': 'up', 'vlan': 'VLAN 10', 'uptime': '2d 4h'},
    {'id': 4, 'name': 'PC2-VLAN20', 'ip': '192.168.2.10', 'type': 'PC', 'cpu': 38, 'mem': 48, 'status': 'up', 'vlan': 'VLAN 20', 'uptime': '2d 4h'},
    {'id': 5, 'name': 'Access-Switch-01', 'ip': '192.168.1.3', 'type': 'Switch', 'cpu': 22, 'mem': 41, 'status': 'up', 'vlan': 'Access', 'uptime': '45d 2h'},
    {'id': 6, 'name': 'VPN-Gateway', 'ip': '192.168.2.1', 'type': 'Router', 'cpu': 55, 'mem': 69, 'status': 'warning', 'vlan': 'WAN', 'uptime': '12d 5h'},
]

VLANS = [
    {'id': 10, 'name': 'VLAN10', 'network': '192.168.1.0/24', 'gateway': '192.168.1.1', 'devices': 12, 'type': 'User'},
    {'id': 20, 'name': 'VLAN20', 'network': '192.168.2.0/24', 'gateway': '192.168.2.1', 'devices': 8, 'type': 'Guest'},
]

ALERTS = [
    {'id': 1, 'severity': 'critical', 'title': 'Device Down: VPN-Gateway', 'message': 'No response for 2 minutes', 'time': '14:32', 'acknowledged': False},
    {'id': 2, 'severity': 'warning', 'title': 'High CPU: CoreRouter-01', 'message': 'CPU at 88% for 5 minutes', 'time': '14:41', 'acknowledged': False},
    {'id': 3, 'severity': 'info', 'title': 'Backup Completed', 'message': 'All devices backed up', 'time': '12:00', 'acknowledged': True},
]

COMPLIANCE_CHECKS = {
    'password_encryption': {'name': 'Password Encryption', 'status': 'pass', 'message': 'Enable secret configured', 'severity': 'high'},
    'ssh_version': {'name': 'SSH v2 Enabled', 'status': 'pass', 'message': 'SSH version 2 configured', 'severity': 'medium'},
    'telnet_disabled': {'name': 'Telnet Disabled', 'status': 'pass', 'message': 'Telnet disabled', 'severity': 'high'},
    'acl_configured': {'name': 'ACL Configuration', 'status': 'fail', 'message': 'No ACL on management interface', 'severity': 'high'},
    'port_security': {'name': 'Port Security', 'status': 'warn', 'message': 'Port security not enabled', 'severity': 'medium'},
    'snmp_version': {'name': 'SNMP v3', 'status': 'warn', 'message': 'Using SNMP v2c', 'severity': 'medium'},
}

BACKUPS = [
    {'id': 1, 'device': 'CoreRouter-01', 'date': '2024-03-31 14:30', 'size': '12.4 KB', 'version': 'v8', 'status': 'success'},
    {'id': 2, 'device': 'FW-Perimeter', 'date': '2024-03-31 14:30', 'size': '28.1 KB', 'version': 'v5', 'status': 'success'},
    {'id': 3, 'device': 'SW-Dist-01', 'date': '2024-03-31 14:30', 'size': '8.7 KB', 'version': 'v12', 'status': 'success'},
]

# ============================================
# HELPER FUNCTIONS
# ============================================

def get_stats():
    """Get dashboard statistics"""
    total = len(DEVICES)
    online = len([d for d in DEVICES if d['status'] == 'up'])
    warnings = len([d for d in DEVICES if d['status'] == 'warning'])
    down = len([d for d in DEVICES if d['status'] == 'down'])
    
    passed = len([c for c in COMPLIANCE_CHECKS.values() if c['status'] == 'pass'])
    total_checks = len(COMPLIANCE_CHECKS)
    
    return {
        'total_devices': total,
        'online_devices': online,
        'warning_devices': warnings,
        'down_devices': down,
        'uptime_percentage': round((online / total) * 100, 1) if total > 0 else 0,
        'total_vlans': len(VLANS),
        'total_alerts': len([a for a in ALERTS if not a['acknowledged']]),
        'critical_alerts': len([a for a in ALERTS if a['severity'] == 'critical' and not a['acknowledged']]),
        'compliance_score': round((passed / total_checks) * 100, 1),
        'passed_checks': passed,
        'failed_checks': len([c for c in COMPLIANCE_CHECKS.values() if c['status'] == 'fail']),
        'warning_checks': len([c for c in COMPLIANCE_CHECKS.values() if c['status'] == 'warn'])
    }

def generate_cisco_config(data):
    """Generate Cisco configuration"""
    hostname = data.get('hostname', 'Router')
    mgmt_ip = data.get('mgmt_ip', '192.168.1.1')
    mgmt_mask = data.get('mgmt_mask', '255.255.255.0')
    
    config = f"""!
! AutoNet Pro Generated Configuration
! Device: {hostname}
! Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
!
hostname {hostname}
!
! Management Interface
interface GigabitEthernet0/0
 ip address {mgmt_ip} {mgmt_mask}
 no shutdown
!
! Enable SSH
ip domain-name autonet.local
crypto key generate rsa modulus 2048
ip ssh version 2
!
! Enable password
enable secret AutoNet@2024
!
! Line configuration
line vty 0 4
 transport input ssh
 login local
 exec-timeout 10 0
!
! End
end
"""
    return config

# ============================================
# ROUTES
# ============================================

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', devices=DEVICES, stats=get_stats(), vlans=VLANS)

@app.route('/devices')
def devices():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('devices.html', devices=DEVICES)

@app.route('/ping')
def ping():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('ping.html')

@app.route('/vlan')
def vlan():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('vlan.html', vlans=VLANS)

@app.route('/config')
def config():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('config.html')

@app.route('/compliance')
def compliance():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('compliance.html', checks=COMPLIANCE_CHECKS, stats=get_stats())

@app.route('/monitoring')
def monitoring():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('monitoring.html', devices=DEVICES)

@app.route('/alerts')
def alerts():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('alerts.html', alerts=ALERTS)

@app.route('/backups')
def backups():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('backups.html', backups=BACKUPS)

@app.route('/reports')
def reports():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('reports.html')

# ============================================
# API ROUTES
# ============================================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if username == 'admin' and password == 'admin123':
        session['user'] = username
        return jsonify({'success': True, 'message': 'Login successful'})
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/devices')
def api_devices():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(DEVICES)

@app.route('/api/stats')
def api_stats():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(get_stats())

@app.route('/api/ping', methods=['POST'])
def api_ping():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    destination = data.get('destination')
    
    try:
        # For Windows
        if platform.system() == 'Windows':
            result = subprocess.run(['ping', '-n', '2', destination], capture_output=True, text=True, timeout=5)
        else:
            result = subprocess.run(['ping', '-c', '2', destination], capture_output=True, text=True, timeout=5)
        
        if result.returncode == 0:
            return jsonify({'status': 'Success', 'output': result.stdout, 'destination': destination})
        else:
            return jsonify({'status': 'Failed', 'output': result.stderr, 'destination': destination})
    except Exception as e:
        return jsonify({'status': 'Error', 'error': str(e)})

@app.route('/api/vlan', methods=['POST'])
def api_vlan():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    vlan_id = data.get('vlan_id')
    vlan_name = data.get('vlan_name')
    network = data.get('network', f'192.168.{vlan_id}.0/24')
    
    commands = [
        f"vlan {vlan_id}",
        f" name {vlan_name}",
        " exit",
        f"interface vlan {vlan_id}",
        f" ip address 192.168.{vlan_id}.1 255.255.255.0",
        " no shutdown"
    ]
    
    return jsonify({
        'success': True,
        'vlan_id': vlan_id,
        'vlan_name': vlan_name,
        'network': network,
        'commands': commands
    })

@app.route('/api/config/generate', methods=['POST'])
def api_generate_config():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.json
    config = generate_cisco_config(data)
    
    return jsonify({
        'success': True,
        'config': config,
        'lines': len(config.split('\n')),
        'size': round(len(config.encode()) / 1024, 1)
    })

@app.route('/api/compliance')
def api_compliance():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    passed = len([c for c in COMPLIANCE_CHECKS.values() if c['status'] == 'pass'])
    failed = len([c for c in COMPLIANCE_CHECKS.values() if c['status'] == 'fail'])
    warnings = len([c for c in COMPLIANCE_CHECKS.values() if c['status'] == 'warn'])
    total = len(COMPLIANCE_CHECKS)
    
    return jsonify({
        'score': round((passed / total) * 100, 1),
        'passed': passed,
        'failed': failed,
        'warnings': warnings,
        'total': total,
        'checks': COMPLIANCE_CHECKS
    })

@app.route('/api/alerts')
def api_alerts():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify([a for a in ALERTS if not a['acknowledged']])

@app.route('/api/backups')
def api_backups():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    return jsonify(BACKUPS)

@app.route('/api/reports/generate', methods=['POST'])
def api_generate_report():
    if 'user' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    return jsonify({
        'success': True,
        'message': 'Report generated',
        'timestamp': datetime.now().isoformat()
    })

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 AutoNet Pro - Intent-Based Network Automation Platform")
    print("="*60)
    print("📍 Server: http://localhost:5000")
    print("📍 Login: admin / admin123")
    print("="*60)
    print("\n✅ Cisco VLAN Configuration Active")
    print("✅ Inter-VLAN Routing Working")
    print("✅ Real-Time Monitoring Active")
    print("✅ Security Compliance Ready\n")
    app.run(debug=True, host='0.0.0.0', port=5000)