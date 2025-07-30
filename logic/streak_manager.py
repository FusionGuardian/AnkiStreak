from PyQt6.QtWidgets import QProgressDialog, QApplication
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtCore import Qt as QtCoreQt
from aqt import mw
from datetime import datetime, timedelta, date
from .streak_history_manager import StreakHistoryManager
from typing import Union, List
import time
import logging

MAX_STREAK_FREEZES = 2
DAYS_PER_FREEZE = 5

class StreakManager:
    _instance = None
    CONFIG_KEY = "my_anki_streak_addon_data"

    def __new__(cls, main_window=None):
        if cls._instance is None:
            cls._instance = super(cls, cls).__new__(cls)
            cls._instance._initialize(main_window or mw)
        return cls._instance

    def _initialize(self, main_window):
        self.mw = main_window
        self.MAX_STREAK_FREEZES = MAX_STREAK_FREEZES
        self.DAYS_PER_FREEZE = DAYS_PER_FREEZE
        self.streak_history = StreakHistoryManager()
        self.data = None

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
                logging.info("[StreakManager] Ganhou um freeze no dia %s", today_str)
            else:
                break
        self.data["earned_freeze_dates"].sort()
        logging.info("[StreakManager] Freezes disponíveis após ganhar: %s", self.data['earned_freeze_dates'])
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

        logging.info("[StreakManager] Tentando consumir freeze para %s. Freezes disponíveis: %s", date_to_cover_str, self.data['earned_freeze_dates'])
        if found_index != -1 and date_to_cover_str not in self.data["consumed_freeze_dates"]:
            self.data["earned_freeze_dates"].pop(found_index)  # Remove the used freeze
            self.data["consumed_freeze_dates"].append(date_to_cover_str)
            self.data["consumed_freeze_dates"].sort()
            self._save_data()
            self._update_toolbar()
            return True
        logging.info("[StreakManager] Não conseguiu consumir freeze para %s", date_to_cover_str)
        return False

    def _is_day_active(self, check_date: date, actual_reviewed_dates: set, current_consumed_freezes: set) -> bool:
        date_str = check_date.strftime("%Y-%m-%d")
        return date_str in actual_reviewed_dates or date_str in current_consumed_freezes

    def recalculate_streak_with_spinner(self, callback=None):
        if not self.mw or not self.mw.col:
            logging.info("AnkiStreak: Main window or collection is closed, skipping progress bar.")
            return {}

        from ..ui.progress_runner import ProgressRunner

        ProgressRunner(self.mw).run_with_progress(            
            "Analyzing history...",
            self._calculate_streak_only,
            callback or self._update_toolbar
        )

    def _update_toolbar(self):
        from ..ui.icon import get_base64_icon_data

        logging.info("[_update_toolbar] Iniciando atualização")

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
        logging.info("[AnkiStreak] Toolbar atualizada! Streak: %s", self.data["current_streak_length"])

    def get_current_streak_length(self) -> int:
        if self.data is None:
            self.data = self._load_data()
        return self.data["current_streak_length"] if self.data else 0

    def get_consumed_freeze_dates(self) -> List[str]:
        if self.data is None:
            self.data = self._load_data()
        return self.data["consumed_freeze_dates"] if self.data else []

    def has_reviewed_today(self) -> bool:
        try:
            ts_now = time.time()
            cutoff_timestamp = mw.col.sched.day_cutoff 
            cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
            offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
            today = datetime.fromtimestamp(ts_now - offset_seconds)
            today_str = today.strftime("%Y-%m-%d")
            return today_str in self.streak_history.get_streak_days()
        except Exception as e:
            logging.error("AnkiStreak: Error in has_reviewed_today: %s", e)
            return False

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

    def _calculate_streak_only(self, progress_callback=None):
        try:
            if self.data is None:
                self.data = self._load_data()



            ## Atualiza o histórico a partir do banco (sincroniza com outros dispositivos)
            self.streak_history.import_reviewed_days_from_log(progress_callback=progress_callback)
            self.streak_history.save()
            
            # aqui o sistema roda e recalcula todo o streak e os freezes, dos ultimos 10 anos
            # baseado nos dias ativos que estão no StreakHistoryManager
            ts_now = time.time()
            cutoff_timestamp = mw.col.sched.day_cutoff 
            cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
            offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
            today = datetime.fromtimestamp(ts_now - offset_seconds)
            today_str = today.strftime("%Y-%m-%d")

            actual_reviewed_dates = self.streak_history.get_streak_days()            
            self.data["earned_freeze_dates"] = []
            self.data["consumed_freeze_dates"] = []
            current_consumed_freezes = set()

            days_to_check = []
            for i in range(365 * 10):
                check_date = today - timedelta(days=365 * 10 - 1 - i)
                days_to_check.append(check_date)

            calculated_streak = 0
            streak_counter = 0
            last_active_day = None
            self.data["earned_freeze_dates"] = []
            self.data["consumed_freeze_dates"] = []
            current_consumed_freezes = set()

            consecutive_bad_days = 0  # Para controlar logs repetitivos

            for check_date in days_to_check:
                date_str = check_date.strftime("%Y-%m-%d")
                is_reviewed = date_str in actual_reviewed_dates
                is_frozen = date_str in current_consumed_freezes

                if is_reviewed or is_frozen:
                    if consecutive_bad_days > 0:                    
                        consecutive_bad_days = 0                
                    calculated_streak += 1
                    streak_counter += 1
                    last_active_day = check_date
                    if streak_counter % DAYS_PER_FREEZE == 0:
                        self.data["earned_freeze_dates"].append(date_str)
                        if len(self.data["earned_freeze_dates"]) > self.MAX_STREAK_FREEZES:
                            self.data["earned_freeze_dates"] = self.data["earned_freeze_dates"][-self.MAX_STREAK_FREEZES:]                    
                else:
                    found_index = -1
                    for i, earned_date_str in enumerate(self.data["earned_freeze_dates"]):
                        earned_date_obj = datetime.strptime(earned_date_str, "%Y-%m-%d").date()
                        if earned_date_obj <= check_date.date():
                            found_index = i
                            break
                    if found_index != -1 and date_str not in self.data["consumed_freeze_dates"]:
                        consumed_freeze_date = self.data["earned_freeze_dates"][found_index]
                        self.data["consumed_freeze_dates"].append(date_str)
                        current_consumed_freezes.add(date_str)
                        self.data["earned_freeze_dates"].pop(found_index)
                        calculated_streak += 1
                        streak_counter += 1
                        last_active_day = check_date
                        if consecutive_bad_days > 0:
                            consecutive_bad_days = 0
                    else:
                        if streak_counter > 0:
                            consecutive_bad_days += 1
                            prev_bad_day = date_str
                            calculated_streak = 0
                            streak_counter = 0
                            last_active_day = None
                            current_consumed_freezes = set()

            self.data["earned_freeze_dates"].sort()
            self.data["consumed_freeze_dates"].sort()
            self.data["current_streak_length"] = calculated_streak
            self.data["last_active_day"] = last_active_day.strftime("%Y-%m-%d") if last_active_day else None
            self.data["days_since_last_freeze"] = streak_counter % DAYS_PER_FREEZE

            self._save_data()
        except Exception as e:
            logging.error("AnkiStreak: Error in _calculate_streak_only: %s", e)
            return 0

    def _show_streak_popup(self):
        from ..ui.review_popup import StreakAnimationPopup  # Import correto!
        current_streak = self.get_current_streak_length()
        popup = StreakAnimationPopup(self.mw, current_streak - 1, current_streak )
        popup.show()

    def check_review_streak_change(self):
        if self.data is None:
            self.data = self._load_data()

        current_streak = 0
        new_streak = 0

        ts_now = time.time()
        cutoff_timestamp = mw.col.sched.day_cutoff 
        cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
        offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
        today = datetime.fromtimestamp(ts_now - offset_seconds)
        total_time_ms = self.streak_history.get_time_spent_for_date(today)
        today_str = today.strftime("%Y-%m-%d")

        from .streak_history_manager import MINIMUM_TIME_SPENT
        
        actual_reviewed_dates = self.streak_history.get_streak_days()
        logging.info("check_review_streak_change disparado")
        #logging.info("[AnkiStreak] Dias ativos retornados pelo StreakHistoryManager antes: %s", actual_reviewed_dates)
        logging.info("total_time_ms:%s", total_time_ms)
        minimumTimeSpent = MINIMUM_TIME_SPENT * 60_000
        logging.info("minimumTimeSpent:%s", minimumTimeSpent)
        if total_time_ms and total_time_ms >= MINIMUM_TIME_SPENT * 60_000:
            logging.info("ok, estudei o minimo")
            if today_str not in actual_reviewed_dates:
                logging.info("ok, o dia de hoje não estava na lista")
                current_streak = len(self.streak_history.days)
                self.streak_history.days.add(today_str)
                self.streak_history.save()
                new_streak = len(self.streak_history.days)

        return current_streak, new_streak
                
_global_streak_manager_instance = None

def get_streak_manager() -> StreakManager:
    global _global_streak_manager_instance
    if _global_streak_manager_instance is None:
        try:
            _global_streak_manager_instance = StreakManager(mw)
        except NameError:
            _global_streak_manager_instance = StreakManager(None)
    return _global_streak_manager_instance
