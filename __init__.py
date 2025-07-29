from aqt import gui_hooks, mw
from datetime import datetime, date

from .logic.streak_manager import get_streak_manager
from .hooks.toolbar import setup_toolbar
from .ui.streak_popup import open_streak_popup_with_manager
from .ui.review_popup import StreakAnimationPopup
from PyQt6.QtCore import QTimer
from .logic.streak_history_manager import StreakHistoryManager

DEBUG_FORCE_ANIMATION_POPUP = True

last_streak_popup_shown_for_day = None
last_study_time_ms = 0

setup_toolbar()

is_closing_profile = False

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
    streak_manager = get_streak_manager()
    total_time_ms = streak_manager.streak_history.get_time_spent_for_date(today)
    today_str = today.strftime("%Y-%m-%d")
    
    return total_time_ms or 0


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
        print(f"current_streak: {current_streak}, new_streak: {new_streak}")
        if new_streak > current_streak:
            popup = StreakAnimationPopup(mw, current_streak, new_streak)
            popup.show()
        
    except Exception as e:
        print(f"AnkiStreak: Error on review: {e}")


def _on_sync_finish():
    global is_closing_profile
    try:
        if is_closing_profile:
            print("AnkiStreak: Sync finished but profile is closing, skipping streak update.")
            return

        streak_manager = get_streak_manager()
        print(f"_on_sync_finish")

        prev_streak = streak_manager.get_current_streak_length()
        print(f"on sync: prev_streak: {prev_streak}")

        def after_recalc():
            streak_manager._update_toolbar()  # Atualiza a toolbar
            new_streak = streak_manager.get_current_streak_length()
            print(f"on sync: new_streak: {new_streak}")
            if new_streak > prev_streak:
                popup = StreakAnimationPopup(mw, prev_streak, new_streak)
                popup.show()        

        # se sincronizou, pode ter histórico novo de outros dispositivos
        # então, atualiza o histórico de dias revisados
        #StreakHistoryManager().import_reviewed_days_with_spinner()
        #print(f"after import_reviewed_days_with_spinner")
        # depois, reprocessa o streak
        streak_manager.recalculate_streak_with_spinner(callback=after_recalc)
        print(f"after recalculate_streak_with_spinner (async)")

        ## Checa o streak depois da sincronização
        #new_streak = streak_manager.get_current_streak_length()
        #print(f"on sync: new_streak: {new_streak}")

        ## Se ganhou streak, mostra o popup
        #if new_streak > prev_streak:
        #    popup = StreakAnimationPopup(mw, prev_streak, new_streak)
        #    popup.show()

    except Exception as e:
        print(f"AnkiStreak: Error after sync: {e}")

gui_hooks.sync_did_finish.append(_on_sync_finish)

gui_hooks.reviewer_did_answer_card.append(_on_review)

def open_streak_popup():
    open_streak_popup_with_manager(mw)

def _on_profile_close():
    global is_closing_profile
    is_closing_profile = True
    
gui_hooks.profile_will_close.append(_on_profile_close)


