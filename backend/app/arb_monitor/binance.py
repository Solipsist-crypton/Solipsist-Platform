import requests

def get_prices(symbols):
    """Отримати ціни з Binance"""
    url = "https://api.binance.com/api/v3/ticker/price"
    response = requests.get(url).json()
    
    prices = {}
    for item in response:
        if item['symbol'] in symbols:
            prices[item['symbol']] = float(item['price'])
    
    return prices