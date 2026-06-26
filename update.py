import asyncio
import requests



class TelegramSendUpdate:
    def __init__(self):
        self.headers = {
            "X-API-Key": "ya-silno_liublu-lesiy"
        }

        self.bot_api_url = "http://127.0.0.1:9000/send-update"

        
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
