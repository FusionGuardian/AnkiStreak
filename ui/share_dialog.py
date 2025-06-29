import base64
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout,
    QApplication, QWidget, QToolButton,
    QFileDialog, QToolTip
)
from PyQt6.QtCore import Qt, QUrl, QSize, QStandardPaths, QPoint, QRect
from PyQt6.QtGui import QDesktopServices, QIcon, QPixmap, QPainter

from .icon import get_base64_icon_data
from ..logic.streak_manager import get_streak_manager


class ShareDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Share Streak")
        self.setFixedSize(650, 470)

        try:
            self.streak_manager = get_streak_manager()
            self.current_streak = self.streak_manager.get_current_streak_length()
            self.reviewed_today = self.streak_manager.has_reviewed_today()
        except Exception as e:
            self.current_streak = 0
            self.reviewed_today = False
            print(f"AnkiStreak: Error getting streak in ShareDialog: {e}")

        if self.reviewed_today:
            bg_color = "#d67e00"
            text_color = "white"
            icon_data_uri = get_base64_icon_data("streak")
        else:
            bg_color = "#545454"
            text_color = "#AAAAAA"
            icon_data_uri = get_base64_icon_data("grey_streak")

        self.setStyleSheet(f"""
            ShareDialog {{
                background-color: #2e2e2e;
                border-radius: 10px;
                color: white;
            }}
            QLabel {{
                color: white;
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton {{
                background-color: #545454;
                color: white;
                border: 1px solid #777777;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: 12px;
            }}
            QPushButton:hover {{
                background-color: #6a6a6a;
            }}
            QPushButton:pressed {{
                background-color: #4a4a4a;
            }}
            #StreakVisualSection {{
                background-color: {bg_color};
                border-radius: 15px;
            }}
            #StreakNumberLabel {{
                color: {text_color};
                font-size: 95px; 
                font-weight: bold;
            }}
            #DayStreakLabel {{
                color: {text_color};
                font-size: 20px; 
                font-weight: bold;
            }}
        """)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        top_label = QLabel("Share your streak with friends!")
        top_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(top_label)

        main_layout.addSpacing(15)

        self.streak_visual_section = QWidget(self)
        self.streak_visual_section.setObjectName("StreakVisualSection")
        self.streak_visual_section.setFixedSize(250, 250)

        visual_layout = QVBoxLayout(self.streak_visual_section)
        visual_layout.setContentsMargins(15, 15, 15, 15)
        visual_layout.setSpacing(0)
        visual_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.orange_icon_label = QLabel(self.streak_visual_section)
        orange_pixmap = QPixmap()
        orange_pixmap.loadFromData(base64.b64decode(icon_data_uri.split(",")[1]))
        scaled_orange_pixmap = orange_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio,
                                                    Qt.TransformationMode.SmoothTransformation)
        self.orange_icon_label.setPixmap(scaled_orange_pixmap)
        self.orange_icon_label.setFixedSize(80, 80)
        self.orange_icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visual_layout.addWidget(self.orange_icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        self.streak_number_label = QLabel(str(self.current_streak), self.streak_visual_section)
        self.streak_number_label.setObjectName("StreakNumberLabel")
        self.streak_number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visual_layout.addWidget(self.streak_number_label, alignment=Qt.AlignmentFlag.AlignCenter)


        self.day_label = QLabel("day streak in Anki!", self.streak_visual_section)
        self.day_label.setObjectName("DayStreakLabel")
        self.day_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        visual_layout.addWidget(self.day_label, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addWidget(self.streak_visual_section, alignment=Qt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(40)

        share_options_layout = QHBoxLayout()
        share_options_layout.setContentsMargins(0, 0, 0, 0)
        share_options_layout.setSpacing(10)
        share_options_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        tool_button_stylesheet = """
            QToolButton {
                background-color: #545454;
                color: white;
                border: 1px solid #777777;
                border-radius: 5px;
                padding: 4px;
                qproperty-toolButtonStyle: ToolButtonTextUnderIcon;
                font-size: 10px;
            }
            QToolButton:hover {
                background-color: #6a6a6a;
            }
            QToolButton:pressed {{
                background-color: #4a4a4a;
            }}
        """

        copy_text_button = QToolButton()
        copy_text_button.setText("Copy")
        copy_text_button.setFixedSize(110, 60)
        copy_text_button.setStyleSheet(tool_button_stylesheet)
        copy_icon_pixmap = QPixmap()
        copy_icon_pixmap.loadFromData(base64.b64decode(get_base64_icon_data("copy").split(",")[1]))
        copy_text_button.setIcon(QIcon(copy_icon_pixmap))
        copy_text_button.setIconSize(QSize(32, 32))
        copy_text_button.clicked.connect(self.copy_image_to_clipboard)
        share_options_layout.addWidget(copy_text_button)

        download_button = QToolButton()
        download_button.setText("Download")
        download_button.setFixedSize(110, 60)
        download_button.setStyleSheet(tool_button_stylesheet)
        download_icon_pixmap = QPixmap()
        download_icon_pixmap.loadFromData(base64.b64decode(get_base64_icon_data("download").split(",")[1]))
        download_button.setIcon(QIcon(download_icon_pixmap))
        download_button.setIconSize(QSize(32, 32))
        download_button.clicked.connect(self.save_streak_image)
        share_options_layout.addWidget(download_button)

        twitter_button = QToolButton()
        twitter_button.setText("Share to X")
        twitter_button.setFixedSize(110, 60)
        twitter_button.setStyleSheet(tool_button_stylesheet)
        twitter_icon_pixmap = QPixmap()
        twitter_icon_pixmap.loadFromData(base64.b64decode(get_base64_icon_data("x").split(",")[1]))
        twitter_button.setIcon(QIcon(twitter_icon_pixmap))
        twitter_button.setIconSize(QSize(32, 32))
        twitter_button.clicked.connect(self.share_to_twitter)
        share_options_layout.addWidget(twitter_button)

        facebook_button = QToolButton()
        facebook_button.setText("Share to Facebook")
        facebook_button.setFixedSize(110, 60)
        facebook_button.setStyleSheet(tool_button_stylesheet)
        facebook_icon_pixmap = QPixmap()
        facebook_icon_pixmap.loadFromData(base64.b64decode(get_base64_icon_data("facebook").split(",")[1]))
        facebook_button.setIcon(QIcon(facebook_icon_pixmap))
        facebook_button.setIconSize(QSize(32, 32))
        facebook_button.clicked.connect(self.share_to_facebook)
        share_options_layout.addWidget(facebook_button)

        main_layout.addLayout(share_options_layout)
        close_button = QPushButton("Close")
        close_button.setFixedSize(100, 30)
        close_button.clicked.connect(self.close)
        main_layout.addWidget(close_button, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_copied_message(self, widget: QWidget):
        global_pos = widget.mapToGlobal(QPoint(0, 0))
        tooltip_x = global_pos.x() + widget.width() // 2
        tooltip_y = global_pos.y() + widget.height() // 2

        QToolTip.showText(QPoint(tooltip_x, tooltip_y), "Copied to clipboard!", self, QRect(), 1000)

    def copy_text_to_clipboard(self):
        clipboard_text = f"I'm on a fantastic Anki streak of {self.current_streak} days! Keep up the good work! 🔥 #AnkiStreak"
        QApplication.instance().clipboard().setText(clipboard_text)
        self.show_copied_message(self.sender())

    def copy_image_to_clipboard(self):
        pixmap = QPixmap(self.streak_visual_section.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.streak_visual_section.render(painter)
        painter.end()

        QApplication.instance().clipboard().setPixmap(pixmap)

        self.show_copied_message(self.sender())

    def share_to_twitter(self):
        share_text = f"I'm on an Anki streak of {self.current_streak} days! #AnkiStreak"
        encoded_text = QUrl.toPercentEncoding(share_text).data().decode('utf-8')
        twitter_url = f"https://x.com/intent/tweet?text={encoded_text}"
        QDesktopServices.openUrl(QUrl(twitter_url))

    def share_to_facebook(self):
        share_url_link = QUrl.toPercentEncoding("https://www.ankiweb.net/").data().decode('utf-8')
        share_text = f"I'm on an Anki streak of {self.current_streak} days! #AnkiStreak"
        encoded_text = QUrl.toPercentEncoding(share_text).data().decode('utf-8')

        facebook_url = f"https://www.facebook.com/sharer/sharer.php?u={share_url_link}&quote={encoded_text}"
        QDesktopServices.openUrl(QUrl(facebook_url))

    def save_streak_image(self):
        pixmap = QPixmap(self.streak_visual_section.size())
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        self.streak_visual_section.render(painter)
        painter.end()

        downloads_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DownloadLocation)
        default_file_name = f"{downloads_path}/anki_streak.png"

        file_name, _ = QFileDialog.getSaveFileName(self,
                                                   "Save Streak Image",
                                                   default_file_name,
                                                   "PNG Image (*.png);;All Files (*)")
        if file_name:
            pixmap.save(file_name)