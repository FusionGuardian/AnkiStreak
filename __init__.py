from aqt import gui_hooks, mw
from datetime import date

from .logic.streak_manager import get_streak_manager
from .hooks.toolbar import setup_toolbar
from .ui.streak_popup import open_streak_popup_with_manager
from .ui.review_popup import StreakAnimationPopup

from PyQt6.QtCore import QTimer

DEBUG_FORCE_ANIMATION_POPUP = True

last_streak_popup_shown_for_day = None
last_study_time_ms = 0

setup_toolbar()

def get_today_study_time_ms():
    #col = mw.col
    #cutoff = col.sched.day_cutoff
    #start = cutoff - 86400
    #end = cutoff
    #total_ms = col.db.scalar(
    #    "SELECT SUM(time) FROM revlog WHERE id >= ? AND id < ?",
    #    start * 1000, end * 1000
    #)
    #return total_ms or 0

    ts_now = time.time()
    #--------------------------------------------
    # abaixo está comentado porque o método já faz a tratativa do cuttoff
    #--------------------------------------------
    #cutoff_timestamp = mw.col.sched.day_cutoff 
    #cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
    #offset_seconds = cutoff_datetime.hour * 3600 + cutoff_datetime.minute * 60 + cutoff_datetime.second
    today = datetime.fromtimestamp(ts_now)
    total_time_ms = self.streak_history.get_time_spent_for_date(today)
    today_str = today.strftime("%Y-%m-%d")
    
    return total_ms or 0


def calculate_animation_bounds(current_streak):
    prev = max(current_streak, 0)
    curr = max(current_streak  + 1, 1)
    return prev, curr

def _on_profile_open():
    try:
        print(f"_on_profile_open do __init__.py")
        streak_manager = get_streak_manager()
        if not mw.pm.profile.get("syncKey"):
            QTimer.singleShot(100, streak_manager.recalculate_streak_with_spinner)
    except Exception as e:
        print(f"AnkiStreak: Error on profile open: {e}")

gui_hooks.profile_did_open.append(_on_profile_open)

def _on_review(*args, **kwargs):
    try:
        streak_manager = get_streak_manager()
        print(f"_on_review")
        current_streak, new_streak = streak_manager.check_review_streak_change()
        if new_streak > current_streak:
            popup = StreakAnimationPopup(mw, current_streak, new_streak)
            popup.show()
        
    except Exception as e:
        print(f"AnkiStreak: Error on review: {e}")


def _on_sync_finish():
    try:
        streak_manager = get_streak_manager()
        print(f"_on_sync_finish")
        streak_manager.recalculate_streak_with_spinner()
    except Exception as e:
        print(f"AnkiStreak: Error after sync: {e}")

gui_hooks.sync_did_finish.append(_on_sync_finish)

gui_hooks.reviewer_did_answer_card.append(_on_review)

def open_streak_popup():
    open_streak_popup_with_manager(mw)

def _on_profile_close():
    try:
        streak_manager = get_streak_manager()
        streak_manager.cleanup_on_close()
    except Exception as e:
        print(f"AnkiStreak: Error on profile close: {e}")

gui_hooks.profile_will_close.append(_on_profile_close)


