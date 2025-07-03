import re
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QScrollArea, QWidget, QPushButton, QHBoxLayout
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
        self.setFixedSize(300, 230)

        self.setStyleSheet("""
            DayDetailsPopup {
                background-color: #3C3C3C;
                border: none;
                border-radius: 8px;
                color: white;
            }
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollArea > QWidget {
                 background-color: transparent;
            }
            QWidget {
                background-color: #3C3C3C;
            }

            QWidget#ContentWidget {
                background-color: #2E2E2E;
                border-radius: 4px;
            }
            QWidget#ContentWidget QLabel {
                color: white;
                font-size: 12px;
                background-color: transparent;
                padding: 0px;
            }
            QLabel#HeaderLabel {
                font-weight: bold;
                font-size: 16px;
                background-color: #3C3C3C;
                padding: 0px;
                margin: 0px;
            }
            QLabel#SubHeaderLabel {
                font-size: 12px;
                color: white;
                background-color: transparent;
                padding: 0px;
                margin: 0px;
            }
            QPushButton#CloseButton {
                background-color: transparent;
                border: none;
                font-weight: bold;
                font-size: 14px;
                color: white;
            }
            QPushButton#CloseButton:hover {
                color: #dddddd;
            }
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 10)
        main_layout.setSpacing(5)

        details_for_totals = self.streak_manager.get_review_details_for_date(self.selected_date)
        total_reviews = sum(data['reviews'] for data in details_for_totals.values()) if details_for_totals else 0
        total_time_ms = sum(data['time_spent_ms'] for data in details_for_totals.values()) if details_for_totals else 0
        total_time_min = round(total_time_ms / 60000, 1)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)

        stacked_labels_layout = QVBoxLayout()
        stacked_labels_layout.setContentsMargins(0, 0, 0, 0)
        stacked_labels_layout.setSpacing(0)
        stacked_labels_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_label = QLabel(f"Reviews on {selected_date.strftime('%b %d, %Y')}")
        header_label.setObjectName("HeaderLabel")
        header_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        stacked_labels_layout.addWidget(header_label)

        subheader_text = ""
        if total_reviews > 0:
            subheader_text = f"<b>{total_reviews}</b> reviews in <b>{total_time_min}</b> minutes"
        else:
            subheader_text = "No reviews on this day."

        subheader_label = QLabel(subheader_text)
        subheader_label.setObjectName("SubHeaderLabel")
        subheader_label.setTextFormat(Qt.TextFormat.RichText)
        subheader_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
        stacked_labels_layout.addWidget(subheader_label)

        close_button = QPushButton("✕")
        close_button.setObjectName("CloseButton")
        close_button.setFixedSize(24, 24)
        close_button.clicked.connect(self.close)

        header_layout.addStretch()
        header_layout.addLayout(stacked_labels_layout)
        header_layout.addStretch()
        header_layout.addWidget(close_button)

        main_layout.addLayout(header_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("border: none;")

        content_widget = QWidget()
        content_widget.setObjectName("ContentWidget")
        self.content_layout = QVBoxLayout(content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.content_layout.setContentsMargins(8, 8, 8, 8)
        self.content_layout.setSpacing(2)

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
            no_reviews_label = self._create_label("", alignment=Qt.AlignmentFlag.AlignCenter)
            self.content_layout.addWidget(no_reviews_label)
            return

        for deck_name_full, data in details.items():
            cleaned_deck_name_full = re.sub(r'[\x00-\x1F\x7F]', '/', deck_name_full)

            reviews = data['reviews']
            time_spent_ms = data['time_spent_ms']
            time_spent_min = round(time_spent_ms / 60000, 1)

            deck_label = self._create_label(f"<b>{cleaned_deck_name_full}</b>", font_size=15, bold=True)
            self.content_layout.addWidget(deck_label)

            stats_label = self._create_label(f"  • <b>{reviews}</b> reviews in <b>{time_spent_min}</b> minutes", font_size=14)
            self.content_layout.addWidget(stats_label)
