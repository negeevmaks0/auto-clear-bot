import sqlite3
import json

import os
import asyncio



class DataBase:
    def __init__(self, name='ps.db'):
        self.db_filename = name

        self.create_db()


    def create_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS contacts (
                city TEXT PRIMARY KEY,
                phone TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS group_tasks (
                date_key TEXT PRIMARY KEY,
                monat TEXT,
                woche TEXT,
                gast TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                msg_type TEXT NOT NULL,
                template_id INTEGER,
                text TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS task_descriptions (
                task_id INTEGER PRIMARY KEY,
                description TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS planung (
                date_key TEXT PRIMARY KEY,
                mittwoch TEXT NOT NULL,
                samstag TEXT NOT NULL,
                monat TEXT NOT NULL
            )
        """
        )

        conn.commit()
        conn.close()


    def _get_connection(self):
        return sqlite3.connect(self.db_filename)


    def _sync_save_schedule(self, schedule_list):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        batch_data = [
            (
                item['date_range'],
                item['monthly_cleaning'],
                item['weekly_cleaning'],
                item['hospitality']
            )
            for item in schedule_list
        ]
        
        cursor.executemany(
            "INSERT OR REPLACE INTO group_tasks (date_key, monat, woche, gast) VALUES (?, ?, ?, ?)",
            batch_data
        )
        conn.commit()
        conn.close()


    async def save_parsed_schedule(self, schedule_list):
        await asyncio.to_thread(self._sync_save_schedule, schedule_list)


    def _sync_compare_schedule(self, new_schedule_list):
        conn = self._get_connection()
        cursor = conn.cursor()
        
        diff_report = []
        
        labels = {
            'weekly_cleaning': 'Еженедельная уборка',
            'monthly_cleaning': 'Ежемесячная уборка',
        }

        for new_item in new_schedule_list:
            date_key = new_item['date_range']
            
            cursor.execute(
                "SELECT woche, monat, gast FROM group_tasks WHERE date_key = ?", 
                (date_key,)
            )
            row = cursor.fetchone()
            
            old_item = {
                'weekly_cleaning': row[0] if row else None,
                'monthly_cleaning': row[1] if row else None
            }
            
            has_changes = False
            item_diff = {"date": date_key, "changes": []}
            
            for field in ['weekly_cleaning', 'monthly_cleaning']:
                old_val = old_item[field]
                new_val = new_item[field]
                
                if old_val != new_val:
                    has_changes = True

                    old_display = old_val if old_val else "[Пусто]"
                    new_display = new_val if new_val else "[Удалено]"
                    
                    item_diff["changes"].append(
                        f"🔹 {labels[field]}:\n   {old_display} ➔ <b>{new_display}</b>"
                    )
            
            if has_changes:
                diff_report.append(item_diff)
                
        conn.close()
        return diff_report


    async def compare_schedule(self, new_schedule_list):
        return await asyncio.to_thread(self._sync_compare_schedule, new_schedule_list)


    def get_group_tasks_by_date(self, dat):
        short_year = dat.strftime('%y')
        date_str = f"{short_year}.{dat.month}.{dat.day}"
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT woche, monat, gast FROM group_tasks WHERE date_key = ?", (date_str,))
        row = cursor.fetchone()
        
        cursor.execute("SELECT date_key FROM group_tasks")

        all_keys = [r[0] for r in cursor.fetchall()]
        conn.close()
        
        groups = [row[0] if row and row[0] else '', 
                  row[1] if row and row[1] else '', 
                  row[2] if row and row[2] else ''] if row else ['', '', '']
        
        return groups, all_keys, date_str
        

    def get_contact_phone(self, city):
        if not city:
            return ""

        conn = self._get_connection()

        cursor = conn.cursor()
        cursor.execute("SELECT phone FROM contacts WHERE city = ?", (city,))
        row = cursor.fetchone()

        conn.close()

        return row[0] if row else ""


    def get_planning_and_messages(self, month_key):
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT mittwoch, samstag, monat FROM planung WHERE date_key = ?", (month_key,))
        plan_row = cursor.fetchone()
        
        cursor.execute("SELECT task_id, description FROM task_descriptions")
        tasks_dict = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT msg_type, template_id, text FROM messages")
        messages_rows = cursor.fetchall()
        conn.close()

        planung = {
            "mittwoch": json.loads(plan_row[0]) if plan_row else [],
            "samstag": json.loads(plan_row[1]) if plan_row else [],
            "monat": json.loads(plan_row[2]) if plan_row else []
        }

        messages = {
            'uns': {'woche': {}, 'gast': {}, 'monat': {}, 'nope_monat': ''},
            'woche': {}, 'monat': {}, 'gast': {}
        }
        
        for msg_type, t_id, text in messages_rows:
            if msg_type == 'uns_woche': messages['uns']['woche'][t_id] = text
            elif msg_type == 'uns_gast': messages['uns']['gast'][t_id] = text
            elif msg_type == 'uns_monat': messages['uns']['monat'][t_id] = text
            elif msg_type == 'uns_nope_monat': messages['uns']['nope_monat'] = text
            elif msg_type == 'woche': messages['woche'][t_id] = text

        return planung, tasks_dict, messages


if __name__ == '__main__':
    app = DataBase()
