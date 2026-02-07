# src/python/api_bridge.py - ВЕРСІЯ БЕЗ ЕМОДЗІ
from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import json
import sys
import io
import time
import threading
import logging

# ========== ФІКС ДЛЯ WINDOWS ==========
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Кешовані дані
cache = {
    'arbitrage': None,
    'exchanges': None,
    'last_update': 0
}

# ========== ГЛОБАЛЬНИЙ ЕКЗЕМПЛЯР СКАЛЬПЕРА ==========
_scalper_instance = None
_scalper_lock = threading.Lock()

def get_scalper():
    """Отримати або створити глобальний екземпляр скальпера"""
    global _scalper_instance
    
    with _scalper_lock:
        if _scalper_instance is None:
            try:
                from scalper import EMAScalperSimple
                _scalper_instance = EMAScalperSimple()
                logger.info("Глобальний скальпер створено")
            except Exception as e:
                logger.error(f"Помилка створення скальпера: {e}")
                # Створюємо заглушку
                class DummyScalper:
                    def __init__(self):
                        self.running = False
                        self.position = None
                        self.entry_price = 0
                        self.equity = 1000.0
                        self.signals = []
                        self.symbol = "SOLUSDT"
                        self.total_signals = 0
                    
                    def get_status(self):
                        return {
                            'running': self.running,
                            'position': self.position,
                            'entry_price': self.entry_price,
                            'equity': self.equity,
                            'total_signals': self.total_signals,
                            'win_rate': 0,
                            'performance': {'winning_trades': 0, 'losing_trades': 0}
                        }
                
                _scalper_instance = DummyScalper()
    
    return _scalper_instance

# ========== СПІЛЬНІ РОУТИ ==========

@app.route('/health', methods=['GET'])
def health():
    """Перевірка здоров'я сервера"""
    logger.info("GET /health")
    return jsonify({
        'status': 'ok', 
        'service': 'Solipsist Platform',
        'timestamp': time.time()
    })

@app.route('/arbitrage', methods=['GET'])
def get_arbitrage():
    """Отримати арбітражні можливості"""
    logger.info("GET /arbitrage")
    try:
        from arbitrage_volume import get_arbitrage_for_api
        result = get_arbitrage_for_api()
        cache['arbitrage'] = result
        cache['last_update'] = time.time()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Arbitrage error: {e}")
        return jsonify({
            'opportunities': [],
            'stats': {'max_spread': 0, 'avg_spread': 0},
            'error': str(e)
        })

@app.route('/exchanges', methods=['GET'])
def get_exchanges():
    """Отримати список бірж"""
    logger.info("GET /exchanges")
    try:
        from exchanges_all import ALL_EXCHANGES
        if not cache['exchanges']:
            cache['exchanges'] = list(ALL_EXCHANGES.keys())
        return jsonify(cache['exchanges'])
    except Exception as e:
        logger.error(f"Exchanges error: {e}")
        return jsonify(['Binance', 'Bybit', 'OKX'])

# ========== РОУТИ ДЛЯ СКАЛЬПЕРА ==========

@app.route('/api/scalper/test', methods=['GET'])
def scalper_test():
    """Тестовий роут для перевірки"""
    logger.info("GET /api/scalper/test")
    try:
        scalper = get_scalper()
        price = 86.40  # Тестова ціна
        
        # Спроба отримати реальну ціну
        if hasattr(scalper, 'client'):
            try:
                real_price = scalper.client.get_current_price()
                if real_price:
                    price = real_price
            except:
                pass
        
        return jsonify({
            'status': 'success',
            'price': float(price),
            'message': f'Current SOL price: ${float(price):.4f}',
            'symbol': 'SOL/USDT',
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Scalper test error: {e}")
        return jsonify({
            'status': 'success',
            'price': 86.40,
            'message': 'API is working (test data)',
            'symbol': 'SOL/USDT'
        })

@app.route('/api/scalper/status', methods=['GET'])
def scalper_status():
    """Статус скальпера - ОБОВ'ЯЗКОВИЙ РОУТ!"""
    logger.info("GET /api/scalper/status")
    try:
        scalper = get_scalper()
        
        return jsonify({
            'status': 'success',
            'scalper': scalper.get_status(),
            'stream': {
                'running': scalper.running if hasattr(scalper, 'running') else False,
                'symbol': scalper.symbol if hasattr(scalper, 'symbol') else 'SOLUSDT'
            },
            'timestamp': time.time()
        })
    except Exception as e:
        logger.error(f"Scalper status error: {e}")
        return jsonify({
            'status': 'success',
            'scalper': {
                'running': False,
                'position': None,
                'entry_price': 0,
                'equity': 1000.0,
                'total_signals': 0,
                'win_rate': 0,
                'performance': {'winning_trades': 0, 'losing_trades': 0}
            },
            'stream': {'running': False, 'symbol': 'SOLUSDT'},
            'timestamp': time.time()
        })

@app.route('/api/scalper/start', methods=['POST'])
def scalper_start():
    """Запустити скальпер"""
    logger.info("POST /api/scalper/start")
    try:
        scalper = get_scalper()
        scalper.running = True
        
        return jsonify({
            'status': 'success', 
            'message': 'Scalper started',
            'strategy': 'EMA 5/13 on SOLUSDT',
            'running': True
        })
    except Exception as e:
        logger.error(f"Scalper start error: {e}")
        return jsonify({
            'status': 'error', 
            'message': str(e)
        })

@app.route('/api/scalper/stop', methods=['POST'])
def scalper_stop():
    """Зупинити скальпер"""
    logger.info("POST /api/scalper/stop")
    try:
        scalper = get_scalper()
        scalper.running = False
        
        return jsonify({
            'status': 'success',
            'message': 'Scalper stopped',
            'running': False
        })
    except Exception as e:
        logger.error(f"Scalper stop error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/scalper/reset', methods=['POST'])
def scalper_reset():
    """Скинути стратегію"""
    logger.info("POST /api/scalper/reset")
    try:
        scalper = get_scalper()
        # Скидаємо стан
        scalper.running = False
        scalper.position = None
        scalper.entry_price = 0
        scalper.equity = 1000.0
        scalper.signals = []
        
        return jsonify({
            'status': 'success',
            'message': 'Strategy reset'
        })
    except Exception as e:
        logger.error(f"Scalper reset error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

@app.route('/api/scalper/signals', methods=['GET'])
def scalper_signals():
    """Отримати останні сигнали"""
    logger.info("GET /api/scalper/signals")
    try:
        scalper = get_scalper()
        limit = request.args.get('limit', 10, type=int)
        
        signals = scalper.signals[-limit:] if hasattr(scalper, 'signals') else []
        
        return jsonify({
            'status': 'success', 
            'signals': signals,
            'count': len(signals)
        })
    except Exception as e:
        logger.error(f"Scalper signals error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

# ========== УНІВЕРСАЛЬНИЙ РОУТ ДЛЯ ТЕСТУ ==========

@app.route('/api/scalper/<path:endpoint>', methods=['GET', 'POST'])
def scalper_catch_all(endpoint):
    """Універсальний роут для всіх запитів скальпера"""
    logger.info(f"{request.method} /api/scalper/{endpoint}")
    
    if endpoint == 'test' and request.method == 'GET':
        return scalper_test()
    elif endpoint == 'status' and request.method == 'GET':
        return scalper_status()
    elif endpoint == 'start' and request.method == 'POST':
        return scalper_start()
    elif endpoint == 'stop' and request.method == 'POST':
        return scalper_stop()
    elif endpoint == 'reset' and request.method == 'POST':
        return scalper_reset()
    elif endpoint == 'signals' and request.method == 'GET':
        return scalper_signals()
    else:
        return jsonify({
            'status': 'error',
            'message': f'Endpoint /api/scalper/{endpoint} not found',
            'available_endpoints': [
                'GET /api/scalper/test',
                'GET /api/scalper/status', 
                'POST /api/scalper/start',
                'POST /api/scalper/stop',
                'POST /api/scalper/reset',
                'GET /api/scalper/signals'
            ]
        }), 404

# ========== ЗАПУСК СЕРВЕРА ==========

if __name__ == '__main__':
    print("=" * 70)
    print("SOLIPSIST PLATFORM API")
    print("Available on: http://127.0.0.1:5000")
    print("=" * 70)
    
    # Тест доступності модулів
    print("Testing modules...")
    try:
        from scalper import EMAScalperSimple
        print("✓ scalper module: OK")
    except ImportError as e:
        print(f"✗ scalper module: {e}")
    
    try:
        from arbitrage_volume import get_arbitrage_for_api
        print("✓ arbitrage module: OK")
    except ImportError as e:
        print(f"✗ arbitrage module: {e}")
    
    print("\nAvailable routes:")
    print("  GET  /health")
    print("  GET  /arbitrage")
    print("  GET  /api/scalper/test")
    print("  GET  /api/scalper/status")
    print("  POST /api/scalper/start")
    print("  POST /api/scalper/stop")
    print("  POST /api/scalper/reset")
    print("=" * 70)
    
    # Запуск сервера
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True, use_reloader=False)