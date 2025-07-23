from datetime import datetime, timedelta, date
from aqt import mw, gui_hooks, AnkiQt
from .streak_history_manager import StreakHistoryManager
from typing import Union, Any, List
import time

MAX_STREAK_FREEZES = 2
DAYS_PER_FREEZE = 5

class StreakManager:
    _instance = None
    CONFIG_KEY = "my_anki_streak_addon_data"

    def __new__(cls, main_window: AnkiQt = None):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
            cls._instance._initialize(main_window or mw)
        return cls._instance

    def _initialize(self, main_window: AnkiQt):
        self.mw = main_window
        self.MAX_STREAK_FREEZES = MAX_STREAK_FREEZES
        self.DAYS_PER_FREEZE = DAYS_PER_FREEZE
        self.streak_history = StreakHistoryManager()
        self.data = None

        gui_hooks.profile_did_open.append(self.recalculate_streak)
        gui_hooks.reviewer_did_answer_card.append(self.update_streak_for_review)
        gui_hooks.sync_did_finish.append(self.update_reviews_on_sync)

        if self.mw and self.mw.col:
            self.recalculate_streak()

    def _load_data(self):
        default_data = {
            "current_streak_length": 0,
            "last_active_day": None,
            "earned_freeze_dates": [],
            "consumed_freeze_dates": [],
            "days_since_last_freeze": 0,
            "last_sync_reviews_today_count": 0,
            "last_sync_date": None
        }
        data = self.mw.col.get_config(self.CONFIG_KEY, default_data)
        data.setdefault("current_streak_length", 0)
        data.setdefault("last_active_day", None)
        # Handle migration from old 'streak_freezes_available' if it exists
        if "streak_freezes_available" in data and not data.get("earned_freeze_dates"):
            for _ in range(data["streak_freezes_available"]):
                data["earned_freeze_dates"].append(datetime.today().date().strftime("%Y-%m-%d"))
            del data["streak_freezes_available"]

        data.setdefault("earned_freeze_dates", [])
        data.setdefault("consumed_freeze_dates", [])
        data.setdefault("days_since_last_freeze", 0)
        data.setdefault("last_sync_reviews_today_count", 0)
        data.setdefault("last_sync_date", None)

        data["earned_freeze_dates"].sort()
        data["consumed_freeze_dates"].sort()
        return data

    def _save_data(self):
        if self.mw and self.mw.col and self.data:
            self.mw.col.set_config(self.CONFIG_KEY, self.data)

    def add_streak_freeze(self, count: int = 1):
        if self.data is None:
            return        
        
        ts_now = time.time()
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        today = datetime.fromtimestamp(ts_now - offset_seconds)
        today_str = today.strftime("%Y-%m-%d")
        
        for _ in range(count):
            if len(self.data["earned_freeze_dates"]) < self.MAX_STREAK_FREEZES:
                self.data["earned_freeze_dates"].append(today_str)
            else:
                break
        self.data["earned_freeze_dates"].sort()
        self._save_data()
        self._update_toolbar()

    def consume_streak_freeze(self, date_to_cover_str: str) -> bool:
        if self.data is None:
            return False

        date_to_cover_obj = datetime.strptime(date_to_cover_str, "%Y-%m-%d").date()

        found_index = -1
        for i, earned_date_str in enumerate(self.data["earned_freeze_dates"]):
            earned_date_obj = datetime.strptime(earned_date_str, "%Y-%m-%d").date()
            if earned_date_obj <= date_to_cover_obj:
                found_index = i
                break

        if found_index != -1 and date_to_cover_str not in self.data["consumed_freeze_dates"]:
            self.data["earned_freeze_dates"].pop(found_index)  # Remove the used freeze
            self.data["consumed_freeze_dates"].append(date_to_cover_str)
            self.data["consumed_freeze_dates"].sort()
            self._save_data()
            self._update_toolbar()
            return True
        return False

    def _is_day_active(self, check_date: date, actual_reviewed_dates: set, current_consumed_freezes: set) -> bool:
        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in actual_reviewed_dates or date_str in current_consumed_freezes

    def recalculate_streak(self):
        if self.data is None:
            self.data = self._load_data()

        actual_reviewed_dates = self.streak_history.get_streak_days()
        current_consumed_freezes = set(self.data["consumed_freeze_dates"])
      
        ts_now = time.time()
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        today = datetime.fromtimestamp(ts_now - offset_seconds)
                        
        yesterday = today - timedelta(days=1)
        
        today_is_active = self._is_day_active(today, actual_reviewed_dates, current_consumed_freezes)

        calculated_streak = 0
        final_last_active_day_obj = None

        if today_is_active:
            final_last_active_day_obj = today
            calculated_streak = 1
            check_date = yesterday
        else:
            yesterday_is_active = self._is_day_active(yesterday, actual_reviewed_dates, current_consumed_freezes)
            if not yesterday_is_active:
                if self.consume_streak_freeze(yesterday.strftime("%Y-%m-%d")):
                    current_consumed_freezes.add(yesterday.strftime("%Y-%m-%d"))
                    final_last_active_day_obj = yesterday
                    calculated_streak = 1
                    check_date = yesterday - timedelta(days=1)
                else:
                    self.data["current_streak_length"] = 0
                    self.data["last_active_day"] = None
                    self._save_data()
                    self._update_toolbar()
                    return
            else:
                final_last_active_day_obj = yesterday
                calculated_streak = 1
                check_date = yesterday - timedelta(days=1)

        while True:
            date_str = check_date.strftime("%Y-%m-%d")

            is_reviewed = date_str in actual_reviewed_dates
            is_frozen = date_str in current_consumed_freezes

            if is_reviewed or is_frozen:
                calculated_streak += 1
            else:
                break

            check_date -= timedelta(days=1)
            if calculated_streak > 365 * 10:
                break

        total_potential_freezes = calculated_streak // DAYS_PER_FREEZE

        self.data["days_since_last_freeze"] = calculated_streak % DAYS_PER_FREEZE

        consumed_count = len(self.data.get("consumed_freeze_dates", []))
        current_available_in_data = len(self.data.get("earned_freeze_dates", []))
        net_earned_so_far = consumed_count + current_available_in_data

        if total_potential_freezes > net_earned_so_far:
            newly_earned_count = total_potential_freezes - net_earned_so_far
            if (current_available_in_data + newly_earned_count) > self.MAX_STREAK_FREEZES:
                newly_earned_count = self.MAX_STREAK_FREEZES - current_available_in_data
            
            if newly_earned_count > 0:
                self.add_streak_freeze(newly_earned_count)        

        if len(self.data["earned_freeze_dates"]) > self.MAX_STREAK_FREEZES:
            self.data["earned_freeze_dates"].sort()
            self.data["earned_freeze_dates"] = self.data["earned_freeze_dates"][-self.MAX_STREAK_FREEZES:]

        self.data["current_streak_length"] = calculated_streak
        # final_last_active_day_obj represents the most recent day in the streak
        self.data["last_active_day"] = final_last_active_day_obj.strftime(
            "%Y-%m-%d") if final_last_active_day_obj else None
        self._save_data()
        self._update_toolbar()

    def _update_toolbar(self):
        from ..ui.icon import get_base64_icon_data

        if not self.data:
            self.data = self._load_data()

        current_streak = self.data["current_streak_length"]

        if self.has_reviewed_today():
            icon_data_uri = get_base64_icon_data("streak")
            icon_color_style = "color:orange;"
        else:
            icon_data_uri = get_base64_icon_data("grey_streak")
            icon_color_style = "color:#888888;"

        self.mw.streak_button_text = (
            f"<img src='{icon_data_uri}' style='height:20px; vertical-align:middle;' /> "
            f"<span style='font-weight:bold; font-size:16px; position:relative; top:2px; {icon_color_style}'>"
            f"{current_streak}</span>"
        )

        freezes_available = len(self.data["earned_freeze_dates"])

        self.mw.freeze_button_text = (
            f"<img src='{get_base64_icon_data('frozen_streak')}' style='height:20px; vertical-align:middle;' /> "
            f"<span style='font-weight:bold; font-size:16px; position:relative; top:2px; color:#9BDDFD'>"
            f"{freezes_available}</span>"
        )

        if hasattr(self.mw, 'toolbar'):
            self.mw.toolbar.draw()

    def get_current_streak_length(self) -> int:
        if self.data is None:
            self.recalculate_streak()
        return self.data["current_streak_length"] if self.data else 0

    def get_streak_freezes_available(self) -> int:
        if self.data is None:
            self.recalculate_streak()
        return len(self.data["earned_freeze_dates"]) if self.data else 0

    def get_consumed_freeze_dates(self) -> List[str]:
        if self.data is None:
            self.recalculate_streak()
        return self.data["consumed_freeze_dates"] if self.data else []

    def get_earned_freeze_dates(self) -> List[str]:
        if self.data is None:
            self.recalculate_streak()
        return self.data["earned_freeze_dates"] if self.data else []

    def get_last_active_day(self) -> Union[str, None]:
        if self.data is None:
            self.recalculate_streak()
        return self.data["last_active_day"] if self.data else None

    def get_days_since_last_freeze(self) -> int:
        if self.data is None:
            self.recalculate_streak()
        return self.data.get("days_since_last_freeze", 0)

    def has_reviewed_today(self) -> bool:
        
        ts_now = time.time()
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        today = datetime.fromtimestamp(ts_now - offset_seconds)
        today_str = today.strftime("%Y-%m-%d")
        return today_str in self.streak_history.get_streak_days()

    def get_review_count_for_date(self, check_date: date) -> int:
        
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        
        start_dt = datetime(check_date.year, check_date.month, check_date.day)
        end_dt = start_dt + timedelta(days=1)

        start_ts = int(start_dt.timestamp() + offset_seconds)
        end_ts = int(end_dt.timestamp() + offset_seconds)
        
        query = "select count(*) from revlog where id  >= ? and id  < ?"
        count = self.mw.col.db.scalar(query,  start_ts * 1000,  end_ts * 1000)

        return count

    def get_review_details_for_date(self, check_date: date) -> dict:
        if not self.mw or not self.mw.col:
            return {}
        
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        
        start_dt = datetime(check_date.year, check_date.month, check_date.day)
        end_dt = start_dt + timedelta(days=1)

        start_ts = int(start_dt.timestamp() + offset_seconds)
        end_ts = int(end_dt.timestamp() + offset_seconds)
               
        query = """
                SELECT d.name, \
                       COUNT(r.id), \
                       SUM(r.time)
                FROM revlog r \
                         JOIN \
                     cards c ON r.cid = c.id \
                         JOIN \
                     decks d ON c.did = d.id
                WHERE r.id  >= ? \
                  AND r.id  < ?
                GROUP BY d.name
                ORDER BY d.name \
                """
        results = self.mw.col.db.all(query, start_ts * 1000, end_ts * 1000)
           
        details = {}
        for deck_name, review_count, time_spent_ms in results:
            details[deck_name] = {
                "reviews": review_count,
                "time_spent_ms": time_spent_ms
            }
        return details

    def update_reviews_on_sync(self):
        self.recalculate_streak()

    def update_streak_for_review(self, *args: Any, **kwargs: Any):
        self.recalculate_streak()

_global_streak_manager_instance = None

def get_streak_manager() -> StreakManager:
    global _global_streak_manager_instance
    if _global_streak_manager_instance is None:
        try:
            _global_streak_manager_instance = StreakManager(mw)
        except NameError:
            _global_streak_manager_instance = StreakManager(None)
    return _global_streak_manager_instance
