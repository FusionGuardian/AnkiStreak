import re
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget
from PyQt6.QtCore import Qt
from datetime import date

class DayDetailsPopup(QDialog):
    def __init__(self, streak_manager, selected_date: date, parent=None):
        super().__init__(parent)
        self.streak_manager = streak_manager
        self.selected_date = selected_date

        self.setWindowTitle(f"Details for {selected_date.strftime('%Y-%m-%d')}")
        self.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(300, 250)

        self.setStyleSheet("""
            DayDetailsPopup {
                background-color: #3c3c3c;
                border: none; /* Removed border */
                border-radius: 8px;
                color: white;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLabel#HeaderLabel {
                font-weight: bold;
                font-size: 16px;
                margin-bottom: 5px;
            }
        """
        )

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(5)

        header_label = QLabel(f"Reviews on {selected_date.strftime('%b %d, %Y')}")
        header_label.setObjectName("HeaderLabel")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header_label)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("border: none;")

        content_widget = QWidget()
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(3)

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

        self._load_review_details()

    def _create_label(self, text: str, font_size: int = 14, bold: bool = False, alignment=Qt.AlignmentFlag.AlignLeft):
        label = QLabel(text)
        style = f"color: white; font-size: {font_size}px;"
        if bold:
            style += " font-weight: bold;"
        label.setStyleSheet(style)
        label.setAlignment(alignment)
        return label

    def _load_review_details(self):
        details = self.streak_manager.get_review_details_for_date(self.selected_date)

        if not details:
            no_reviews_label = self._create_label("No reviews on this day.", alignment=Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_reviews_label)
            return

        for deck_name_full, data in details.items():
            cleaned_deck_name_full = re.sub(r'[\x00-\x1F\x7F]', '/', deck_name_full)

            reviews = data['reviews']
            time_spent_ms = data['time_spent_ms']
            time_spent_min = round(time_spent_ms / 60000, 1)

            deck_container_layout = QVBoxLayout()
            deck_container_layout.setContentsMargins(0, 0, 0, 0)
            deck_container_layout.setSpacing(0)

            deck_label = self._create_label(f"<b>{cleaned_deck_name_full}</b>", font_size=15, bold=True)
            deck_container_layout.addWidget(deck_label)

            stats_label = self._create_label(f"  - <b>{reviews}</b> reviews in <b>{time_spent_min}</b> minutes", font_size=14)
            deck_container_layout.addWidget(stats_label)

            self.content_layout.addLayout(deck_container_layout)

        self.content_layout.addStretch(1)

        total_reviews = sum(data['reviews'] for data in details.values())
        total_time_ms = sum(data['time_spent_ms'] for data in details.values())
        total_time_min = round(total_time_ms / 60000, 1)

        self.content_layout.addSpacing(10)

        total_reviews_label = self._create_label(f"<b>Total: {total_reviews}</b> reviews", font_size=15, bold=True)
        self.content_layout.addWidget(total_reviews_label)

        total_time_label = self._create_label(f"<b>Total: {total_time_min}</b> minutes", font_size=15, bold=True)
        self.content_layout.addWidget(total_time_label)
