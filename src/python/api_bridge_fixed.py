# src/python/api_bridge_fixed.py - ВЕРСІЯ БЕЗ ЕМОДЗІ
from flask import Flask, jsonify, request
from flask_cors import CORS
import sys
import os
import time
import logging

# === ВАЖЛИВО ДЛЯ WINDOWS ===
# Налаштування кодування для Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Налаштування шляхів
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, current_dir)
sys.path.insert(0, parent_dir)

# БЕЗ ЕМОДЗІ - використовуйте прості символи
print("=" * 80)
print("API Bridge для Electron")
print(f"Current dir: {current_dir}")
print(f"Parent dir: {parent_dir}")
print("=" * 80)

app = Flask(__name__)
CORS(app)

# Налаштування логування
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# ========== СПРОЩЕНІ ІМПОРТИ ==========

try:
    from arbitrage_volume import get_arbitrage_for_api
    ARBITRAGE_AVAILABLE = True
    logger.info("Arbitrage module loaded")
except ImportError as e:
    ARBITRAGE_AVAILABLE = False
    logger.warning(f"Arbitrage module not available: {e}")
    get_arbitrage_for_api = lambda: {'opportunities': [], 'stats': {}}

# ========== ПРОСТИЙ СКАЛЬПЕР ==========

class SimpleScalper:
    def __init__(self):
        self.running = False
        self.position = None
        self.entry_price = 0
        self.equity = 1000.0
        self.signals = []
        self.symbol = "SOLUSDT"
        self.total_signals = 0
        
        # Спроба імпортувати реальний скальпер
        try:
            from scalper import EMAScalperSimple
            self.real_scalper = EMAScalperSimple()
            self.has_real_scalper = True
            logger.info("Real scalper loaded")
        except ImportError as e:
            self.real_scalper = None
            self.has_real_scalper = False
            logger.warning(f"Real scalper not available: {e}")
    
    def get_status(self):
        if self.has_real_scalper and self.real_scalper:
            status = self.real_scalper.get_status()
            status['running'] = self.running
            return status
        
        return {
            'running': self.running,
            'position': self.position,
            'entry_price': self.entry_price,
            'equity': self.equity,
            'total_signals': self.total_signals,
            'win_rate': 0,
            'performance': {'winning_trades': 0, 'losing_trades': 0}
        }

# Глобальний екземпляр
scalper = SimpleScalper()

# ========== РОУТИ ==========

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'Solipsist Platform',
        'timestamp': time.time(),
        'modules': {
            'arbitrage': ARBITRAGE_AVAILABLE,
            'scalper': True
        }
    })

@app.route('/arbitrage', methods=['GET'])
def get_arbitrage():
    try:
        result = get_arbitrage_for_api()
        return jsonify(result)
    except Exception as e:
        logger.error(f"Arbitrage error: {e}")
        return jsonify({
            'opportunities': [],
            'stats': {'max_spread': 0, 'avg_spread': 0},
            'error': str(e)[:100]
        })

# ========== РОУТИ СКАЛЬПЕРА ==========

@app.route('/api/scalper/test', methods=['GET'])
def scalper_test():
    return jsonify({
        'status': 'success',
        'price': 86.24,
        'message': 'Scalper API is working',
        'symbol': 'SOL/USDT',
        'timestamp': time.time()
    })

@app.route('/api/scalper/status', methods=['GET'])
def scalper_status():
    return jsonify({
        'status': 'success',
        'scalper': scalper.get_status(),
        'stream': {'running': scalper.running, 'symbol': scalper.symbol},
        'timestamp': time.time()
    })

@app.route('/api/scalper/start', methods=['POST'])
def scalper_start():
    scalper.running = True
    return jsonify({
        'status': 'success',
        'message': 'Scalper started',
        'running': True,
        'strategy': 'EMA 5/13'
    })

@app.route('/api/scalper/stop', methods=['POST'])
def scalper_stop():
    scalper.running = False
    return jsonify({
        'status': 'success',
        'message': 'Scalper stopped',
        'running': False
    })

@app.route('/api/scalper/reset', methods=['POST'])
def scalper_reset():
    scalper.__init__()
    return jsonify({
        'status': 'success',
        'message': 'Strategy reset'
    })

@app.route('/api/scalper/signals', methods=['GET'])
def scalper_signals():
    limit = request.args.get('limit', 10, type=int)
    return jsonify({
        'status': 'success',
        'signals': scalper.signals[-limit:] if scalper.signals else [],
        'count': len(scalper.signals)
    })

# ========== ЗАПУСК ==========

if __name__ == '__main__':
    print("=" * 80)
    print("Solipsist Platform API - Electron version")
    print("Running on http://127.0.0.1:5000")
    print("=" * 80)
    
    print("Available routes:")
    print("  GET  /health")
    print("  GET  /arbitrage")
    print("  GET  /api/scalper/test")
    print("  GET  /api/scalper/status")
    print("  POST /api/scalper/start")
    print("  POST /api/scalper/stop")
    print("=" * 80)
    
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, threaded=True, use_reloader=False)
    except Exception as e:
        print(f"Error starting server: {e}")
        input("Press Enter to exit...")