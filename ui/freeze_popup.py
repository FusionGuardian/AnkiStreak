import base64
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from aqt import mw
from ..ui.icon import get_base64_icon_data
from ..logic.streak_manager import get_streak_manager

class FreezePopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Streak Freezes")
        self.setFixedSize(500, 120)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        streak_manager = get_streak_manager()
        current = streak_manager.get_streak_freezes_available()
        max_freezes = streak_manager.MAX_STREAK_FREEZES

        freeze_display_layout = QHBoxLayout()
        freeze_display_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(self._load_and_scale_icon(get_base64_icon_data("frozen_streak")))
        icon_label.setFixedSize(64, 64)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        freeze_text_label = QLabel(f"<b>Freezes: {current}/{max_freezes}</b>")
        freeze_text_label.setStyleSheet("font-size: 28px; color: white;")
        freeze_text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        freeze_display_layout.setSpacing(15)
        freeze_display_layout.addWidget(icon_label)
        freeze_display_layout.addWidget(freeze_text_label)

        layout.addLayout(freeze_display_layout)
        layout.addSpacing(10)

        if current < max_freezes:
            reviews = streak_manager.get_reviews_since_last_freeze()
            progress = min(reviews, 1000)

            bar = QProgressBar()
            bar.setMinimum(0)
            bar.setMaximum(1000)
            bar.setValue(progress)
            bar.setTextVisible(True)
            bar.setFormat(f"{reviews}/1000 reviews until next freeze")
            bar.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(bar)

        self.setLayout(layout)

    def _load_and_scale_icon(self, icon_data_uri: str) -> QPixmap:
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(icon_data_uri.split(",")[1]))
        scaled_pixmap = pixmap.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        return scaled_pixmap

def open_freeze_popup(mw=None):
    if mw is None:
        mw = AnkiQt.mw
    popup = FreezePopup(mw)
    popup.exec()
