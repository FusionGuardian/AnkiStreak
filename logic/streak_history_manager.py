import os
import json
from datetime import datetime
from aqt import mw, gui_hooks
from typing import Set
#from anki.consts import DAY_SECS


class StreakHistoryManager:
    FILENAME = "streak_history.json"

    def __init__(self):
        self.path = os.path.join(mw.pm.addonFolder(), "addon", self.FILENAME)
        self.days = set()
        self.load()

        gui_hooks.profile_did_open.append(self._on_profile_open)

    def _on_profile_open(self):
        self.import_reviewed_days_from_log()
        self.save()

    def load(self):
        try:
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

    def import_reviewed_days_from_log(self):
        if not mw.col:
            print("AnkiStreak: Collection not available for revlog import (unexpected).")
            return

        result = mw.col.db.all("SELECT id FROM revlog")
        current_days_count = len(self.days)

        for revlog_id, in result:           
            ts = revlog_id / 1000            
            cutoff_timestamp = mw.col.sched.day_cutoff 
            cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
            offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
            
            #anki_day = int((ts - offset_seconds) // 86400)
            #date_str = datetime.fromtimestamp(anki_day * 86400).date().isoformat()
            
            #date_obj = datetime.fromtimestamp(ts - offset_seconds)
            date_obj1 = datetime.fromtimestamp(ts)
            date_obj2 = datetime.fromtimestamp(ts - offset_seconds)
            #date_obj2 = mw.col.sched.date_for_timestamp(ts).isoformat()
            #date_obj3 = mw.col.sched.date_for_timestamp(revlog_id).isoformat()
            date_str = date_obj2.strftime("%Y-%m-%d")
            #date_str = mw.col.sched.date_for_timestamp(ts).isoformat()
            
            # DEBUG:
            #print(f"[StreakHist] revlog_id={revlog_id} ts={ts:.0f} cutoff={cutoff} "
            #f"-> date_obj={date_obj.isoformat()} date_str={date_str}")
            
            #[StreakHist] revlog_id=1749445948000 ts=1749445948 cutoff=1753254000 date_obj=2025-06-08T22:12:28 date_obj1=2025-06-09T02:12:28 date_obj2=2025-06-08T22:12:28 -> date_str=2025-06-09
            
            if revlog_id > 1740366000000 and revlog_id < 1740452400000:
                # DEBUG:
                print(f"[StreakHist] revlog_id={revlog_id} ts={ts:.0f} cutoff={cutoff_timestamp} date_obj1={date_obj1.isoformat()} date_obj2={date_obj2.isoformat()}  "
                    f"-> date_str={date_str}")
          
            if date_str not in self.days:
                self.days.add(date_str)

        added = len(self.days) - current_days_count
        if added > 0:
            print(f"[StreakHistory] Added {len(self.days) - current_days_count} new day(s) from review log.")

    def get_streak_days(self) -> Set[str]:
        return self.days
