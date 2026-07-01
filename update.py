import asyncio
import requests
import os

from environ import Env



class TelegramSendUpdate:
    def __init__(self):
        dir_ = os.path.dirname(os.path.abspath(__file__))
        
        self.env = Env()
        self.env.read_env(os.path.join(dir_, '.env'))

        self.headers = {
            "X-API-Key": self.env('X_API_KEY').strip()
        }

        self.bot_api_url = self.env('BOT_API_URL_UPLOAD').strip()

        
    async def send_message(self):
        telegram_message = (
            "Привет! Бот обновился, ниже будут новые функции, или изменения.\n\n"
            "Улучшена безопастность посредством переработки системы доступа к ключам доступа. Мелкая оптимизация\n"
            "Добавлена отбработка и отправка плана для печати\n"
            "Поскольку распоряжения уже были отправлены, но появились новые возможности, все будет отправленно за эту неделю заново."
        )

        payload = {
            'message': telegram_message
        }

        try:
            response = requests.post(self.bot_api_url, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                print(f"[Telegram API] Сигнал успешно отправлен боту")

            else:
                print(f"[Telegram API] Ошибка сервера бота: {response.status_code} — {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[Telegram API] Не удалось связаться со скриптом бота: {e}")


if __name__ == '__main__':
    update = TelegramSendUpdate()

    asyncio.run(update.send_message())
