import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from exchanges_all import ALL_EXCHANGES_VOLUME

def get_all_data_with_volumes():
    """Отримати всі дані з об'ємами"""
    print("📊 ОТРИМАННЯ ДАНИХ З ОБ'ЄМАМИ")
    
    start = time.time()
    results = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(func): name for name, func in ALL_EXCHANGES_VOLUME.items()}
        
        for future in futures:
            exchange = futures[future]
            try:
                results[exchange] = future.result(timeout=15)
                print(f"✅ {exchange}: {len(results[exchange])} пар")
            except:
                print(f"❌ {exchange}: помилка")
                results[exchange] = {}
    
    elapsed = time.time() - start
    print(f"⏱️  Час: {elapsed:.1f} сек")
    print(f"📈 Всього пар отримано: {sum(len(data) for data in results.values())}")
    
    return results

def analyze_arbitrage_fast():
    """Аналіз арбітражу - швидка версія"""
    # 1. Завантажити БІЛЬШЕ пар (100 замість 30)
    try:
        with open("pairs_3plus_of_5.txt", "r") as f:
            pairs = [line.strip() for line in f if line.strip() and not line.startswith('#')]  # ← 100 пар
        print(f"📋 Аналіз {len(pairs)} пар (3+ біржі)")
    except:
        pairs = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'ADAUSDT']
        print("⚠️  Використовую тестові пари")
    
    # 2. Отримати дані
    all_data = get_all_data_with_volumes()
    
    # 3. Аналіз паралельно
    print(f"\n🔍 АНАЛІЗ АРБІТРАЖУ...")
    
    opportunities = []
    analyzed = 0
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Створюємо завдання для кожної пари
        future_to_pair = {}
        for pair in pairs:
            future = executor.submit(analyze_single_pair, pair, all_data)
            future_to_pair[future] = pair
        
        # Обробляємо результати
        for future in future_to_pair:
            pair = future_to_pair[future]
            try:
                result = future.result(timeout=5)
                if result:
                    opportunities.append(result)
            except:
                pass
            
            analyzed += 1
            if analyzed % 20 == 0:
                print(f"  Перевірено {analyzed}/{len(pairs)} пар...")
    
    # 4. Сортування
    opportunities.sort(key=lambda x: x['spread'], reverse=True)
    
    # 5. Результати
    print(f"\n💎 РЕЗУЛЬТАТИ АРБІТРАЖУ:")
    print("=" * 100)
    
    if opportunities:
        print(f"Знайдено {len(opportunities)} можливостей (>0.05%, >$100K об'єму)")
        print("\n🏆 ТОП-15 НАЙКРАЩИХ:")
        print("-" * 100)
        print(f"{'ПАРА':<10} {'СПРЕД':<8} {'КУПИТИ':<10} {'ПРОДАВ.':<10} {'ЦІНА':<25} {'ОБЄМ':<20}")
        print("-" * 100)
        
        for opp in opportunities:
            # Форматуємо ціну
            if opp['buy_price'] < 0.01:
                price_str = f"${opp['buy_price']:.8f}→${opp['sell_price']:.8f}"
            elif opp['buy_price'] < 1:
                price_str = f"${opp['buy_price']:.6f}→${opp['sell_price']:.6f}"
            else:
                price_str = f"${opp['buy_price']:.4f}→${opp['sell_price']:.4f}"
            
            # Форматуємо об'єм
            buy_vol = f"${opp['buy_volume']/1000:.0f}K" if opp['buy_volume'] < 1000000 else f"${opp['buy_volume']/1000000:.1f}M"
            sell_vol = f"${opp['sell_volume']/1000:.0f}K" if opp['sell_volume'] < 1000000 else f"${opp['sell_volume']/1000000:.1f}M"
            volume_str = f"{buy_vol}→{sell_vol}"
            
            print(f"{opp['pair']:<10} {opp['spread']:>6.2f}% "
                  f"{opp['buy']:<10} {opp['sell']:<10} "
                  f"{price_str:<25} {volume_str:<20}")
        
        # Статистика
        print(f"\n📊 СТАТИСТИКА:")
        print(f"• Аналізовано пар: {len(pairs)}")
        print(f"• Знайдено арбітражів: {len(opportunities)}")
        
        if opportunities:
            avg_spread = sum(o['spread'] for o in opportunities) / len(opportunities)
            print(f"• Середній спред: {avg_spread:.3f}%")
            print(f"• Максимальний спред: {opportunities[0]['spread']:.3f}%")
    else:
        print("⚠️  АРБІТРАЖНИХ МОЖЛИВОСТЕЙ НЕ ЗНАЙДЕНО")

def analyze_single_pair(pair, all_data):
    """Аналіз однієї пари"""
    prices = {}
    volumes = {}
    
    for exchange, data in all_data.items():
        # Визначаємо ключ
        if exchange == 'Gate.io':
            key = pair.replace('USDT', '_USDT')
        elif exchange == 'HTX':
            key = pair.lower()
        else:
            key = pair
        
        if key in data:
            prices[exchange] = data[key]['price']
            
            # Об'єм у USDT
            if exchange == 'Binance':
                volumes[exchange] = data[key]['volume']
            elif exchange == 'Bybit':
                volumes[exchange] = data[key]['volume24h']
            elif exchange == 'MEXC':
                volumes[exchange] = data[key]['volume']
            elif exchange == 'Gate.io':
                volumes[exchange] = data[key]['quote_volume']
            elif exchange == 'HTX':
                volumes[exchange] = data[key]['vol']
    
    # Перевірка
    if len(prices) >= 3:
        min_ex = min(prices, key=prices.get)
        max_ex = max(prices, key=prices.get)
        
        min_price = prices[min_ex]
        max_price = prices[max_ex]
        min_volume = volumes.get(min_ex, 0)
        max_volume = volumes.get(max_ex, 0)
        
        spread = ((max_price - min_price) / min_price) * 100
        
        if spread > 0.05 and min_volume > 100000 and max_volume > 100000:
            return {
                'pair': pair,
                'spread': spread,
                'buy': min_ex,
                'sell': max_ex,
                'buy_price': min_price,
                'sell_price': max_price,
                'buy_volume': min_volume,
                'sell_volume': max_volume,
                'exchanges': len(prices)
            }
    
    return None

def main():
    print("🎯 АРБІТРАЖ З ОБ'ЄМАМИ (3+ БІРЖІ)")
    print("=" * 60)
    print("📌 Фільтри: спред >0.05%, об'єм >$100K, мінімум 3 біржі")
    print()
    
    analyze_arbitrage_fast()

if __name__ == "__main__":
    main()