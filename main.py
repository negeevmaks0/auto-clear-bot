import asyncio
import os
import sys
import random

import urllib.parse
from pathlib import Path

import datetime
import calendar

from playwright.async_api import async_playwright
import requests

from settings import Setting
from excl import Excel
from environ import Env




class MainApp(Setting):
    def __init__(self):
        super().__init__()

        self.ca = CreateAntword()
        # self.wa = WhatsApp()
        self.tg = Telegram()
        self.ex = Excel()


    async def main(self):
        dat = datetime.date.today()
        groups = list(self.group_tasks[f'{dat.month}.{dat.day}'].values())

        keys = list(self.group_tasks.keys())
        index = keys.index(f'{dat.month}.{dat.day}')
        prev = keys[index - 1] if index > 0 else None

        month = None

        if prev:
            month = int(prev.split('.')[0])

        texts = list(await self.ca.create(dat, groups))

        tasks = texts.pop(-1)
        new_tasks = [[], [], []]

        for i in range(0, 3):
            for task in tasks[1][i]:
                new_tasks[i].append(tasks[0][task])

        file = self.ex.update_data(new_tasks, tasks[2])

        phones = [self.contacts[groups[1]], self.contacts[groups[0]], self.contacts[groups[2]]]
        enum = [0, 1, 2]

        if month == dat.month:
            texts.pop(1)
            phones.pop(1)
            enum.pop(1)

            file = False


        for ind, phone, text in zip(enum, phones, texts):
            input_data = [phone, text, ind]

            print(input_data)

            # screen = await self.wa.main(input_data)
            await self.tg.send_message(input_data)
        
        if file:
            await self.tg.send_file(file)



class CreateAntword(Setting):
    def __init__(self):
        super().__init__()


    async def create(self, dat, groups):
        year, month, day = int(dat.year), int(dat.month), int(dat.day)
        last_day = int(calendar.monthrange(year, month)[1])

        if last_day - 2 <= day:
            month += 1

        mittwoch, samstag, monat = self.planung[month].values()
        tasks = [mittwoch, samstag, monat if monat else False]
        ttask = ['', '']


        if tasks[0]:
            ttask[0] += 'Четверг:\n\n'

            for task in tasks[0]:
                ttask[0] += f'{self.tasks[task]}\n'

        if tasks[1]:
            ttask[0] += '\nВоскресенье:\n\n' if ttask[0] else 'Воскресенье:\n\n'

            for task in tasks[1]:
                ttask[0] += f'{self.tasks[task]}\n'


        if tasks[2]:
            for task in tasks[2]:
                ttask[1] += f'{self.tasks[task]}\n'

        else:
            ttask[1] = False


        uns = [False, False, False]

        if groups[0] == 'Kostheim':
            uns[0] = True

        elif groups[1] == 'Kostheim':
            uns[1] = True

        elif groups[2] == 'Kostheim':
            uns[2] = True


        if uns[0]:
            text_to_return1 = random.choice(list(self.message['uns']['woche'].values())).format(tasks = ttask[0])

        else:
            text_to_return1 = random.choice(list(self.message['woche'].values())).format(tasks = ttask[0])

        if uns[1]:
            text_to_return2 = random.choice(list(self.message['uns']['monat'].values())).format(tasks = ttask[1]) if monat else self.message['nope_monat']

        else:
            text_to_return2 = random.choice(list(self.message['monat'].values())).format(tasks = ttask[1]) if monat else self.message['nope_monat']

        if uns[2]:
            text_to_return3 = random.choice(list(self.message['uns']['gast'].values()))

        else:
            text_to_return3 = random.choice(list(self.message['gast'].values()))


        return text_to_return1, text_to_return2, text_to_return3, [self.tasks, tasks, self.monats[month]]



class Telegram:
    def __init__(self):
        dir_ = os.path.dirname(os.path.abspath(__file__))
        
        self.env = Env()
        self.env.read_env(os.path.join(dir_, '.env'))

        self.headers = {
            "X-API-Key": self.env('X_API_KEY').strip()
        }

        self.bot_api_url = self.env('BOT_API_URL_SEND').strip()
        self.bot_api_url_file = self.env('BOT_API_URL_FILE').strip()

        
    async def send_message(self, data_to_send):
        phone = data_to_send[0]
        raw_text = data_to_send[1]
        task_type_index = data_to_send[2]

        encoded_text = urllib.parse.quote(raw_text)
        wa_url = f'https://web.whatsapp.com/send?phone={phone}&text={encoded_text}'

        if task_type_index == 1:
            task_type = 'Месячное'

        elif task_type_index == 2:
            task_type = 'Гостеприимство'

        else:
            task_type = 'Недельное'

        telegram_message = (
            "Привет! Новое распоряжение готово, ссылка для отправки будет ниже.\n\n"
            "Краткая информация:\n"
            f"Номер телефона: {phone}\n"
            f"Тип задания: {task_type}"
        )

        payload = {
            'url': wa_url,
            'message': telegram_message
        }

        try:
            response = requests.post(self.bot_api_url, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                print(f"[Telegram API] Сигнал успешно отправлен боту для типа задания: {('Месячное' if task_type_index == 1 else 'Недельное or Гостеприимство')}")

            else:
                print(f"[Telegram API] Ошибка сервера бота: {response.status_code} — {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[Telegram API] Не удалось связаться со скриптом бота: {e}")


    async def send_file(self, file):
        telegram_message = "Прикрепляю файл для розпечатки"

        payload = {
            'file': file,
            'message': telegram_message
        }

        try:
            response = requests.post(self.bot_api_url_file, json=payload, headers=self.headers)
            
            if response.status_code == 200:
                print(f"[Telegram API] Сигнал успешно отправлен боту для типа задания: FILE")

            else:
                print(f"[Telegram API] Ошибка сервера бота: {response.status_code} — {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"[Telegram API] Не удалось связаться со скриптом бота: {e}")




class WhatsApp:
    def __init__(self):
        #self.profile_dir = Path("/home/ps-server/ftp/auto_clearbot/profile")
        self.profile_dir = Path('profile')

        #self.screenshot_dir = Path("/home/ps-server/ftp/auto_clearbot/screenshots")
        self.screenshot_dir = Path('screenshots')

        self.screenshot_dir.mkdir(exist_ok=True)

        self.url = "https://web.whatsapp.com/send?phone={phone}&text={message}"


    def screenshot_filename(self, stage: str):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        return self.screenshot_dir / f"{timestamp}_{stage}.png"


    async def create_profile(self):
        print("Профиль не найден — создаем первый вход.")

        context = await self.playwright.firefox.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            args=["--start-maximized"]
        )
        page = await context.new_page()

        await page.goto("https://web.whatsapp.com")
        await asyncio.sleep(10)
        await page.screenshot(path=str(self.screenshot_filename("page_loaded")))

        try:
            qr_canvas = await page.wait_for_selector("canvas[aria-label='Scan me!']", timeout=60000)
            await qr_canvas.screenshot(path=str(self.screenshot_filename("qr_code")))

            print(f"QR-код сохранен: {self.screenshot_filename('qr_code')}")

        except:
            print("QR-код не найден (возможно сессия уже есть)")

        print("Ожидаем сканирования QR и входа...")

        await page.wait_for_selector("div[role='grid']", timeout=0)
        await page.screenshot(path=str(self.screenshot_filename("logged_in")))

        print("Авторизация выполнена, профиль сохранен.")

        await context.close()


    async def send_message(self):
        context = await self.playwright.firefox.launch_persistent_context(
            user_data_dir=str(self.profile_dir),
            args=["--no-sandbox", "--disable-dev-shm-usage", "--window-size=1920,1080"]
        )

        page = context.pages[0] if context.pages else await context.new_page()

        await page.goto(self.url.format(phone = self.phone, message = self.message))

        try:
            await page.wait_for_selector("div[contenteditable='true']", timeout=30000)
            await asyncio.sleep(7)

            await page.keyboard.press("Enter")

            screen = str(self.screenshot_filename("send"))
            await page.screenshot(path = screen)
            print("Сообщение отправлено (см. скриншот send).")

            return screen

        except:
            await page.screenshot(path=str(self.screenshot_filename("error")))

            print("Ошибка: WhatsApp требует QR! См. скриншот error")

        finally:
            await asyncio.sleep(5)
            await context.close()


    async def main(self, input_data):
        self.phone = input_data[0]
        self.message = urllib.parse.quote(input_data[1])

        async with async_playwright() as self.playwright:
            if not self.profile_dir.exists():
                self.profile_dir.mkdir(exist_ok=True)

                await self.create_profile()
                print("Профиль создан. Теперь можно отправлять сообщения этой же командой.")

                return

            screen = await self.send_message()

            return screen



if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.main())
