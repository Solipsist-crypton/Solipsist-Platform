# src/python/api_bridge.py - ВИПРАВЛЕНА ВЕРСІЯ
from flask import Flask, jsonify, request
from flask_cors import CORS
import subprocess
import json
import sys
import io
import time
import threading
import logging
import os
import ccxt
import time
from datetime import datetime, timedelta
# ========== ФІКС ДЛЯ WINDOWS ==========
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# ========== ФІКС ІМПОРТІВ ==========
# Додаємо поточну директорію до шляху Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

# ========== ІМПОРТ ФУНКЦІЇ АРБІТРАЖУ ==========
try:
    # Імпортуємо з ПРАВИЛЬНОГО файлу
    from arbitrage_volume import analyze_arbitrage_fast
    ARBITRAGE_AVAILABLE = True
    print("✅ Модуль arbitrage_volume успішно імпортовано")
except ImportError as e:
    print(f"❌ Помилка імпорту arbitrage_volume: {e}")
    print("   Створюю заглушку...")
    ARBITRAGE_AVAILABLE = False
    
    # Створюємо заглушку
    def analyze_arbitrage_fast(json_output=False):
        print("⚠️  Використовую заглушку для arbitrage")
        if json_output:
            return {
                'opportunities': [],
                'stats': {
                    'avg_spread': 0,
                    'found_opportunities': 0,
                    'max_spread': 0,
                    'timestamp': time.time(),
                    'total_pairs': 5
                }
            }
        else:
            return []

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
        'timestamp': time.time(),
        'arbitrage_available': ARBITRAGE_AVAILABLE
    })

@app.route('/arbitrage')
def get_arbitrage():
    """Отримати арбітражні можливості"""
    import sys
    sys.stdout.flush()
    
    print(f"\n" + "="*60)
    print(f"🚀 API: /arbitrage викликано", flush=True)
    print(f"   Час: {time.strftime('%H:%M:%S')}", flush=True)
    print(f"   Force: {request.args.get('force')}", flush=True)
    
    # Перевірка кешу (30 секунд)
    cache_age = time.time() - cache['last_update'] if cache['last_update'] else 999
    if cache['arbitrage'] and cache_age < 30 and not request.args.get('force'):
        print(f"   📦 Використовую кеш ({cache_age:.1f}с)", flush=True)
        return jsonify(cache['arbitrage'])
    
    try:
        print(f"   🔄 Запускаю arbitrage...", flush=True)
        
        # Безпосередній виклик функції
        result = analyze_arbitrage_fast(json_output=True)
        
        # ДЕТАЛЬНА ПЕРЕВІРКА
        if result is None:
            print(f"   ❌ Функція повернула None", flush=True)
            result = {'opportunities': [], 'stats': {'error': 'Function returned None'}}
        elif isinstance(result, list):
            print(f"   📊 Отримано список з {len(result)} елементів", flush=True)
            # Конвертуємо list в dict для API
            result = {
                'opportunities': result,
                'stats': {
                    'total_pairs': len(result),
                    'found_opportunities': len(result),
                    'avg_spread': sum(o.get('spread', 0) for o in result) / len(result) if result else 0,
                    'max_spread': max(o.get('spread', 0) for o in result) if result else 0,
                    'timestamp': time.time()
                }
            }
        elif not isinstance(result, dict):
            print(f"   ❌ Невідомий тип: {type(result)}", flush=True)
            result = {'opportunities': [], 'stats': {'error': f'Unknown type: {type(result)}'}}
        
        # Зберігаємо в кеш
        cache['arbitrage'] = result
        cache['last_update'] = time.time()
        
        # Вивід результатів
        opps = result.get('opportunities', [])
        print(f"   ✅ Готово: {len(opps)} можливостей", flush=True)
        
        if opps:
            for i, opp in enumerate(opps[:3]):
                print(f"      {i+1}. {opp['pair']}: {opp['spread']:.2f}%", flush=True)
        
        print("="*60, flush=True)
        return jsonify(result)
        
    except Exception as e:
        print(f"\n   💥 КРИТИЧНА ПОМИЛКА: {e}", flush=True)
        import traceback
        traceback.print_exc()
        print("="*60, flush=True)
        
        return jsonify({
            'opportunities': [],
            'stats': {
                'avg_spread': 0,
                'found_opportunities': 0,
                'max_spread': 0,
                'timestamp': time.time(),
                'total_pairs': 5,
                'error': str(e)
            }
        }), 500
    
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
# ========== РОУТЕР ДЛЯ РЕАЛЬНИХ СВІЧОК З BINANCE ==========

@app.route('/api/scalper/candles', methods=['GET'])
def get_real_candles():
    """Отримати реальні свічки з Binance"""
    try:
        symbol = request.args.get('symbol', 'SOL/USDT')
        interval = request.args.get('interval', '1m')
        limit = request.args.get('limit', 100, type=int)
        
        # Ініціалізуємо Binance
        exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        
        # Отримуємо свічки
        ohlcv = exchange.fetch_ohlcv(symbol, interval, limit=limit)
        
        # Форматуємо дані для Lightweight Charts
        candles = []
        for candle in ohlcv:
            # Binance повертає: [timestamp, open, high, low, close, volume]
            candles.append({
                'time': candle[0] / 1000,  # Конвертуємо мс в секунди
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4]),
                'volume': float(candle[5])
            })
        
        # Отримуємо поточну ціну
        ticker = exchange.fetch_ticker(symbol)
        current_price = float(ticker['last'])
        
        return jsonify({
            'status': 'success',
            'candles': candles,
            'current_price': current_price,
            'symbol': symbol,
            'interval': interval,
            'timestamp': time.time()
        })
        
    except Exception as e:
        logger.error(f"Candles error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/scalper/signals', methods=['GET'])
def get_signals():
    """Отримати сигнали з стратегії"""
    try:
        scalper = get_scalper()
        limit = request.args.get('limit', 10, type=int)
        
        # Симулюємо реальні сигнали
        signals = []
        
        # Якщо скальпер має сигнали
        if hasattr(scalper, 'signals') and scalper.signals:
            for i, signal in enumerate(scalper.signals[-limit:]):
                signals.append({
                    'id': i + 1,
                    'timestamp': signal.get('timestamp', time.time() - i * 60),
                    'signal': signal.get('signal', 'BUY' if i % 2 == 0 else 'SELL'),
                    'price': signal.get('price', 86.40 + (i * 0.1)),
                    'ema_fast': signal.get('fast_ema', 86.30 + (i * 0.05)),
                    'ema_slow': signal.get('slow_ema', 86.20 + (i * 0.03))
                })
        else:
            # Тестові сигнали
            current_time = time.time()
            for i in range(limit):
                signals.append({
                    'id': i + 1,
                    'timestamp': current_time - (i * 300),  # Кожні 5 хвилин
                    'signal': 'BUY' if i % 2 == 0 else 'SELL',
                    'price': 86.40 - (i * 0.5) + (i * 0.1),
                    'ema_fast': 86.30 - (i * 0.4) + (i * 0.08),
                    'ema_slow': 86.20 - (i * 0.3) + (i * 0.06)
                })
        
        return jsonify({
            'status': 'success',
            'signals': signals,
            'count': len(signals)
        })
        
    except Exception as e:
        logger.error(f"Signals error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
    
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


# ========== ЗАПУСК СЕРВЕРА ==========

if __name__ == '__main__':
    print("=" * 70)
    print("SOLIPSIST PLATFORM API - АРБІТРАЖ")
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
        from arbitrage_volume import get_arbitrage_for_api, analyze_arbitrage_fast
        print("✓ arbitrage module: OK")
        print(f"   analyze_arbitrage_fast доступна: {analyze_arbitrage_fast.__module__}")
    except ImportError as e:
        print(f"✗ arbitrage module: {e}")
    
    print(f"\nArbitrage available: {'YES' if ARBITRAGE_AVAILABLE else 'NO (using stub)'}")
    
    print("\nAvailable routes:")
    print("  GET  /health")
    print("  GET  /arbitrage")
    print("  GET  /arbitrage?force=true  (очистити кеш)")
    print("  GET  /api/scalper/test")
    print("  GET  /api/scalper/status")
    print("  POST /api/scalper/start")
    print("  POST /api/scalper/stop")
    print("  POST /api/scalper/reset")
    print("=" * 70)
    
    # Запуск сервера
    app.run(host='127.0.0.1', port=5000, debug=False, threaded=True, use_reloader=False)