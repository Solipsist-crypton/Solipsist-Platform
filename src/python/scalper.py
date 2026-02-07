# src/python/scalper.py - СПРОЩЕНА ВЕРСІЯ
import time
import json
import logging
import requests
from datetime import datetime
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        self.equity = 1000
        self.trades = []
        self.signals = []
        
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
                return False
            
            # Розрахунок EMA
            fast_ema = self.calculate_ema(list(self.prices)[-self.fast_period*2:], self.fast_period)
            slow_ema = self.calculate_ema(list(self.prices)[-self.slow_period*2:], self.slow_period)
            
            if fast_ema is None or slow_ema is None:
                return False
            
            # Визначення сигналів
            signal = None
            
            if fast_ema > slow_ema:
                if self.position == 'SHORT' or self.position is None:
                    signal = 'BUY'
            elif fast_ema < slow_ema:
                if self.position == 'LONG' or self.position is None:
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
    
    def get_status(self):
        """Отримати статус"""
        return {
            'running': True,
            'position': self.position,
            'entry_price': self.entry_price,
            'equity': round(self.equity, 2),
            'total_signals': len(self.signals),
            'total_trades': len(self.trades),
            'win_rate': 50,  # Просте значення
            'performance': {
                'winning_trades': len(self.trades) // 2,
                'losing_trades': len(self.trades) // 2
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
        self.position = None
        self.entry_price = 0
        self.equity = 1000
        self.trades = []
        self.signals = []
        self.prices.clear()
        self.closes.clear()
        logger.info("Стратегію скинуто")

# Глобальний екземпляр
scalper_instance = EMAScalperSimple()

def init_scalper():
    """Ініціалізація"""
    return scalper_instance