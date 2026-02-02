import os
import sys
import requests
from dotenv import load_dotenv

# Завантажуємо змінні з .env файлу
load_dotenv()

class TelegramBot:
    def __init__(self):
        # Отримуємо дані з .env
        self.token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    def send_message(self, message="привіт"):
        """Надсилає повідомлення у Telegram"""
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        
        data = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"  # можна використовувати HTML розмітку
        }
        
        try:
            response = requests.post(url, data=data)
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get('ok'):
                print(f"✅ Повідомлення відправлено: '{message}'")
                return True
            else:
                print(f"❌ Помилка відправки: {response_data.get('description')}")
                return False
                
        except Exception as e:
            print(f"❌ Помилка з'єднання: {e}")
            return False
    
    def get_updates(self):
        """Отримує оновлення бота (для перевірки)"""
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        try:
            response = requests.get(url)
            return response.json()
        except Exception as e:
            print(f"Помилка: {e}")
            return None

def main():
    # Ініціалізуємо бота
    bot = TelegramBot()
    
    # Варіанти використання:
    
    # 1. Відправити просте повідомлення
    bot.send_message("привіт! 👋")
    
    # 2. Відправити кілька повідомлень
    # messages = ["Перше повідомлення", "Друге повідомлення", "Третє повідомлення"]
    # for msg in messages:
    #     bot.send_message(msg)
    
    # 3. Відправити змінну
    # name = "Макс"
    # bot.send_message(f"Привіт, {name}! Як справи?")
    
    # 4. Перевірити оновлення (для отримання chat_id)
    # print("\nПеревірка оновлень:")
    # updates = bot.get_updates()
    # if updates and updates.get('ok'):
    #     for update in updates.get('result', []):
    #         if 'message' in update:
    #             chat_id = update['message']['chat']['id']
    #             print(f"Chat ID: {chat_id}")

if __name__ == "__main__":
    main()