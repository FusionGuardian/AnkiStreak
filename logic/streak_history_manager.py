import os
import json
from datetime import datetime
from aqt import mw, gui_hooks
from typing import Set
from anki.consts import DAY_SECS


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
            cutoff = mw.col.sched.dayCutoff
            date_obj = datetime.fromtimestamp(ts + cutoff)
            date_str = date_obj.strftime("%Y-%m-%d")
            if date_str not in self.days:
                self.days.add(date_str)

        added = len(self.days) - current_days_count
        if added > 0:
            print(f"[StreakHistory] Added {len(self.days) - current_days_count} new day(s) from review log.")

    def get_streak_days(self) -> Set[str]:
        return self.days
