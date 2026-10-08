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
from db import DataBase




class MainApp(Setting):
    def __init__(self):
        super().__init__()

        self.db = DataBase()

        self.ca = CreateAntword(self.db)
        self.tg = Telegram()
        self.ex = Excel()


    async def main(self):
        dat = datetime.date.today()

        groups, keys, date_str = self.db.get_group_tasks_by_date(dat)

        try:
            raw_keys = [k[0] if isinstance(k, tuple) else k for k in keys]

            def to_real_date(key_str):
                y, m, d = map(int, key_str.split('.'))
                return datetime.date(2000 + y, m, d)

            clean_keys = sorted(raw_keys, key=to_real_date)

            index = clean_keys.index(date_str)
            prev = clean_keys[index - 1] if index > 0 else None

        except ValueError:
            prev = None

        month = None

        if prev:
            month = int(prev.split('.')[1])

        texts = list(await self.ca.create(dat, groups))

        excel_package = texts.pop(-1) 
        db_tasks = excel_package[0]
        active_task_ids = excel_package[1]
        month_name = excel_package[2]

        new_tasks = [[], [], []]

        for i in range(0, 3):
            if i < len(active_task_ids) and active_task_ids[i]:
                for task_id in active_task_ids[i]:
                    task_text = db_tasks.get(task_id)

                    if task_text:
                        new_tasks[i].append(task_text)

        print(f"Передаем в Excel месяц: {month_name}")
        file = self.ex.update_data(new_tasks, month_name)

        phones = [
            self.db.get_contact_phone(groups[1]), 
            self.db.get_contact_phone(groups[0]), 
            self.db.get_contact_phone(groups[2])
        ]
        enum = [0, 1, 2]

        if not texts[2]:
            texts.pop(-1)

        if month == dat.month:
            texts.pop(1)
            phones.pop(1)
            enum.pop(1)

            file = False

        for ind, phone, text in zip(enum, phones, texts):
            input_data = [phone, text, ind]

            print(input_data)

            await self.tg.send_message(input_data)
        
        if file:
            await self.tg.send_file(file)



class CreateAntword(Setting):
    def __init__(self, db_instance):
        super().__init__()

        self.db = db_instance


    async def create(self, dat, groups):
        year, month, day = int(dat.year), int(dat.month), int(dat.day)
        last_day = int(calendar.monthrange(year, month)[1])

        if last_day - 2 <= day:
            month += 1

        short_year = str(year)[2:]
        month_key = f'{month}.{short_year}'

        db_planung, db_tasks, db_messages = self.db.get_planning_and_messages(month_key)

        mittwoch = db_planung["mittwoch"]
        samstag = db_planung["samstag"]
        monat = db_planung["monat"]

        tasks = [mittwoch, samstag, monat if monat else None]
        ttask = ['', '']


        if tasks[0]:
            ttask[0] += 'Четверг:\n\n'

            for task in tasks[0]:
                ttask[0] += f'{db_tasks.get(task, "")}\n'

        if tasks[1]:
            ttask[0] += '\nВоскресенье:\n\n' if ttask[0] else 'Воскресенье:\n\n'

            for task in tasks[1]:
                ttask[0] += f'{db_tasks.get(task, "")}\n'


        if tasks[2]:
            for task in tasks[2]:
                ttask[1] += f'{db_tasks.get(task, "")}\n'

        else:
            ttask[1] = False


        uns = [False, False, False]

        if groups[0] == 'Kastel': uns[0] = True
        elif groups[1] == 'Kastel': uns[1] = True
        elif groups[2] == 'Kastel': uns[2] = True

        if uns[0]:
            text_to_return1 = random.choice(list(db_messages['uns']['woche'].values())).format(tasks=ttask[0])

        else:
            text_to_return1 = random.choice(list(db_messages['woche'].values())).format(tasks=ttask[0])

        if uns[1]:
            text_to_return2 = random.choice(list(db_messages['uns']['monat'].values())).format(tasks=ttask[1]) if monat else db_messages['uns']['nope_monat']

        else:
            monat_templates = list(db_messages['monat'].values())
            text_to_return2 = random.choice(monat_templates).format(tasks=ttask[1]) if (monat and monat_templates) else db_messages['uns']['nope_monat']


        if uns[2]:
            text_to_return3 = random.choice(list(db_messages['uns']['gast'].values()))

        else:
            gast_templates = list(db_messages['gast'].values())
            text_to_return3 = random.choice(gast_templates) if gast_templates else None


        return text_to_return1, text_to_return2, text_to_return3, [db_tasks, tasks, self.monats[month]]



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

        task_type = 'Месячное' if task_type_index == 1 else ('Гостеприимство' if task_type_index == 2 else 'Недельное')

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



if __name__ == "__main__":
    app = MainApp()
    asyncio.run(app.main())
