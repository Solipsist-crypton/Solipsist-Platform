import requests
import time

# ==================== ФУНКЦІЇ БЕЗ ОБ'ЄМІВ (ШВИДКІ) ====================

def get_all_binance_fast():
    """Всі пари Binance (швидко, тільки ціни)"""
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        data = requests.get(url, timeout=10).json()
        return {item['symbol']: float(item['price']) for item in data}
    except:
        return {}

def get_all_bybit_fast():
    """Всі пари Bybit (швидко)"""
    try:
        url = "https://api.bybit.com/v5/market/tickers?category=spot"
        data = requests.get(url, timeout=10).json()
        return {item['symbol']: float(item['lastPrice']) 
                for item in data['result']['list']}
    except:
        return {}

def get_all_mexc_fast():
    """Всі пари MEXC (швидко)"""
    try:
        url = "https://api.mexc.com/api/v3/ticker/price"
        data = requests.get(url, timeout=10).json()
        return {item['symbol']: float(item['price']) for item in data}
    except:
        return {}

def get_all_gateio_fast():
    """Всі пари Gate.io (швидко)"""
    try:
        url = "https://api.gateio.ws/api/v4/spot/tickers"
        data = requests.get(url, timeout=10).json()
        return {item['currency_pair']: float(item['last']) for item in data}
    except:
        return {}

def get_all_htx_fast():
    """Всі пари HTX (швидко)"""
    try:
        url = "https://api.huobi.pro/market/tickers"
        data = requests.get(url, timeout=10).json()
        return {item['symbol'].upper(): float(item['close']) 
                for item in data['data']}
    except:
        return {}

# ==================== ФУНКЦІЇ З ОБ'ЄМАМИ ====================

def get_all_binance_with_volume():
    """Всі пари Binance з об'ємами"""
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        data = requests.get(url, timeout=10).json()
        
        result = {}
        for item in data:
            result[item['symbol']] = {
                'price': float(item['lastPrice']),
                'volume': float(item['volume']),  # USDT об'єм
                'quoteVolume': float(item['quoteVolume'])
            }
        return result
    except:
        return {}

def get_all_bybit_with_volume():
    """Всі пари Bybit з об'ємами"""
    try:
        url = "https://api.bybit.com/v5/market/tickers?category=spot"
        data = requests.get(url, timeout=10).json()
        
        result = {}
        for item in data['result']['list']:
            result[item['symbol']] = {
                'price': float(item['lastPrice']),
                'volume24h': float(item['volume24h']),
                'turnover24h': float(item['turnover24h'])
            }
        return result
    except:
        return {}

def get_all_mexc_with_volume():
    """Всі пари MEXC з об'ємами"""
    try:
        url = "https://api.mexc.com/api/v3/ticker/24hr"
        data = requests.get(url, timeout=10).json()
        
        result = {}
        for item in data:
            result[item['symbol']] = {
                'price': float(item['lastPrice']),
                'volume': float(item['volume']),
                'quoteVolume': float(item['quoteVolume'])
            }
        return result
    except:
        return {}

def get_all_gateio_with_volume():
    """Всі пари Gate.io з об'ємами"""
    try:
        url = "https://api.gateio.ws/api/v4/spot/tickers"
        data = requests.get(url, timeout=10).json()
        
        result = {}
        for item in data:
            symbol = item['currency_pair']
            result[symbol] = {
                'price': float(item['last']),
                'base_volume': float(item['base_volume']),
                'quote_volume': float(item['quote_volume'])  # USDT об'єм
            }
        return result
    except:
        return {}

def get_all_htx_with_volume():
    """Всі пари HTX з об'ємами"""
    try:
        url = "https://api.huobi.pro/market/tickers"
        data = requests.get(url, timeout=10).json()
        
        result = {}
        for item in data['data']:
            symbol = item['symbol'].upper()
            result[symbol] = {
                'price': float(item['close']),
                'amount': float(item['amount']),
                'vol': float(item['vol'])  # USDT об'єм
            }
        return result
    except:
        return {}

# ==================== СЛОВНИКИ ====================

# Тільки 5 працюючих бірж (ШВИДКІ версії - без об'ємів)
ALL_EXCHANGES_FAST = {
    'Binance': get_all_binance_fast,
    'Bybit': get_all_bybit_fast,
    'MEXC': get_all_mexc_fast,
    'Gate.io': get_all_gateio_fast,
    'HTX': get_all_htx_fast,
}

# З об'ємами (повільніше)
ALL_EXCHANGES_VOLUME = {
    'Binance': get_all_binance_with_volume,
    'Bybit': get_all_bybit_with_volume,
    'MEXC': get_all_mexc_with_volume,
    'Gate.io': get_all_gateio_with_volume,
    'HTX': get_all_htx_with_volume,
}

# По замовчуванню використовуємо швидкі
ALL_EXCHANGES = ALL_EXCHANGES_FAST