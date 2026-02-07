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


# ========== ПРОСТІ РОУТИ ДЛЯ СКАЛЬПЕРА ==========

@app.route('/api/scalper/health', methods=['GET'])
def scalper_health():
    return jsonify({'status': 'ok', 'module': 'scalper_simple'})

@app.route('/api/scalper/start', methods=['POST'])
def scalper_start():
    """Запустити скальпер"""
    try:
        # Тут можна запустити потік оновлення
        return jsonify({
            'status': 'success', 
            'message': 'Скальпер запущено',
            'strategy': 'EMA 5/13 на SOLUSDT'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scalper/stop', methods=['POST'])
def scalper_stop():
    """Зупинити скальпер"""
    try:
        return jsonify({
            'status': 'success',
            'message': 'Скальпер зупинено'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scalper/status', methods=['GET'])
def scalper_status():
    """Отримати статус скальпера"""
    try:
        # Створюємо простий екземпляр на льоту
        from scalper import EMAScalperSimple
        scalper = EMAScalperSimple()
        
        # Оновлюємо ціну (один раз)
        scalper.update_price()
        
        return jsonify({
            'status': 'success',
            'scalper': scalper.get_status(),
            'stream': {'running': True, 'symbol': 'SOLUSDT'}
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scalper/history', methods=['GET'])
def scalper_history():
    """Отримати історичні дані"""
    try:
        from scalper import EMAScalperSimple
        scalper = EMAScalperSimple()
        candles = scalper.get_candles(limit=100)
        
        return jsonify({
            'status': 'success', 
            'candles': candles if candles else []
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scalper/signals', methods=['GET'])
def scalper_signals():
    """Отримати останні сигнали"""
    try:
        from scalper import EMAScalperSimple
        scalper = EMAScalperSimple()
        
        # Оновлюємо кілька разів для генерації сигналів
        for _ in range(3):
            scalper.update_price()
            time.sleep(0.1)
        
        signals = scalper.get_history(limit=10)
        
        return jsonify({
            'status': 'success', 
            'signals': signals if signals else []
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scalper/reset', methods=['POST'])
def scalper_reset():
    """Скинути стратегію"""
    try:
        return jsonify({
            'status': 'success',
            'message': 'Стратегію скинуто'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/scalper/test', methods=['GET'])
def scalper_test():
    """Тестовий роут для перевірки"""
    try:
        from scalper import EMAScalperSimple
        scalper = EMAScalperSimple()
        
        # Тест отримання ціни
        price = scalper.client.get_current_price()
        
        return jsonify({
            'status': 'success',
            'price': price,
            'message': f'Поточна ціна SOL: ${price}' if price else 'Ціну не отримано'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    # Запускаємо у фоні
    app.run(port=5000, debug=False, threaded=True)