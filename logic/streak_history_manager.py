import os
import json
from datetime import datetime, timedelta, date
from aqt import mw, gui_hooks
from typing import Set
import locale  # Import necessário para localização


MINIMUM_TIME_SPENT = 14 # minutos

class StreakHistoryManager:
    FILENAME = "streak_history.json"

    def __init__(self):
        print(f"__init__ do StreakHistoryManager.py")
        self.path = os.path.join(mw.pm.addonFolder(), "addon", self.FILENAME)
        self.days = set()
        self.load()

        gui_hooks.profile_did_open.append(self._on_profile_open)

    def _on_profile_open(self):
        print(f"_on_profile_open do StreakHistoryManager.py")
        #self.import_reviewed_days_from_log()
        self.save()

    def load(self):
        try:
            print(f"load do StreakHistoryManager.py")
            if os.path.exists(self.path):
                with open(self.path, "r") as f:
                    self.days = set(json.load(f))
        except Exception as e:
            print(f"Error loading streak history from {self.path}: {e}")
            self.days = set()

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as f:
                json.dump(sorted(list(self.days)), f)
        except Exception as e:
            print(f"Error saving streak history to {self.path}: {e}")

    def get_last_day(self) -> str:
        if not self.days:
            return None
        return max(self.days)
        
    def add_day(self, date_str: str):
        if date_str not in self.days:
            self.days.add(date_str)
            self.save()

    def get_time_spent_for_date(self, check_date: date) -> int:
        if not mw or not mw.col:
            print("AnkiStreak: Collection not available, skipping get_time_spent_for_date.")
            return
        
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        
        start_dt = datetime(check_date.year, check_date.month, check_date.day)
        end_dt = start_dt + timedelta(days=1)

        start_ts = int(start_dt.timestamp() + offset_seconds)
        end_ts = int(end_dt.timestamp() + offset_seconds)
        
        query = "select SUM(time) from revlog where id  >= ? and id  < ?"
        time_spent_ms = mw.col.db.scalar(query,  start_ts * 1000,  end_ts * 1000)

        return time_spent_ms

    def import_reviewed_days_from_log(self, progress_callback=None):
        try:
            if not mw.col:
                print("AnkiStreak: Collection not available for revlog import (unexpected).")
                return
            
            print(f"import_reviewed_days_from_log do StreakHistoryManager.py")

            # Configura a localização para o formato de data do sistema
            locale.setlocale(locale.LC_TIME, '')

            last_day = self.get_last_day()
            if last_day:
                last_dt = datetime.strptime(last_day, "%Y-%m-%d")
                cutoff_timestamp = mw.col.sched.day_cutoff
                cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
                offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
                start_ts = int(last_dt.timestamp() + offset_seconds) * 1000
            else:
                start_ts = 0

            query = "SELECT id FROM revlog WHERE id > ?"
            result = mw.col.db.all(query, start_ts)
            current_days_count = len(self.days)

            for revlog_id, in result:
                print(f"import_reviewed_days_from_log analisando... revlog_id: {revlog_id}")           
                ts = revlog_id / 1000            
                cutoff_timestamp = mw.col.sched.day_cutoff 
                cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
                offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second          
                date_obj = datetime.fromtimestamp(ts - offset_seconds)

                # Formata a data no formato localizado                
                date_str = date_obj.strftime("%Y-%m-%d")  # %x usa o formato de data localizado                

                if progress_callback:
                    locale.setlocale(locale.LC_TIME, '')  # Define a localização do sistema
                    date_locale_str = date_obj.strftime("%x")
                    progress_callback(f"({date_locale_str})")

                total_time_ms = self.get_time_spent_for_date(date_obj)
                total_time_min = round(total_time_ms / 60000, 1)

                if total_time_min < MINIMUM_TIME_SPENT:
                    continue

                if date_str not in self.days:
                    self.days.add(date_str)

            added = len(self.days) - current_days_count
            if added > 0:
                print(f"[StreakHistory] Added {added} new day(s) from review log.")

            print(f"import_reviewed_days_from_log concluído")
        except Exception as e:
            print(f"AnkiStreak: Error in get_time_spent_for_date: {e}")
            return 0
            
    def get_streak_days(self) -> Set[str]:
        return self.days
