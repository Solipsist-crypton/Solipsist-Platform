# src/python/simple_scalper_api.py
from flask import Flask, jsonify
import time
import sys
import os

# Фікс для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

app = Flask(__name__)

print("=" * 70)
print("SIMPLE SCALPER API")
print("Running on: http://127.0.0.1:5000")
print("=" * 70)

# ========== ПРОСТІ РОУТИ ==========

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': time.time()})

@app.route('/api/scalper/test')
def test():
    return jsonify({
        'status': 'success',
        'price': 86.24,
        'message': 'API is working',
        'symbol': 'SOL/USDT'
    })

@app.route('/api/scalper/status')
def status():
    return jsonify({
        'status': 'success',
        'scalper': {
            'running': False,
            'position': None,
            'equity': 1000.0,
            'total_signals': 0,
            'win_rate': 0
        },
        'stream': {'running': False},
        'timestamp': time.time()
    })

@app.route('/api/scalper/start', methods=['POST'])
def start():
    return jsonify({
        'status': 'success',
        'message': 'Started',
        'running': True
    })

@app.route('/api/scalper/stop', methods=['POST'])
def stop():
    return jsonify({
        'status': 'success',
        'message': 'Stopped',
        'running': False
    })

@app.route('/arbitrage')
def arbitrage():
    # Імпортуємо тільки коли потрібно
    try:
        from arbitrage_volume import get_arbitrage_for_api
        return jsonify(get_arbitrage_for_api())
    except:
        return jsonify({'opportunities': [], 'stats': {}})

if __name__ == '__main__':
    print("Available routes:")
    print("  GET  /health")
    print("  GET  /api/scalper/test")
    print("  GET  /api/scalper/status")
    print("  POST /api/scalper/start")
    print("  POST /api/scalper/stop")
    print("  GET  /arbitrage")
    print("=" * 70)
    
    app.run(host='127.0.0.1', port=5000, debug=False)