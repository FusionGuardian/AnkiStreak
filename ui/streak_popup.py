import base64
import PyQt6.QtCore as QtCore
from PyQt6.QtCore import Qt as QtCoreQt, QSize
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtWidgets import (
    QDialog, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QWidget
)

from ..logic.streak_manager import get_streak_manager
from .calendar_widget import CalendarWidget
from .icon import get_base64_icon_data

class StreakPopup(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.streak_manager = get_streak_manager()

        self.setWindowTitle("Streak Info")
        self.setWindowFlags(self.windowFlags() | QtCoreQt.WindowType.FramelessWindowHint)
        self.setWindowModality(QtCoreQt.WindowModality.ApplicationModal)
        self.setFixedSize(520, 700)
        self.drag_pos = None

        streak = self.streak_manager.get_current_streak_length()

        self.header_widget = QWidget()
        self.header_widget.setFixedHeight(30)
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(8, 0, 12, 0)

        close_button = QPushButton("✕")
        close_button.setFixedSize(24, 24)
        close_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-weight: bold;
                font-size: 14px;
                color: white;
            }
            QPushButton:hover {
                color: #dddddd;
            }
        """)
        close_button.clicked.connect(self.close)

        center_label = QLabel("Streak")
        center_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        center_label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)

        share_button = QPushButton()
        share_button.setFixedSize(28, 28) # Slightly smaller
        share_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                /* Removed background-color change on hover */
                border-radius: 5px;
            }
        """)
        share_icon_pixmap = QPixmap()
        share_icon_pixmap.loadFromData(base64.b64decode(get_base64_icon_data("share").split(",")[1]))
        share_button.setIcon(QIcon(share_icon_pixmap))
        share_button.setIconSize(QSize(24, 24)) # Set icon size explicitly
        share_button.clicked.connect(self.open_share_window)

        header_layout.addWidget(close_button, alignment=QtCoreQt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        header_layout.addWidget(center_label)
        header_layout.addStretch()
        header_layout.addWidget(share_button, alignment=QtCoreQt.AlignmentFlag.AlignRight)
        self.header_widget.setLayout(header_layout)

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: white;") # Simpler styling for a solid line

        top_widget = QWidget()
        top_widget.setFixedHeight(120)

        top_layout = QVBoxLayout()
        top_layout.setContentsMargins(0, 4, 0, 0)
        top_layout.setSpacing(0)

        content_layout = QHBoxLayout()
        content_layout.setAlignment(QtCoreQt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setContentsMargins(12, 0, 0, 0)
        text_layout.setAlignment(QtCoreQt.AlignmentFlag.AlignTop | QtCoreQt.AlignmentFlag.AlignLeft)

        self.streak_number_label = QLabel(str(self.streak_manager.get_current_streak_length()))
        self.streak_number_label.setFont(QFont("Arial", 52, QFont.Weight.Bold))

        day_label = QLabel("day streak!")
        day_label.setFont(QFont("Arial", 20, QFont.Weight.Bold))

        text_layout.addWidget(self.streak_number_label)
        text_layout.addWidget(day_label)
        content_layout.addLayout(text_layout)

        if self.streak_manager.has_reviewed_today():
            self.header_widget.setStyleSheet("background-color: #d67e00;")
            top_widget.setStyleSheet("background-color: #d67e00;")
            self.streak_number_label.setStyleSheet("color: white;")
            day_label.setStyleSheet("color: white;")
            icon_data_uri = get_base64_icon_data("streak")
        else:
            top_widget.setStyleSheet("background-color: #2e2e2e;")
            self.header_widget.setStyleSheet("background-color: #2e2e2e;")
            self.streak_number_label.setStyleSheet("color: #AAAAAA;")
            day_label.setStyleSheet("color: #AAAAAA;")
            icon_data_uri = get_base64_icon_data("grey_streak")

        icon_label = QLabel()
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(icon_data_uri.split(",")[1]))
        scaled_pixmap = pixmap.scaled(100, 100, QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                                      QtCore.Qt.TransformationMode.SmoothTransformation)
        icon_label.setPixmap(scaled_pixmap)
        icon_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight)
        icon_label.setContentsMargins(6, 6, 2, 0)

        content_layout.addWidget(icon_label)
        top_layout.addLayout(content_layout)
        top_widget.setLayout(top_layout)

        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background-color: #2e2e2e;")

        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setAlignment(QtCoreQt.AlignmentFlag.AlignTop)
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # Set to 0 to remove extra margins
        bottom_layout.setSpacing(0)  # Set to 0 to remove extra spacing

        self.calendar_widget = CalendarWidget()
        bottom_layout.addWidget(self.calendar_widget)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.header_widget)
        main_layout.addWidget(separator)
        main_layout.addWidget(top_widget)
        main_layout.addWidget(bottom_widget)

        self.setLayout(main_layout)

    def open_share_window(self):
        from .share_dialog import ShareDialog
        dialog = ShareDialog(self)
        dialog.exec()

    def mousePressEvent(self, event):
        if event.button() == QtCoreQt.MouseButton.LeftButton:
            # Allow dragging only from the header widget
            if self.header_widget.underMouse():
                self.drag_pos = event.globalPosition().toPoint()
                event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == QtCoreQt.MouseButton.LeftButton and self.drag_pos:
            self.move(self.pos() + event.globalPosition().toPoint() - self.drag_pos)
            self.drag_pos = event.globalPosition().toPoint()
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        event.accept()

def open_streak_popup_with_manager(parent):
    popup = StreakPopup(parent)
    popup.exec()