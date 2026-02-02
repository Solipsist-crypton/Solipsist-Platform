# src/python/api_bridge.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import json
import time
import threading
from arbitrage_volume import analyze_arbitrage_fast, get_all_data_with_volumes
from exchanges_all import ALL_EXCHANGES

app = Flask(__name__)
CORS(app)

# Кешовані дані
cache = {
    'arbitrage': None,
    'exchanges': None,
    'last_update': 0
}

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'timestamp': time.time()})

@app.route('/arbitrage')
def get_arbitrage():
    """Отримати арбітражні можливості"""
    # Перевірка кешу (30 секунд)
    if (cache['arbitrage'] and 
        time.time() - cache['last_update'] < 30 and
        not request.args.get('force')):
        return jsonify(cache['arbitrage'])
    
    try:
        # Викликаємо твою логіку
        result = analyze_arbitrage_fast(json_output=True)
        cache['arbitrage'] = result
        cache['last_update'] = time.time()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update', methods=['POST'])
def update_arbitrage():
    """Примусове оновлення арбітражу"""
    try:
        result = analyze_arbitrage_fast(json_output=True)
        cache['arbitrage'] = result
        cache['last_update'] = time.time()
        return jsonify({'status': 'updated', 'data': result})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/exchanges')
def get_exchanges():
    """Отримати список доступних бірж"""
    if not cache['exchanges']:
        cache['exchanges'] = list(ALL_EXCHANGES.keys())
    return jsonify(cache['exchanges'])

@app.route('/filters', methods=['POST'])
def set_filters():
    """Встановити фільтри"""
    filters = request.json
    # Зберегти фільтри у файл
    with open('filters.json', 'w') as f:
        json.dump(filters, f)
    return jsonify({'status': 'saved'})

@app.route('/config', methods=['GET'])
def get_config():
    """Отримати конфігурацію"""
    try:
        with open('config.json', 'r') as f:
            return jsonify(json.load(f))
    except:
        return jsonify({'min_spread': 1, 'min_volume': 100000})

if __name__ == '__main__':
    # Запускаємо у фоні
    app.run(port=5000, debug=False, threaded=True)