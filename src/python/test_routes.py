import market_data
print('Доступні функції:')
for item in dir(market_data):
    if not item.startswith('_'):
        print(f'  - {item}')