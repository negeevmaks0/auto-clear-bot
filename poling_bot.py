import os
import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)



class BotPolling:
    def __init__(self):
        self.token = '2111646132:AAFrkWTTzbfLsLtVwlOAXd2RUuKDDmJQgiw'

        self.application = ApplicationBuilder().token(self.token).build()

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            handlers=[
                logging.FileHandler("log_polling.ps", encoding="utf-8"),
                logging.StreamHandler()
            ]
        )

        for noisy in ["httpx", "telegram", "apscheduler"]:
            logging.getLogger(noisy).setLevel(logging.WARNING)


    async def start(self, update: Update, null):
        user_id = update.effective_user.id
        name = update.effective_user.full_name

        logging.info(f'User ID: {user_id}')
        logging.info(f'Name: {name}')
        await update.message.reply_text("Deine ID ist erfolgreich gespeichert!")


    def main(self):
        self.application.add_handler(CommandHandler('start', self.start))

        logging.info('Bot start!')

        self.application.run_polling()



if __name__ == '__main__':
    app = BotPolling()

    app.main()
