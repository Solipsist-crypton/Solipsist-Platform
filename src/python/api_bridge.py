# src/python/api_bridge.py
from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import json
import sys
import io
import time
import threading
from arbitrage_volume import get_arbitrage_for_api, get_all_data_with_volumes
from exchanges_all import ALL_EXCHANGES

app = Flask(__name__)
CORS(app)
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

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
    try:
        # Використовуй нову функцію
        result = get_arbitrage_for_api()  # або analyze_arbitrage_fast(json_output=True)
        cache['arbitrage'] = result
        cache['last_update'] = time.time()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/update', methods=['POST'])
def update_arbitrage():
    """Примусове оновлення арбітражу"""
    try:
        # НА ЦЕЙ:
        result = get_arbitrage_for_api()  # або analyze_arbitrage_fast(json_output=True), якщо додав параметр
        
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