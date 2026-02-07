# src/python/electron_debug.py
from flask import Flask, jsonify
import time
import os
import sys

app = Flask(__name__)

print("=" * 60)
print("🧪 ELECTRON DEBUG API")
print(f"PID: {os.getpid()}")
print(f"CWD: {os.getcwd()}")
print("=" * 60)

@app.route('/test')
def test():
    return jsonify({'status': 'ok', 'from': 'electron_debug'})

@app.route('/api/scalper/status')
def status():
    return jsonify({
        'status': 'success',
        'scalper': {'running': False, 'equity': 1000},
        'timestamp': time.time()
    })

@app.route('/<path:any_path>')
def catch_all(any_path):
    return jsonify({
        'status': 'error',
        'message': f'Route /{any_path} not found',
        'available_routes': ['/test', '/api/scalper/status', '/health']
    }), 404

if __name__ == '__main__':
    print("🌐 Запуск на порті 5000...")
    print("✅ Доступні роути: /test, /api/scalper/status")
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True)