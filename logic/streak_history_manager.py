import os
import json
from datetime import datetime, timedelta, date
from aqt import mw, gui_hooks
from typing import Set

MINIMUM_TIME_SPENT = 8

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

    def add_day(self, date_str: str):
        if date_str not in self.days:
            self.days.add(date_str)
            self.save()

    def get_time_spent_for_date(self, check_date: date) -> int:
        
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

    def import_reviewed_days_from_log(self):
        if not mw.col:
            print("AnkiStreak: Collection not available for revlog import (unexpected).")
            return
        
        print(f"import_reviewed_days_from_log do StreakHistoryManager.py")

        result = mw.col.db.all("SELECT id FROM revlog")
        current_days_count = len(self.days)

        for revlog_id, in result:           
            ts = revlog_id / 1000            
            cutoff_timestamp = mw.col.sched.day_cutoff 
            cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
            offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second          
            date_obj = datetime.fromtimestamp(ts - offset_seconds)
            date_str = date_obj.strftime("%Y-%m-%d")
                
            total_time_ms = self.get_time_spent_for_date(date_obj)
            total_time_min = round(total_time_ms / 60000, 1)

            if total_time_min < MINIMUM_TIME_SPENT:
                continue

            if date_str not in self.days:
                self.days.add(date_str)

        added = len(self.days) - current_days_count
        if added > 0:
            print(f"[StreakHistory] Added {len(self.days) - current_days_count} new day(s) from review log.")

    def get_streak_days(self) -> Set[str]:
        return self.days
