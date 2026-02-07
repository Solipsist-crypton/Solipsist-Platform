# test_api.py
import requests
import json

try:
    # Тест 1: Звичайний запит
    print("Тест 1: GET /arbitrage")
    r = requests.get('http://127.0.0.1:5000/arbitrage', timeout=10)
    print(f"Статус: {r.status_code}")
    print(f"Дані: {json.dumps(r.json(), indent=2)[:500]}...")
    
    # Тест 2: Health check
    print("\nТест 2: GET /health")
    r = requests.get('http://127.0.0.1:5000/health', timeout=5)
    print(f"Статус: {r.status_code}")
    print(f"Відповідь: {r.json()}")
    
except Exception as e:
    print(f"Помилка: {e}")