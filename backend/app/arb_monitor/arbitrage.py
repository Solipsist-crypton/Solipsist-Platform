import time
import requests
from concurrent.futures import ThreadPoolExecutor

# Завантажуємо пари з файлу
def load_3plus_pairs(limit=100):
    """Завантажити пари на 3+ біржах"""
    try:
        with open("pairs_3plus_of_5.txt", "r") as f:
            pairs = [line.strip() for line in f 
                    if line.strip() and not line.startswith('#')]
        print(f"📊 Завантажено {len(pairs)} пар з pairs_3plus_of_5.txt")
        return pairs[:limit]
    except:
        print("❌ Файл pairs_3plus_of_5.txt не знайдено!")
        return ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']

# Біржі
EXCHANGES = ['Binance', 'Bybit', 'MEXC', 'Gate.io', 'HTX']

def get_price_volume(exchange, pair):
    """Отримати ціну та об'єм з однієї біржі"""
    try:
        if exchange == 'Binance':
            url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={pair}"
            data = requests.get(url, timeout=5).json()
            return {
                'price': float(data['lastPrice']),
                'volume': float(data['volume']),
                'bid': float(data['bidPrice']),
                'ask': float(data['askPrice'])
            }
        
        elif exchange == 'Bybit':
            url = f"https://api.bybit.com/v5/market/tickers?category=spot&symbol={pair}"
            data = requests.get(url, timeout=5).json()
            item = data['result']['list'][0]
            return {
                'price': float(item['lastPrice']),
                'volume': float(item['volume24h']),
                'bid': float(item['bid1Price']),
                'ask': float(item['ask1Price'])
            }
        
        elif exchange == 'MEXC':
            url = f"https://api.mexc.com/api/v3/ticker/24hr?symbol={pair}"
            data = requests.get(url, timeout=5).json()
            return {
                'price': float(data['lastPrice']),
                'volume': float(data['volume']),
                'bid': float(data['bidPrice']),
                'ask': float(data['askPrice'])
            }
        
        elif exchange == 'Gate.io':
            gate_pair = pair.replace('USDT', '_USDT')
            url = f"https://api.gateio.ws/api/v4/spot/tickers?currency_pair={gate_pair}"
            data = requests.get(url, timeout=5).json()
            if data:
                return {
                    'price': float(data[0]['last']),
                    'volume': float(data[0]['quote_volume']),
                    'bid': float(data[0]['highest_bid']),
                    'ask': float(data[0]['lowest_ask'])
                }
        
        elif exchange == 'HTX':
            htx_pair = pair.lower()
            url = f"https://api.huobi.pro/market/detail/merged?symbol={htx_pair}"
            data = requests.get(url, timeout=5).json()
            tick = data['tick']
            return {
                'price': float(tick['close']),
                'volume': float(tick['amount']),
                'bid': float(tick['bid'][0]),
                'ask': float(tick['ask'][0])
            }
    
    except:
        return None
    
    return None

def analyze_pair_arbitrage(pair):
    """Аналіз арбітражу для однієї пари"""
    # Отримуємо дані з усіх бірж паралельно
    pair_data = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for exchange in EXCHANGES:
            future = executor.submit(get_price_volume, exchange, pair)
            futures[future] = exchange
        
        for future in futures:
            exchange = futures[future]
            try:
                data = future.result(timeout=5)
                if data and data['volume'] > 0:
                    pair_data[exchange] = data
            except:
                pass
    
    # Перевіряємо чи є мінімум 3 біржі
    if len(pair_data) >= 3:
        # Знаходимо найнижчу ask (де купити) та найвищу bid (де продати)
        buy_exchange = min(pair_data, key=lambda x: pair_data[x]['ask'])
        sell_exchange = max(pair_data, key=lambda x: pair_data[x]['bid'])
        
        buy_price = pair_data[buy_exchange]['ask']
        sell_price = pair_data[sell_exchange]['bid']
        
        # Розраховуємо спред (без комісій)
        spread = ((sell_price - buy_price) / buy_price) * 100
        
        # Перевіряємо об'єми
        buy_volume = pair_data[buy_exchange]['volume']
        sell_volume = pair_data[sell_exchange]['volume']
        
        if spread > 0.05 and buy_volume > 100000 and sell_volume > 100000:
            return {
                'pair': pair,
                'spread': spread,
                'buy_exchange': buy_exchange,
                'sell_exchange': sell_exchange,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'buy_volume': buy_volume,
                'sell_volume': sell_volume,
                'exchanges': len(pair_data)
            }
    
    return None

def main():
    print("🎯 АРБІТРАЖНИЙ АНАЛІЗ (3+ БІРЖІ, З ОБ'ЄМАМИ)")
    print("=" * 60)
    
    # Завантажуємо пари
    pairs = load_3plus_pairs(limit=50)  # Перевіряємо перші 50
    
    print(f"🔍 Аналіз {len(pairs)} пар...")
    
    # Аналізуємо паралельно
    opportunities = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(analyze_pair_arbitrage, pair): pair for pair in pairs}
        
        for future in futures:
            pair = futures[future]
            try:
                result = future.result(timeout=10)
                if result:
                    opportunities.append(result)
            except:
                pass
    
    elapsed = time.time() - start_time
    
    # Сортуємо за спредом
    opportunities.sort(key=lambda x: x['spread'], reverse=True)
    
    # Результати
    print(f"\n✅ Аналіз завершено за {elapsed:.1f} сек")
    
    if opportunities:
        print(f"\n💎 ЗНАЙДЕНО {len(opportunities)} АРБІТРАЖІВ (>0.05%):")
        print("=" * 90)
        print(f"{'ПАРА':<10} {'СПРЕД':<8} {'КУПИТИ':<12} {'ПРОДАВ.':<12} {'ЦІНА':<20} {'ОБЄМ':<15}")
        print("-" * 90)
        
        for opp in opportunities:
            # Форматування ціни
            if opp['buy_price'] < 0.01:
                price_str = f"${opp['buy_price']:.8f}→${opp['sell_price']:.8f}"
            elif opp['buy_price'] < 1:
                price_str = f"${opp['buy_price']:.6f}→${opp['sell_price']:.6f}"
            else:
                price_str = f"${opp['buy_price']:.4f}→${opp['sell_price']:.4f}"
            
            # Форматування об'єму
            volume_str = f"${opp['buy_volume']/1000000:.1f}M→${opp['sell_volume']/1000000:.1f}M"
            
            print(f"{opp['pair']:<10} {opp['spread']:>6.2f}% "
                  f"{opp['buy_exchange']:<12} {opp['sell_exchange']:<12} "
                  f"{price_str:<20} {volume_str:<15}")
    else:
        print("\n⚠️  АРБІТРАЖНИХ МОЖЛИВОСТЕЙ НЕ ЗНАЙДЕНО")
    
    # Статистика
    print(f"\n📊 СТАТИСТИКА:")
    print(f"• Аналізовано пар: {len(pairs)}")
    print(f"• Знайдено арбітражів: {len(opportunities)}")
    print(f"• Мінімальний об'єм: $100K")
    
    if opportunities:
        avg_spread = sum(o['spread'] for o in opportunities) / len(opportunities)
        print(f"• Середній спред: {avg_spread:.3f}%")
        print(f"• Максимальний спред: {opportunities[0]['spread']:.3f}%")

if __name__ == "__main__":
    main()