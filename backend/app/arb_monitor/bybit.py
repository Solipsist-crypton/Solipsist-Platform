import requests

def get_prices(symbols):
    """Отримати ціни з Bybit"""
    url = "https://api.bybit.com/v2/public/tickers"
    response = requests.get(url).json()
    
    prices = {}
    for item in response['result']:
        symbol = item['symbol'].replace("USD", "USDT")
        if symbol in symbols:
            prices[symbol] = float(item['last_price'])
    
    return prices