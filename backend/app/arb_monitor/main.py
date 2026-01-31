import time
from exchanges import *

def load_coins(filename="coins.txt"):
    """Завантажити список монет з файлу"""
    try:
        with open(filename, 'r') as f:
            coins = [line.strip() for line in f if line.strip()]
        return coins
    except:
        # Якщо файлу немає - стандартний список
        return ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"]

def check_all_coins(coins):
    """Перевірити всі монети на всіх біржах"""
    results = {}
    
    print("🔍 ПЕРЕВІРКА МОНЕТ НА БІРЖАХ")
    print("=" * 70)
    print(f"{'МОНЕТА':<12} {'Binance':<12} {'Bybit':<12} {'KuCoin':<12} Статус")
    print("-" * 70)
    
    for coin in coins:
        # Отримуємо ціни
        b_price = get_binance_price(coin)
        y_price = get_bybit_price(coin)
        k_price = get_kucoin_price(coin)
        
        # Статус доступності
        status = []
        if b_price: status.append("✅")
        else: status.append("❌")
        if y_price: status.append("✅")
        else: status.append("❌")
        if k_price: status.append("✅")
        else: status.append("❌")
        
        # Виводимо результат
        b_str = f"${b_price:,.2f}" if b_price else "---"
        y_str = f"${y_price:,.2f}" if y_price else "---"
        k_str = f"${k_price:,.2f}" if k_price else "---"
        
        print(f"{coin:<12} {b_str:<12} {y_str:<12} {k_str:<12} {' '.join(status)}")
        
        # Зберігаємо результати
        results[coin] = {
            'Binance': b_price,
            'Bybit': y_price,
            'KuCoin': k_price
        }
        
        # Невелика затримка, щоб не заблокували
        time.sleep(0.1)
    
    return results

def show_statistics(results):
    """Показати статистику"""
    print("\n📊 СТАТИСТИКА:")
    print("=" * 70)
    
    total_coins = len(results)
    
    # Підрахунок доступності
    available_on = {
        'Binance': 0,
        'Bybit': 0,
        'KuCoin': 0,
        'All': 0,
        'None': 0
    }
    
    for coin, prices in results.items():
        # Рахуємо для кожної біржі
        if prices['Binance']: available_on['Binance'] += 1
        if prices['Bybit']: available_on['Bybit'] += 1
        if prices['KuCoin']: available_on['KuCoin'] += 1
        
        # Рахуємо загальну доступність
        available_count = sum(1 for price in prices.values() if price)
        if available_count == 3:
            available_on['All'] += 1
        elif available_count == 0:
            available_on['None'] += 1
    
    # Виводимо статистику
    print(f"Усього монет: {total_coins}")
    print(f"\nДоступність:")
    print(f"  Binance:  {available_on['Binance']}/{total_coins} ({available_on['Binance']/total_coins*100:.1f}%)")
    print(f"  Bybit:    {available_on['Bybit']}/{total_coins} ({available_on['Bybit']/total_coins*100:.1f}%)")
    print(f"  KuCoin:   {available_on['KuCoin']}/{total_coins} ({available_on['KuCoin']/total_coins*100:.1f}%)")
    print(f"\nНа всіх 3 біржах: {available_on['All']}")
    print(f"Не на жодній:    {available_on['None']}")
    
    # Показуємо монети, які не знайдені
    not_found = [coin for coin, prices in results.items() 
                 if not any(prices.values())]
    
    if not_found:
        print(f"\n⚠️  Не знайдені: {', '.join(not_found)}")

def main():
    # Завантажуємо монети
    coins = load_coins()
    print(f"📋 Завантажено {len(coins)} монет для перевірки")
    
    # Перевіряємо
    results = check_all_coins(coins)
    
    # Показуємо статистику
    show_statistics(results)
    
    # Записуємо результати в файл
    with open("results.txt", "w") as f:
        f.write("Результати перевірки монет\n")
        f.write("=" * 50 + "\n")
        for coin, prices in results.items():
            f.write(f"{coin}:\n")
            f.write(f"  Binance:  {prices['Binance'] or 'N/A'}\n")
            f.write(f"  Bybit:    {prices['Bybit'] or 'N/A'}\n")
            f.write(f"  KuCoin:   {prices['KuCoin'] or 'N/A'}\n\n")
    
    print(f"\n💾 Результати збережено в results.txt")

# Запуск
if __name__ == "__main__":
    main()