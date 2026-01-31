from compare import compare_prices, find_arbitrage

# Список монет для порівняння
symbols = ['BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT', 'ADAUSDT']

# Порівняти ціни
print("🔍 Порівняння цін на біржах:")
print("=" * 60)

results = compare_prices(symbols)

for symbol, data in results.items():
    print(f"\n{symbol}:")
    print(f"  Binance:  ${data['binance']:,.2f}")
    print(f"  Bybit:    ${data['bybit']:,.2f}")
    print(f"  Різниця:  ${data['difference']:.2f} ({data['diff_percent']:.2f}%)")
    print(f"  Дешевше: {data['cheaper']}")

# Знайти арбітражні можливості
print("\n💡 Арбітражні можливості:")
print("=" * 60)

arbitrage = find_arbitrage(results, threshold=0.05)  # 0.05% мінімум

if arbitrage:
    for opp in arbitrage:
        print(f"\n{opp['symbol']}:")
        print(f"  Купити на: {opp['buy_at']} (${opp['buy_price']:,.2f})")
        print(f"  Продати на: {opp['sell_at']} (${opp['sell_price']:,.2f})")
        print(f"  Прибуток: {opp['profit_percent']:.2f}%")
else:
    print("Немає арбітражних можливостей (>0.05%)")