import requests

# 1. BINANCE
def get_binance_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
        data = requests.get(url, timeout=3).json()
        return float(data['price'])
    except:
        return None

def get_binance_all():
    try:
        url = "https://api.binance.com/api/v3/ticker/price"
        data = requests.get(url, timeout=3).json()
        return {item['symbol']: float(item['price']) for item in data}
    except:
        return {}

# 2. BYBIT  
def get_bybit_price(symbol):
    try:
        # Конвертуємо BTCUSDT → BTCUSD для Bybit
        symbol_fixed = symbol.replace('USDT', 'USD')
        url = f"https://api.bybit.com/v2/public/tickers?symbol={symbol_fixed}"
        data = requests.get(url, timeout=3).json()
        return float(data['result'][0]['last_price'])
    except:
        return None

def get_bybit_all():
    try:
        url = "https://api.bybit.com/v5/market/tickers?category=spot"
        data = requests.get(url, timeout=3).json()
        return {item['symbol']: float(item['lastPrice']) for item in data['result']['list']}
    except:
        return {}

# 3. KUCOIN
def get_kucoin_price(symbol):
    try:
        # Конвертуємо BTCUSDT → BTC-USDT для KuCoin
        symbol_fixed = symbol.replace('USDT', '-USDT')
        url = f"https://api.kucoin.com/api/v1/market/orderbook/level1?symbol={symbol_fixed}"
        data = requests.get(url, timeout=3).json()
        return float(data['data']['price'])
    except:
        return None

def get_kucoin_all():
    try:
        url = "https://api.kucoin.com/api/v1/market/allTickers"
        data = requests.get(url, timeout=3).json()
        return {item['symbol'].replace('-', ''): float(item['last']) 
                for item in data['data']['ticker']}
    except:
        return {}