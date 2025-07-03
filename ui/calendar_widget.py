import calendar
from datetime import date
from PyQt6.QtCore import Qt as QtCoreQt, QEvent, QPoint
from PyQt6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QToolTip
)
from PyQt6.QtGui import QCursor, QMouseEvent, QColor
from .day_details_popup import DayDetailsPopup
from ..logic.streak_manager import get_streak_manager
import re

class CalendarWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.streak_manager = get_streak_manager()
        self.current_date = date.today().replace(day=1)
        self.displayed_date = self.current_date
        self.setStyleSheet("background-color: #2e2e2e;")
        self.setMouseTracking(False)  # Essential for getting QEvent.MouseMove

        bottom_layout = QVBoxLayout(self)
        bottom_layout.setAlignment(QtCoreQt.AlignmentFlag.AlignTop)
        bottom_layout.setContentsMargins(20, 20, 20, 20)
        bottom_layout.setSpacing(10)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        calendar_title = QLabel("Streak Calendar")
        calendar_title.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        calendar_title.setAlignment(QtCoreQt.AlignmentFlag.AlignLeft)


        header_layout.addWidget(calendar_title, 0, QtCoreQt.AlignmentFlag.AlignLeft)
        bottom_layout.addWidget(header_widget)
        
        calendar_container = QWidget()
        calendar_container.setObjectName("calendarContainer")
        calendar_container.setFixedHeight(480)
        calendar_container.setStyleSheet("""
            QWidget#calendarContainer {
                background-color: #2e2e2e;
                border-radius: 16px;
                border: 1px solid #999999;
                margin: 0px;
            }
        """)

        calendar_layout = QVBoxLayout(calendar_container)
        calendar_layout.setContentsMargins(15, 15, 15, 15)
        calendar_layout.setSpacing(10)

        calendar_header_widget = QWidget()
        calendar_header_widget.setFixedHeight(36)
        calendar_header_widget.setStyleSheet("""
            background-color: #2e2e2e;
            border-top-left-radius: 16px;
            border-top-right-radius: 16px;
        """)

        calendar_header_layout = QHBoxLayout(calendar_header_widget)
        calendar_header_layout.setContentsMargins(12, 0, 12, 0)
        calendar_header_layout.setSpacing(12)

        prev_button = QPushButton("〈")
        prev_button.setFixedSize(28, 28)
        prev_button.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: white;
                font-size: 18px;
                border: none;
            }
            QPushButton:hover {
                color: #bbbbbb;
            }
        """)

        next_button = QPushButton("〉")
        next_button.setFixedSize(28, 28)
        next_button.setStyleSheet(prev_button.styleSheet())

        self.next_button = next_button
        self.prev_button = prev_button
        self.update_calendar_nav_buttons()

        self.prev_button.clicked.connect(self.show_previous_month)
        self.next_button.clicked.connect(self.show_next_month)

        self.month_label = QLabel(self.displayed_date.strftime("%B %Y"))
        self.month_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        self.month_label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)

        calendar_header_layout.addWidget(prev_button)
        calendar_header_layout.addStretch()
        calendar_header_layout.addWidget(self.month_label)
        calendar_header_layout.addStretch()
        calendar_header_layout.addWidget(next_button)

        calendar_header_widget.setLayout(calendar_header_layout)

        calendar_body = QWidget()
        self.calendar_grid_layout = QGridLayout(calendar_body)
        self.calendar_grid_layout.setContentsMargins(10, 10, 10, 10)
        self.calendar_grid_layout.setSpacing(10)

        days_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        for i, day in enumerate(days_of_week):
            label = QLabel(day)
            label.setStyleSheet("color: white; font-weight: bold; font-size: 18px;")
            label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
            self.calendar_grid_layout.addWidget(label, 0, i)

        calendar_body.setLayout(self.calendar_grid_layout)
        calendar_layout.setAlignment(QtCoreQt.AlignmentFlag.AlignTop)
        calendar_layout.addWidget(calendar_header_widget)
        calendar_layout.addWidget(calendar_body)

        calendar_container.setLayout(calendar_layout)
        bottom_layout.addWidget(calendar_container)

        self.day_labels = []

        for i in range(6):
            for j in range(7):
                label = QLabel()
                label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
                label.setStyleSheet("color: white; padding: 6px;")
                label.setFixedSize(50, 50)
                self.calendar_grid_layout.addWidget(label, i + 1, j)
                self.day_labels.append(label)
                label.installEventFilter(self) # Re-enable event filter

        self.refresh_calendar_grid()

    def eventFilter(self, obj, event):
        if obj in self.day_labels:
            if event.type() == QEvent.Type.Enter:
                if hasattr(obj, '_associated_date'): # Only apply hover if it's a valid day
                    # Store original stylesheet
                    obj._original_stylesheet = obj.styleSheet()

                    # Extract current background color
                    current_style = obj.styleSheet()
                    bg_color_match = re.search(r'background-color:\s*([^;]+)', current_style)
                    if bg_color_match:
                        current_bg_color_str = bg_color_match.group(1).strip()
                        current_color = QColor(current_bg_color_str)
                        lighter_color = current_color.lighter(120) # Make it 20% lighter
                        obj.setStyleSheet(current_style.replace(current_bg_color_str, lighter_color.name()))
                    else:
                        # Fallback if no background-color found (e.g., transparent)
                        obj.setStyleSheet("background-color: #555555; color: white; padding: 6px; border-radius: 10px; font-size: 20px;")

                    self.setCursor(QCursor(QtCoreQt.CursorShape.PointingHandCursor))
                return True
            elif event.type() == QEvent.Type.Leave:
                if hasattr(obj, '_associated_date'): # Only revert if it was a valid day
                    # Revert to original stylesheet
                    if hasattr(obj, '_original_stylesheet'):
                        obj.setStyleSheet(obj._original_stylesheet)
                    else:
                        # Fallback if original stylesheet not stored
                        self.refresh_calendar_grid() # Re-render the grid to reset styles
                    self.unsetCursor()
                return True
        return super().eventFilter(obj, event)

    def update_calendar_nav_buttons(self):
        if (self.displayed_date.year, self.displayed_date.month) == (date.today().year, date.today().month):
            self.next_button.setEnabled(False)
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #666666;
                    font-size: 18px;
                    border: none;
                }
            """)
        else:
            self.next_button.setEnabled(True)
            self.next_button.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: white;
                    font-size: 18px;
                    border: none;
                }
                QPushButton:hover {
                    color: #bbbbbb;
                }
            """)

    def show_previous_month(self):
        QToolTip.hideText()
        year = self.displayed_date.year
        month = self.displayed_date.month - 1
        if month == 0:
            month = 12
            year -= 1
        self.displayed_date = self.displayed_date.replace(year=year, month=month)
        self.month_label.setText(self.displayed_date.strftime("%B %Y"))
        self.update_calendar_nav_buttons()
        self.refresh_calendar_grid()

    def show_next_month(self):
        QToolTip.hideText()
        year = self.displayed_date.year
        month = self.displayed_date.month + 1
        if month == 13:
            month = 1
            year += 1
        self.displayed_date = self.displayed_date.replace(year=year, month=month)
        self.month_label.setText(self.displayed_date.strftime("%B %Y"))
        self.update_calendar_nav_buttons()
        self.refresh_calendar_grid()

    def refresh_calendar_grid(self):
        all_reviewed_dates = self.streak_manager.streak_history.get_streak_days()
        consumed_freeze_dates = set(self.streak_manager.get_consumed_freeze_dates())

        year = self.displayed_date.year
        month = self.displayed_date.month

        cal = calendar.Calendar(firstweekday=calendar.MONDAY)
        month_days = cal.monthdayscalendar(year, month)

        today_str = date.today().strftime("%Y-%m-%d")

        for label in self.day_labels:
            label.setText("")
            if hasattr(label, '_associated_date'):
                del label._associated_date
            label.setStyleSheet("background-color: transparent; color: white; padding: 6px; border-radius: 10px; font-size: 20px;")

        label_index = 0
        for week in month_days:
            for day in week:
                if day != 0:
                    label = self.day_labels[label_index]
                    label.setText(str(day))

                    current_day_date_str = f"{year:04d}-{month:02d}-{day:02d}"
                    label._associated_date = date(year, month, day)

                    is_reviewed_day = current_day_date_str in all_reviewed_dates
                    is_freeze_day = current_day_date_str in consumed_freeze_dates
                    is_today = current_day_date_str == today_str

                    label.setStyleSheet(self._get_day_label_stylesheet(is_today, is_reviewed_day, is_freeze_day))
                    label.mousePressEvent = lambda event, lbl=label: self._on_day_label_clicked(event, lbl)

                label_index += 1

    def _get_day_label_stylesheet(self, is_today: bool, is_reviewed_day: bool, is_freeze_day: bool) -> str:
        base_style = "color: white; font-weight: bold; border-radius: 10px; padding: 6px; font-size: 20px;"
        today_font_size = "22px"

        if is_today:
            if is_reviewed_day:
                return f"background-color: #F47C00; color: black; font-weight: bold; border-radius: 10px; padding: 6px; font-size: {today_font_size};"
            elif is_freeze_day:
                return f"background-color: #5bb3ff; color: black; font-weight: bold; border-radius: 10px; padding: 6px; border: 5px solid #80D3FF; font-size: {today_font_size};"
            else:
                return f"background-color: #545454; color: white; font-weight: bold; border-radius: 10px; padding: 6px; border: 1px solid #999999; font-size: {today_font_size};"
        elif is_reviewed_day:
            return f"background-color: #D67E00; color: black; font-weight: bold; border-radius: 10px; padding: 6px; font-size: 22px;"
        elif is_freeze_day:
            return f"background-color: #44B1F9; color: white; font-weight: bold; border-radius: 10px; padding: 6px; border: 5px solid #80D3FF; font-size: 20px;"
        else:
            return base_style

    def _on_day_label_clicked(self, event: QMouseEvent, label: QLabel):
        if event.button() == QtCoreQt.MouseButton.LeftButton:
            if hasattr(label, '_associated_date'):
                selected_date = label._associated_date # Get selected_date here

                # Get the global position of the label
                global_pos = label.mapToGlobal(QPoint(0, 0))
                # Calculate the center of the label
                center_x = global_pos.x() + label.width() // 2
                center_y = global_pos.y() + label.height() // 2

                popup = DayDetailsPopup(self.streak_manager, selected_date, self)
                # Position the popup above the clicked label
                popup_x = center_x - popup.width() // 2
                popup_y = global_pos.y() - popup.height() - 10 # 10 pixels above the label
                popup.move(popup_x, popup_y)
                popup.exec()
