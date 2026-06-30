import asyncio
import requests

from environ import Env



class TelegramSendUpdate:
    def __init__(self):
        self.env = Env()
        self.env.read_env('.env')

        self.headers = {
            "X-API-Key": self.env('X_API_KEY').strip()
        }

        self.bot_api_url = self.env('BOT_API_URL_UPLOAD').strip()

        
    async def send_message(self):
        telegram_message = (
            "Привет! Бот обновился, ниже будут новые функции, или изменения.\n\n"
            "Добавлены в план новые группы и внесены в систему.\n"
            "Добавлена возможность отправлять задания с типом Гостеприимство и внесены новые данные на ближайшие даты.\n"
            "Исправленны небольшие ошибки и проблема отправки неверного текста."
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
