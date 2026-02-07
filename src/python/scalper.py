# src/python/scalper.py - ТІЛЬКИ КЛАСИ (без Flask)

import time
import json
import logging
import requests
import threading
from datetime import datetime
from collections import deque

# Налаштування логування
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ========== КЛАС КЛІЄНТА BINANCE ==========
class SimpleBinanceClient:
    """Простий клієнт для Binance API"""
    
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
    
    def get_current_price(self, symbol="SOLUSDT"):
        """Отримати поточну ціну"""
        try:
            url = f"{self.base_url}/ticker/price"
            response = requests.get(url, params={"symbol": symbol}, timeout=5)
            data = response.json()
            return float(data['price'])
        except Exception as e:
            logger.error(f"Помилка отримання ціни: {e}")
            return None
    
    def get_historical_klines(self, symbol="SOLUSDT", interval="1m", limit=100):
        """Отримати історичні свічки"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                "symbol": symbol,
                "interval": interval,
                "limit": limit
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            candles = []
            for kline in data:
                candles.append({
                    'timestamp': kline[0],
                    'time': kline[0] / 1000,
                    'open': float(kline[1]),
                    'high': float(kline[2]),
                    'low': float(kline[3]),
                    'close': float(kline[4]),
                    'volume': float(kline[5])
                })
            
            logger.info(f"Отримано {len(candles)} свічок для {symbol}")
            return candles
            
        except Exception as e:
            logger.error(f"Помилка історичних даних: {e}")
            return []

# ========== КЛАС СТРАТЕГІЇ ==========
class EMAScalperSimple:
    """Спрощена стратегія скальпінга"""
    
    def __init__(self):
        self.client = SimpleBinanceClient()
        self.symbol = "SOLUSDT"
        
        # Історія цін
        self.prices = deque(maxlen=50)
        self.closes = deque(maxlen=50)
        
        # Стан стратегії
        self.position = None  # 'LONG', 'SHORT', або None
        self.entry_price = 0
        self.equity = 1000.0
        self.trades = []
        self.signals = []
        self.running = False
        self.stream_thread = None
        
        # Налаштування (з TradingView)
        self.fast_period = 5
        self.slow_period = 13
        self.atr_filter = False
        
        logger.info("Скальпер ініціалізовано (проста версія)")
    
    def calculate_ema(self, prices, period):
        """Розрахунок EMA"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price - ema) * multiplier + ema
        
        return ema
    
    def update_price(self):
        """Оновити ціну та перевірити сигнали"""
        try:
            price = self.client.get_current_price(self.symbol)
            if price is None:
                return False
            
            self.prices.append(price)
            self.closes.append(price)
            
            # Перевіряємо, чи достатньо даних
            if len(self.prices) < self.slow_period * 2:
                logger.debug(f"Недостатньо даних: {len(self.prices)}/{self.slow_period*2}")
                return False
            
            # Розрахунок EMA
            recent_prices = list(self.prices)
            fast_ema = self.calculate_ema(recent_prices[-self.fast_period*2:], self.fast_period)
            slow_ema = self.calculate_ema(recent_prices[-self.slow_period*2:], self.slow_period)
            
            if fast_ema is None or slow_ema is None:
                return False
            
            # Визначення сигналів
            signal = None
            
            if fast_ema > slow_ema and (self.position is None or self.position == 'SHORT'):
                signal = 'BUY'
            elif fast_ema < slow_ema and (self.position is None or self.position == 'LONG'):
                signal = 'SELL'
            
            # Обробка сигналу
            if signal:
                self.process_signal(signal, price, fast_ema, slow_ema)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Помилка оновлення: {e}")
            return False
    
    def process_signal(self, signal, price, fast_ema, slow_ema):
        """Обробка сигналу"""
        # Закриваємо попередню позицію
        if self.position:
            self.close_position(price)
        
        # Відкриваємо нову
        self.open_position(signal, price)
        
        # Записуємо сигнал
        signal_data = {
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'price': price,
            'fast_ema': fast_ema,
            'slow_ema': slow_ema,
            'position': self.position
        }
        
        self.signals.append(signal_data)
        logger.info(f"Сигнал {signal} по {price:.4f} | EMA: {fast_ema:.4f}/{slow_ema:.4f}")
        
        # Записуємо торгівлю
        trade_data = {
            'timestamp': datetime.now().isoformat(),
            'signal': signal,
            'entry_price': price,
            'position': self.position,
            'equity': self.equity
        }
        
        self.trades.append(trade_data)
    
    def open_position(self, side, price):
        """Відкрити позицію"""
        self.position = 'LONG' if side == 'BUY' else 'SHORT'
        self.entry_price = price
        logger.info(f"Відкрита позиція {self.position} по {price:.4f}")
    
    def close_position(self, exit_price):
        """Закрити позицію"""
        if not self.position or self.entry_price == 0:
            return
        
        # Розрахунок PnL
        if self.position == 'LONG':
            pnl = (exit_price - self.entry_price) * (self.equity / self.entry_price)
        else:  # SHORT
            pnl = (self.entry_price - exit_price) * (self.equity / self.entry_price)
        
        # Оновлюємо баланс
        self.equity += pnl
        
        logger.info(f"Закрита позиція {self.position}: {pnl:+.2f}")
        self.position = None
        self.entry_price = 0
    
    def start_stream(self):
        """Запустити потік даних"""
        if self.running:
            return True
        
        self.running = True
        
        def stream_loop():
            logger.info("Запуск потоку даних...")
            while self.running:
                try:
                    if self.update_price():
                        logger.debug("Оновлення ціни успішне")
                    time.sleep(2)  # Оновлюємо кожні 2 секунди
                except Exception as e:
                    logger.error(f"Помилка в потоці: {e}")
                    time.sleep(5)
        
        self.stream_thread = threading.Thread(target=stream_loop, daemon=True)
        self.stream_thread.start()
        return True
    
    def stop_stream(self):
        """Зупинити потік даних"""
        self.running = False
        if self.stream_thread:
            self.stream_thread.join(timeout=5)
        logger.info("Потік даних зупинено")
    
    def get_status(self):
        """Отримати статус"""
        winning = sum(1 for trade in self.trades if 'profit' in trade and trade['profit'] > 0)
        losing = len(self.trades) - winning
        win_rate = (winning / len(self.trades) * 100) if self.trades else 0
        
        return {
            'running': self.running,
            'position': self.position,
            'entry_price': self.entry_price,
            'equity': round(self.equity, 2),
            'total_signals': len(self.signals),
            'total_trades': len(self.trades),
            'win_rate': round(win_rate, 1),
            'performance': {
                'winning_trades': winning,
                'losing_trades': losing
            }
        }
    
    def get_history(self, limit=20):
        """Отримати останні сигнали"""
        return list(self.signals)[-limit:] if self.signals else []
    
    def get_candles(self, limit=100):
        """Отримати свічки"""
        return self.client.get_historical_klines(self.symbol, "1m", limit)
    
    def reset(self):
        """Скинути стратегію"""
        self.stop_stream()
        self.position = None
        self.entry_price = 0
        self.equity = 1000.0
        self.trades = []
        self.signals = []
        self.prices.clear()
        self.closes.clear()
        logger.info("Стратегію скинуто")

# Глобальний екземпляр для імпорту
# Цей екземпляр буде використовуватися в api_bridge.py
_scalper_instance = None

def get_scalper_instance():
    """Отримати глобальний екземпляр скальпера"""
    global _scalper_instance
    if _scalper_instance is None:
        _scalper_instance = EMAScalperSimple()
        print("✅ Глобальний скальпер створено")
    return _scalper_instance

# ========== ТЕСТОВИЙ ЗАПУСК (якщо запускати окремо) ==========
if __name__ == '__main__':
    print("=" * 50)
    print("🧪 Тестування класу скальпера")
    print("=" * 50)
    
    scalper = EMAScalperSimple()
    
    # Тест отримання ціни
    price = scalper.client.get_current_price()
    print(f"💰 Поточна ціна SOL: {price:.4f} USDT" if price else "❌ Не вдалося отримати ціну")
    
    # Тест отримання свічок
    candles = scalper.get_candles(limit=5)
    print(f"📊 Отримано {len(candles)} свічок")
    
    print("✅ Тестування завершено. Клас готовий до використання.")
    print("ℹ️ Запускайте через api_bridge.py для повної функціональності")