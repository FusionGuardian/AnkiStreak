from datetime import datetime, timedelta, date
from aqt import mw, gui_hooks, AnkiQt
from .streak_history_manager import StreakHistoryManager
from typing import Union, Any

MAX_STREAK_FREEZES_CONSTANT = 2

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
        self.MAX_STREAK_FREEZES = MAX_STREAK_FREEZES_CONSTANT
        self.streak_history = StreakHistoryManager()
        self.data = None

        gui_hooks.profile_did_open.append(self.recalculate_streak)
        gui_hooks.reviewer_did_answer_card.append(self.update_streak_for_review)

    def _load_data(self):
        default_data = {
            "current_streak_length": 0,
            "last_active_day": None,
            "streak_freezes_available": self.MAX_STREAK_FREEZES,
            "consumed_freeze_dates": [],
            "reviews_since_last_freeze": 0,
            "last_sync_reviews_today_count": 0,
            "last_sync_date": None
        }
        if self.mw and self.mw.col:
            data = self.mw.col.get_config(self.CONFIG_KEY, default_data)
            data.setdefault("current_streak_length", 0)
            data.setdefault("last_active_day", None)
            data.setdefault("streak_freezes_available", self.MAX_STREAK_FREEZES)
            data.setdefault("consumed_freeze_dates", [])
            data.setdefault("reviews_since_last_freeze", 0)
            data.setdefault("last_sync_reviews_today_count", 0)
            data.setdefault("last_sync_date", None)
            data["consumed_freeze_dates"].sort()
            return data
        else:
            print("AnkiStreak: Warning: Collection not available during _load_data. Returning default.")
            return default_data

    def _save_data(self):
        if self.mw and self.mw.col:
            self.mw.col.set_config(self.CONFIG_KEY, self.data)
        else:
            print("AnkiStreak: Warning: Attempted to save data before collection was loaded.")

    def add_streak_freeze(self, count: int = 1):
        if self.data is None:
            print("AnkiStreak: Warning: Data not loaded yet. Cannot add streak freeze.")
            return

        self.data["streak_freezes_available"] = min(self.data["streak_freezes_available"] + count,
                                                    self.MAX_STREAK_FREEZES)
        self._save_data()

    def consume_streak_freeze(self, date_str: str):
        if self.data is None:
            print("AnkiStreak: Warning: Data not loaded yet. Cannot consume streak freeze.")
            return False

        if self.data["streak_freezes_available"] > 0 and date_str not in self.data["consumed_freeze_dates"]:
            self.data["streak_freezes_available"] -= 1
            self.data["consumed_freeze_dates"].append(date_str)
            self.data["consumed_freeze_dates"].sort()
            self._save_data()
            return True
        return False

    def recalculate_streak(self):
        if self.data is None:
            self.data = self._load_data()

        actual_reviewed_dates = self.streak_history.get_streak_days()
        current_consumed_freezes = set(self.data["consumed_freeze_dates"])

        today = datetime.today().date()
        yesterday = today - timedelta(days=1)

        today_is_active = today.strftime("%Y-%m-%d") in actual_reviewed_dates or \
                          today.strftime("%Y-%m-%d") in current_consumed_freezes

        calculated_streak = 0
        last_active_day_obj = None

        start_date_for_calc = None
        if today_is_active:
            start_date_for_calc = today
        else:
            yesterday_is_active = yesterday.strftime("%Y-%m-%d") in actual_reviewed_dates or \
                                  yesterday.strftime("%Y-%m-%d") in current_consumed_freezes
            if yesterday_is_active:
                start_date_for_calc = yesterday
            else:
                self.data["current_streak_length"] = 0
                self.data["last_active_day"] = None
                self._save_data()
                return

        check_date = start_date_for_calc
        while True:
            date_str = check_date.strftime("%Y-%m-%d")

            is_reviewed = date_str in actual_reviewed_dates
            is_frozen = date_str in current_consumed_freezes

            if is_reviewed or is_frozen:
                calculated_streak += 1
                last_active_day_obj = check_date
            else:
                if self.data["streak_freezes_available"] > 0:
                    self.consume_streak_freeze(date_str)
                    current_consumed_freezes.add(date_str)
                    calculated_streak += 1
                    last_active_day_obj = check_date
                else:
                    break

            check_date -= timedelta(days=1)
            if (start_date_for_calc - check_date).days > 365 * 10:
                print("AnkiStreak: Streak recalculation hit safety limit (10 years).")
                break

        self.data["current_streak_length"] = calculated_streak
        self.data["last_active_day"] = last_active_day_obj.strftime("%Y-%m-%d") if last_active_day_obj else None
        self._save_data()

    def get_current_streak_length(self) -> int:
        if self.data is None:
            self.recalculate_streak()
        return self.data["current_streak_length"] if self.data else 0

    def get_streak_freezes_available(self) -> int:
        if self.data is None:
            self.recalculate_streak()
        return self.data["streak_freezes_available"] if self.data else 0

    def get_consumed_freeze_dates(self) -> list[str]:
        if self.data is None:
            self.recalculate_streak()
        return self.data["consumed_freeze_dates"] if self.data else []

    def get_last_active_day(self) -> Union[str, None]:
        if self.data is None:
            self.recalculate_streak()
        return self.data["last_active_day"] if self.data else None

    def get_reviews_since_last_freeze(self) -> int:
        if self.data is None:
            self.recalculate_streak()
        return self.data.get("reviews_since_last_freeze", 0)

    def has_reviewed_today(self) -> bool:
        today_str = datetime.today().date().strftime("%Y-%m-%d")
        return today_str in self.streak_history.get_streak_days()

    def get_review_count_for_date(self, check_date: date) -> int:
        start_dt = datetime(check_date.year, check_date.month, check_date.day)
        end_dt = start_dt + timedelta(days=1)

        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())

        query = "select count(*) from revlog where id >= ? and id < ?"
        count = self.mw.col.db.scalar(query, start_ts * 1000, end_ts * 1000)

        return count

    def get_review_details_for_date(self, check_date: date) -> dict:
        if not self.mw or not self.mw.col:
            return {}

        start_dt = datetime(check_date.year, check_date.month, check_date.day)
        end_dt = start_dt + timedelta(days=1)

        start_ts = int(start_dt.timestamp())
        end_ts = int(end_dt.timestamp())

        query = """
            SELECT
                d.name,
                COUNT(r.id),
                SUM(r.time)
            FROM
                revlog r
            JOIN
                cards c ON r.cid = c.id
            JOIN
                decks d ON c.did = d.id
            WHERE
                r.id >= ? AND r.id < ?
            GROUP BY
                d.name
            ORDER BY
                d.name
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
        if self.data is None:
            self.data = self._load_data()

        today = datetime.today().date()
        today_str = today.strftime("%Y-%m-%d")

        current_reviews_today = self.get_review_count_for_date(today)

        last_sync_date_str = self.data.get("last_sync_date")
        last_sync_reviews_today = self.data.get("last_sync_reviews_today_count", 0)

        if last_sync_date_str == today_str:
            new_reviews_from_sync = current_reviews_today - last_sync_reviews_today
            if new_reviews_from_sync > 0:
                self.data["reviews_since_last_freeze"] += new_reviews_from_sync
        else:
            self.data["reviews_since_last_freeze"] += current_reviews_today

        self.data["last_sync_date"] = today_str
        self.data["last_sync_reviews_today_count"] = current_reviews_today
        self._save_data()

        if self.data["reviews_since_last_freeze"] >= 1000:
            self.add_streak_freeze(1)
            self.data["reviews_since_last_freeze"] = 0
            self._save_data()

    def update_streak_for_review(self, *args: Any, **kwargs: Any):
        if self.data is None:
            self.data = self._load_data()
            print("AnkiStreak: Data loaded for update_streak_for_review due to prior uninitialized access.")

        today_str = datetime.today().date().strftime("%Y-%m-%d")

        self.streak_history.add_day(today_str)

        self.data["reviews_since_last_freeze"] = self.data.get("reviews_since_last_freeze", 0) + 1
        if self.data["reviews_since_last_freeze"] >= 1000:
            self.add_streak_freeze(1)
            self.data["reviews_since_last_freeze"] = 0

        self.recalculate_streak()

_global_streak_manager_instance = None

def get_streak_manager() -> StreakManager:
    global _global_streak_manager_instance
    if _global_streak_manager_instance is None:
        try:
            _global_streak_manager_instance = StreakManager(mw)
        except NameError:
            print("AnkiStreak: Warning: 'mw' not available yet for StreakManager initialization. "
                  "Deferring full setup until profile_did_open hook.")
            _global_streak_manager_instance = StreakManager(None)
    return _global_streak_manager_instance