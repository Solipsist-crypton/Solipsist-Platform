# test_routes.py
from api_bridge import app

print("Доступні роути:")
for rule in app.url_map.iter_rules():
    print(f"  {rule.rule}")