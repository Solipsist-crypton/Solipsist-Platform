import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from exchanges import EXCHANGES, get_all_binance_prices

def load_coins(filename="backend/app/arb_monitor/coins.txt"):
    try:
        with open(filename, 'r') as f:
            coins = [line.strip() for line in f if line.strip()]
        
        # Фільтруємо проблемні монети
        problematic = [
            'MATICUSDT', 'EOSUSDT', 'FTMUSDT', 'KLAYUSDT', 'MKRUSDT',
            'RNDRUSDT', 'AGIXUSDT', 'BTCBUSD', 'ETHBUSD', 'BNBBUSD',
            'SOLBUSD', 'ADABUSD', 'XRPDUSD', 'LTCBUSD', 'ADAUSD',
            'XRPUSD', 'LTCUSD'
        ]
        
        filtered_coins = [c for c in coins if c not in problematic]
        removed = len(coins) - len(filtered_coins)
        
        if removed > 0:
            print(f"🗑️  Видалено {removed} проблемних монет")
        
        return filtered_coins[:100]  # Макс 100 монет
    except:
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

def format_price(price):
    if price is None or price <= 0:
        return "---"
    price = float(price)
    if price < 0.01: return f"${price:.6f}"
    elif price < 1: return f"${price:.4f}"
    elif price < 10: return f"${price:.4f}"
    elif price < 1000: return f"${price:.2f}"
    else: return f"${price:,.2f}"

def check_all_coins_optimized(coins, selected_exchanges):
    """Оптимізована перевірка з кешуванням"""
    
    total_coins = len(coins)
    total_exchanges = len(selected_exchanges)
    
    print(f"\n🚀 ОПТИМІЗОВАНА ПЕРЕВІРКА")
    print(f"📊 {total_coins} монет на {total_exchanges} біржах")
    print("=" * 60)
    
    results = {}
    start_time = time.time()
    
    # КЕШУВАННЯ: Отримуємо всі ціни Binance одним запитом
    print("🔍 Отримую всі ціни Binance...")
    binance_cache = get_all_binance_prices()
    binance_hits = 0
    
    if binance_cache:
        print(f"✅ Отримано {len(binance_cache)} пар з Binance")
    
    # Функція для отримання ціни з кешу
    def get_price_cached(coin, exchange):
        if exchange == 'Binance' and binance_cache:
            if coin in binance_cache:
                return binance_cache[coin]
        
        # Для інших бірж - звичайний запит
        func = EXCHANGES[exchange]
        return func(coin)
    
    # Паралельна перевірка
    with ThreadPoolExecutor(max_workers=20) as executor:
        future_to_pair = {}
        
        for coin in coins:
            for exchange_name in selected_exchanges:
                future = executor.submit(get_price_cached, coin, exchange_name)
                future_to_pair[future] = (coin, exchange_name)
        
        # Обробка результатів
        completed = 0
        total_requests = len(future_to_pair)
        
        for future in as_completed(future_to_pair):
            coin, exchange_name = future_to_pair[future]
            
            if coin not in results:
                results[coin] = {}
            
            try:
                price = future.result(timeout=5)
                results[coin][exchange_name] = price
                
                # Лічильник кеш-хітів
                if exchange_name == 'Binance' and price and coin in binance_cache:
                    binance_hits += 1
                    
            except:
                results[coin][exchange_name] = None
            
            completed += 1
            if completed % 50 == 0:
                elapsed = time.time() - start_time
                speed = completed / elapsed if elapsed > 0 else 0
                print(f"  {completed}/{total_requests} | {speed:.0f} з/сек")
    
    elapsed = time.time() - start_time
    
    if binance_cache:
        hit_rate = (binance_hits / total_coins) * 100
        print(f"🎯 Binance кеш: {binance_hits}/{total_coins} ({hit_rate:.1f}%)")
    
    print(f"\n✅ Готово за {elapsed:.1f} сек ({total_coins/elapsed:.1f} монет/сек)")
    
    return results, selected_exchanges

def show_results_compact(results, coins, exchanges):
    """Компактний вивід результатів"""
    print(f"\n📋 РЕЗУЛЬТАТИ ({len(coins)} монет, {len(exchanges)} бірж):")
    print("=" * 70)
    
    # Тільки перші 15 монет для компактності
    display_coins = coins[:15]
    
    for coin in display_coins:
        if coin in results:
            row = f"{coin:<12}"
            success_count = 0
            
            for exchange_name in exchanges:
                price = results[coin].get(exchange_name)
                if price and price > 0:
                    row += " ✓"
                    success_count += 1
                else:
                    row += " ✗"
            
            row += f" {success_count}/{len(exchanges)}"
            print(row)
    
    if len(coins) > 15:
        print(f"\n... і ще {len(coins) - 15} монет")

def main():
    print("🎯 ТЕСТ ПОКРИТТЯ КРИПТОМОНЕТ (ОПТИМІЗОВАНИЙ)")
    print("=" * 50)
    
    # Завантажити монети
    coins = load_coins()
    print(f"📋 Монет для тесту: {len(coins)}")
    
    # Тільки працюючі біржі
    selected = ['Binance', 'Coinex', 'Gate.io', 'HTX', 'MEXC', 'KuCoin', 'Bybit', 'Kraken']
    print(f"🎯 Бірж: {len(selected)}")
    
    # Запустити перевірку
    results, exchanges = check_all_coins_optimized(coins, selected)
    
    # Статистика
    print(f"\n📊 СТАТИСТИКА ПОКРИТТЯ:")
    print("=" * 40)
    
    for exchange in exchanges:
        available = sum(1 for coin in coins 
                       if coin in results and results[coin].get(exchange) and results[coin][exchange] > 0)
        percent = (available / len(coins)) * 100
        print(f"{exchange:<12} {available:>3}/{len(coins)} ({percent:>5.1f}%)")
    
    # Загальне покриття
    print(f"\n📈 ЗАГАЛЬНЕ ПОКРИТТЯ:")
    total_success = 0
    total_possible = len(coins) * len(exchanges)
    
    for coin in coins:
        if coin in results:
            total_success += sum(1 for ex in exchanges if results[coin].get(ex))
    
    coverage_percent = (total_success / total_possible) * 100
    print(f"Успішних запитів: {total_success}/{total_possible} ({coverage_percent:.1f}%)")
    
    # Показати компактні результати
    show_results_compact(results, coins, exchanges)

if __name__ == "__main__":
    main()