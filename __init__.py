from aqt import gui_hooks, mw
from datetime import datetime, date

from .logic.streak_manager import get_streak_manager
from .hooks.toolbar import setup_toolbar
from .ui.streak_popup import open_streak_popup_with_manager
from .ui.review_popup import StreakAnimationPopup
from PyQt6.QtCore import QTimer
from .logic.streak_history_manager import StreakHistoryManager

import logging
import os

# Configuração do modo debug/log
DEBUG_MODE = True
logging.basicConfig(level=logging.INFO if DEBUG_MODE else logging.CRITICAL)

setup_toolbar()

is_closing_profile = False

def _on_profile_open():
    try:
        logging.info("_on_profile_open do __init__.py")
        streak_manager = get_streak_manager()
        if not mw.pm.profile.get("syncKey"):
            QTimer.singleShot(100, streak_manager.recalculate_streak_with_spinner)
    except Exception as e:
        logging.error(f"AnkiStreak: Error on profile open: {e}")

gui_hooks.profile_did_open.append(_on_profile_open)

def _on_review(*args, **kwargs):
    try:
        streak_manager = get_streak_manager()
        logging.info("_on_review")
        current_streak, new_streak = streak_manager.check_review_streak_change()
        logging.info(f"current_streak: {current_streak}, new_streak: {new_streak}")
        if new_streak > current_streak:
            popup = StreakAnimationPopup(mw, current_streak, new_streak)
            popup.show()
    except Exception as e:
        logging.error(f"AnkiStreak: Error on review: {e}")

def _on_sync_finish():
    global is_closing_profile
    try:
        if is_closing_profile:
            logging.info("AnkiStreak: Sync finished but profile is closing, skipping streak update.")
            return

        streak_manager = get_streak_manager()
        logging.info("_on_sync_finish")

        prev_streak = streak_manager.get_current_streak_length()
        logging.info(f"on sync: prev_streak: {prev_streak}")

        def after_recalc():
            streak_manager._update_toolbar()
            new_streak = streak_manager.get_current_streak_length()
            logging.info(f"on sync: new_streak: {new_streak}")
            if new_streak > prev_streak:
                popup = StreakAnimationPopup(mw, prev_streak, new_streak)
                popup.show()

        streak_manager.recalculate_streak_with_spinner(callback=after_recalc)
        logging.info("after recalculate_streak_with_spinner (async)")

    except Exception as e:
        logging.error(f"AnkiStreak: Error after sync: {e}")

gui_hooks.sync_did_finish.append(_on_sync_finish)
gui_hooks.reviewer_did_answer_card.append(_on_review)

def _on_profile_close():
    global is_closing_profile
    is_closing_profile = True

gui_hooks.profile_will_close.append(_on_profile_close)


