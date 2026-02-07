# src/python/market_data.py
import ccxt
import time
import threading
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BinanceDataStream:
    """Потокове отримання даних з Binance"""
    
    def __init__(self, symbol="SOL/USDT", timeframe="1m"):
        self.symbol = symbol
        self.timeframe = timeframe
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.is_running = False
        self.thread = None
        self.callbacks = []
        self.last_price = None
        self.candles_cache = []
        
    def add_callback(self, callback):
        """Додати callback для отримання даних"""
        self.callbacks.append(callback)
        
    def get_historical_candles(self, limit=100):
        """Отримати історичні свічки"""
        try:
            candles = self.exchange.fetch_ohlcv(
                self.symbol, 
                self.timeframe, 
                limit=limit
            )
            
            formatted_candles = []
            for candle in candles:
                formatted_candles.append({
                    'timestamp': candle[0],
                    'time': candle[0] / 1000,  # Конвертуємо до секунд
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                })
            
            self.candles_cache = formatted_candles
            logger.info(f"Отримано {len(formatted_candles)} історичних свічок для {self.symbol}")
            return formatted_candles
            
        except Exception as e:
            logger.error(f"Помилка отримання історичних даних: {e}")
            return []
    
    def _stream_loop(self):
        """Основний цикл стримінгу"""
        while self.is_running:
            try:
                # Отримуємо поточну ціну
                ticker = self.exchange.fetch_ticker(self.symbol)
                current_price = ticker['last']
                
                if self.last_price != current_price:
                    self.last_price = current_price
                    
                    # Створюємо дані для відправки
                    data = {
                        'type': 'price_update',
                        'symbol': self.symbol,
                        'price': current_price,
                        'timestamp': datetime.now().isoformat(),
                        'volume': ticker['baseVolume'],
                        'change': ticker['percentage']
                    }
                    
                    # Відправляємо всім підписникам
                    for callback in self.callbacks:
                        try:
                            callback(data)
                        except Exception as e:
                            logger.error(f"Помилка в callback: {e}")
                
                # Затримка перед наступним оновленням
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Помилка в стримінгу: {e}")
                time.sleep(10)
    
    def start(self):
        """Запустити стримінг"""
        if not self.is_running:
            self.is_running = True
            self.thread = threading.Thread(target=self._stream_loop, daemon=True)
            self.thread.start()
            logger.info(f"Стримінг даних запущено для {self.symbol}")
    
    def stop(self):
        """Зупинити стримінг"""
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=2)
        logger.info(f"Стримінг даних зупинено для {self.symbol}")
    
    def get_status(self):
        """Отримати статус"""
        return {
            'running': self.is_running,
            'symbol': self.symbol,
            'last_price': self.last_price,
            'callbacks_count': len(self.callbacks)
        }