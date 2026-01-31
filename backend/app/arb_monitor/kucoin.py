import requests

def get_prices(symbols):
    """Отримати ціни з KuCoin"""
    url = "https://api.kucoin.com/api/v1/market/allTickers"
    response = requests.get(url).json()
    
    prices = {}
    for item in response['data']['ticker']:
        symbol = item['symbol'].replace("-", "")
        if symbol in symbols:
            prices[symbol] = float(item['last'])
    
    return prices