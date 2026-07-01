import os
import asyncio
import logging
from contextlib import asynccontextmanager

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import (
    ApplicationBuilder, 
    CommandHandler, 
    MessageHandler, 
    CallbackQueryHandler, 
    ContextTypes, 
    filters
)

import uvicorn
from fastapi import FastAPI, Body, Header, HTTPException

from environ import Env



fast_app = FastAPI()



class BotPolling:
    def __init__(self):
        self.env = Env()
        self.env.read_env('.env')

        self.token = self.env('API_TOKEN').strip()
        self.api_key = self.env('X_API_KEY').strip()

        self.allowed_ids = self.env.list('ALLOWED_IDS', cast=int)
        # self.allowed_ids = [int(self.env('TEST').strip())]

        self.application = None
        self.server = None

        
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

        self.setup_routes()


    def setup_routes(self):
        @fast_app.post("/send-signal")
        async def receive_signal(x_api_key: str = Header(None), data: dict = Body(...)):
            if x_api_key != self.api_key:
                raise HTTPException(status_code=403, detail="Forbidden")

            url = data.get('url')
            message = data.get('message')

            await self.send_message(url, message)
            return {"status": "sent"}


        @fast_app.post("/send-signal-file")
        async def receive_signal(x_api_key: str = Header(None), data: dict = Body(...)):
            if x_api_key != self.api_key:
                raise HTTPException(status_code=403, detail="Forbidden")

            file = data.get('file')
            message = data.get('message')

            await self.send_message_file(file, message)
            return {"status": "sent"}
        

        @fast_app.post("/send-update")
        async def receive_signal_update(x_api_key: str = Header(None), data: dict = Body(...)):
            if x_api_key != self.api_key:
                raise HTTPException(status_code=403, detail="Forbidden")

            message = data.get('message')

            for id_ in self.allowed_ids:
                await self.application.bot.send_message(
                    chat_id = id_,
                    text = message,
                )

            return {"status": "sent"}


    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        name = update.effective_user.full_name

        logging.info(f'User ID: {user_id}')
        logging.info(f'Name: {name}')
        await update.message.reply_text("Deine ID ist erfolgreich gespeichert!")



    async def send_message(self, url, message):
        keyboard = [[InlineKeyboardButton("Send", url=url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        for id_ in self.allowed_ids:
            await self.application.bot.send_message(
                chat_id = id_,
                text = message,
                reply_markup = reply_markup
            )


    async def send_message_file(self, file, message):
        for id_ in self.allowed_ids:
            with open(file, 'rb') as document_file:
                await self.application.bot.send_document(
                    chat_id = id_,
                    document = document_file,
                    caption = message,
                    read_timeout = 60,
                    write_timeout = 60
                )


    async def main(self):
        self.application = ApplicationBuilder().token(self.token).build()
        self.application.add_handler(CommandHandler('start', self.start))

        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()

        logging.info('Bot start!')


        config = uvicorn.Config(
            app=fast_app,
            host=self.env('HOST').strip(),
            port=int(self.env('PORT').strip()),
            log_level='info'
        )
        self.server = uvicorn.Server(config)

        try:
            await self.server.serve()

        finally:
            logging.info('Stopping bot...')

            await self.application.updater.stop()
            await self.application.stop()
            await self.application.shutdown()



if __name__ == '__main__':
    bot_app = BotPolling()

    asyncio.run(bot_app.main())
