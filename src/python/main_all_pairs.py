import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.python.exchanges_all import ALL_EXCHANGES_FAST

def get_all_prices_fast():
    """Отримати всі ціни з 5 бірж швидко"""
    print("🚀 ОТРИМАННЯ ВСІХ ЦІН")
    
    start = time.time()
    results = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(func): name for name, func in ALL_EXCHANGES_FAST.items()}
        
        for future in futures:
            exchange = futures[future]
            try:
                results[exchange] = future.result(timeout=10)
            except:
                results[exchange] = {}
    
    print(f"⏱️  Час: {time.time() - start:.1f} сек")
    return results

def create_3plus_file():
    """Створити файл з парами на 3+ біржах"""
    print("\n🎯 СТВОРЕННЯ ФАЙЛУ ПАР НА 3+ БІРЖАХ")
    print("=" * 60)
    
    # 1. Отримати всі ціни
    all_data = get_all_prices_fast()
    
    # 2. Отримати USDT пари
    usdt_pairs_by_exchange = {}
    
    for exchange, pairs in all_data.items():
        if exchange == 'Gate.io':
            # BTC_USDT → BTCUSDT
            usdt_pairs = [p.replace('_USDT', 'USDT') for p in pairs.keys() 
                         if p.endswith('_USDT')]
        elif exchange == 'HTX':
            # btcusdt → BTCUSDT
            usdt_pairs = [p.upper() for p in pairs.keys() 
                         if p.lower().endswith('usdt')]
        else:
            # BTCUSDT
            usdt_pairs = [p for p in pairs.keys() if p.endswith('USDT')]
        
        usdt_pairs_by_exchange[exchange] = set(usdt_pairs)
    
    # 3. Всі унікальні USDT пари
    all_usdt_pairs = set()
    for pairs in usdt_pairs_by_exchange.values():
        all_usdt_pairs.update(pairs)
    
    print(f"📈 Усього унікальних USDT пар: {len(all_usdt_pairs)}")
    
    # 4. Рахуємо кількість бірж для кожної пари
    pair_coverage = {}
    for pair in all_usdt_pairs:
        count = sum(1 for exchange in usdt_pairs_by_exchange 
                   if pair in usdt_pairs_by_exchange[exchange])
        pair_coverage[pair] = count
    
    # 5. Беремо пари на 3, 4, 5 біржах
    pairs_3plus = []
    for count in [3, 4, 5]:
        pairs = [p for p, c in pair_coverage.items() if c == count]
        pairs_3plus.extend(pairs)
        print(f"🎯 На {count}/5 біржах: {len(pairs):>4} пар")
    
    # 6. Записуємо в файл
    with open("pairs_3plus_of_5.txt", "w") as f:
        f.write("# Пари на 3+ біржах (з 5)\n")
        f.write(f"# Згенеровано: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"# Кількість: {len(pairs_3plus)}\n")
        f.write("#" * 50 + "\n\n")
        
        for pair in sorted(pairs_3plus):
            f.write(f"{pair}\n")
    
    print(f"\n✅ Створено pairs_3plus_of_5.txt: {len(pairs_3plus)} пар")
    
    # 7. Топ-20 найпопулярніших
    print(f"\n🏆 ТОП-20 НАЙПОПУЛЯРНІШИХ ПАР:")
    sorted_pairs = sorted(pair_coverage.items(), key=lambda x: (-x[1], x[0]))
    for i, (pair, count) in enumerate(sorted_pairs[:20], 1):
        print(f"{i:>2}. {pair:<12} {count}/5 бірж")
    
    return pairs_3plus

def main():
    create_3plus_file()

if __name__ == "__main__":
    main()