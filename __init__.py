from aqt import gui_hooks, mw
from datetime import date

from .logic.streak_manager import get_streak_manager
from .hooks.toolbar import setup_toolbar
from .ui.streak_popup import open_streak_popup_with_manager
from .ui.review_popup import StreakAnimationPopup

DEBUG_FORCE_ANIMATION_POPUP = False

setup_toolbar()

def calculate_animation_bounds(current_streak):
    prev = max(current_streak - 1, 0)
    curr = max(current_streak, 1)
    return prev, curr

def _on_profile_open():
    try:
        streak_manager = get_streak_manager()
        streak_manager.recalculate_streak()
    except Exception as e:
        print(f"AnkiStreak: Error on profile open: {e}")

gui_hooks.profile_did_open.append(_on_profile_open)

def _on_sync_finish():
    try:
        streak_manager = get_streak_manager()
        streak_manager.update_reviews_on_sync()
    except Exception as e:
        print(f"AnkiStreak: Error after sync: {e}")

gui_hooks.sync_did_finish.append(_on_sync_finish)

def show_streak_animation(*args, **kwargs):
    try:
        streak_manager = get_streak_manager()
        today = date.today()

        reviews_today = streak_manager.get_review_count_for_date(today)
        current_streak = streak_manager.get_current_streak_length()

        should_show = False
        if DEBUG_FORCE_ANIMATION_POPUP:
            should_show = True
        elif reviews_today == 1 and current_streak >= 1:
            should_show = True

        if should_show:
            prev, curr = calculate_animation_bounds(current_streak)
            popup = StreakAnimationPopup(mw)
            popup.show()
    except Exception as e:
        print(f"AnkiStreak: Error showing streak animation: {e}")

gui_hooks.reviewer_did_answer_card.append(show_streak_animation)

def open_streak_popup():
    open_streak_popup_with_manager(mw)
