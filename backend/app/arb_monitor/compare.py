import binance, bybit

def compare_prices(symbols=['BTCUSDT', 'ETHUSDT', 'SOLUSDT']):
    """Порівняти ціни на біржах"""
    
    # Отримати ціни з кожного exchange
    binance_prices = binance.get_prices(symbols)
    bybit_prices = bybit.get_prices(symbols)
    
    results = {}
    
    for symbol in symbols:
        price_binance = binance_prices.get(symbol)
        price_bybit = bybit_prices.get(symbol)
        
        if price_binance and price_bybit:
            diff = price_binance - price_bybit
            diff_percent = (diff / price_binance) * 100
            
            results[symbol] = {
                'binance': price_binance,
                'bybit': price_bybit,
                'difference': diff,
                'diff_percent': diff_percent,
                'cheaper': 'Binance' if price_binance < price_bybit else 'Bybit'
            }
    
    return results

def find_arbitrage(results, threshold=0.1):
    """Знайти арбітражні можливості"""
    opportunities = []
    
    for symbol, data in results.items():
        if abs(data['diff_percent']) > threshold:
            opportunities.append({
                'symbol': symbol,
                'buy_at': 'Binance' if data['binance'] < data['bybit'] else 'Bybit',
                'sell_at': 'Bybit' if data['binance'] < data['bybit'] else 'Binance',
                'profit_percent': abs(data['diff_percent']),
                'buy_price': min(data['binance'], data['bybit']),
                'sell_price': max(data['binance'], data['bybit'])
            })
    
    return opportunities