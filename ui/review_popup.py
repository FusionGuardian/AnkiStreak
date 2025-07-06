import base64
from PyQt6.QtCore import (
    Qt as QtCoreQt, QPropertyAnimation, QEasingCurve, QObject,
    pyqtProperty, QTimer, QPoint, pyqtSignal, QParallelAnimationGroup, QSequentialAnimationGroup
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QWidget, QPushButton, QGraphicsOpacityEffect

from .icon import get_base64_icon_data
from ..logic.streak_manager import get_streak_manager


class ColorPropertyAnimator(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._color = QColor()

    def get_color(self):
        return self._color

    def set_color(self, color):
        self._color = color

    color = pyqtProperty(QColor, get_color, set_color)


class IntPropertyAnimator(QObject):
    animated_valueChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._value = 0

    def get_value(self):
        return self._value

    def set_value(self, value):
        if self._value != value:
            self._value = value
            self.animated_valueChanged.emit(value)

    animated_value = pyqtProperty(int, get_value, set_value)


class IconAnimationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(80, 80)
        self.setContentsMargins(0, 0, 0, 0)

        self.grey_icon_label = QLabel(self)
        self.grey_icon_label.setPixmap(self._load_and_scale_icon(get_base64_icon_data("grey_streak")))
        self.grey_icon_label.setGeometry(0, 0, 80, 80)
        self.grey_icon_label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)

        self.orange_icon_label = QLabel(self)
        self.orange_icon_label.setPixmap(self._load_and_scale_icon(get_base64_icon_data("streak")))
        self.orange_icon_label.setGeometry(0, 0, 80, 80)
        self.orange_icon_label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
        self.orange_icon_label.hide()

        self.orange_icon_opacity_effect = QGraphicsOpacityEffect(self.orange_icon_label)
        self.orange_icon_label.setGraphicsEffect(self.orange_icon_opacity_effect)
        self.orange_icon_opacity_effect.setOpacity(0.0)

        self.grey_icon_opacity_effect = QGraphicsOpacityEffect(self.grey_icon_label)
        self.grey_icon_label.setGraphicsEffect(self.grey_icon_opacity_effect)
        self.grey_icon_opacity_effect.setOpacity(1.0)

    def _load_and_scale_icon(self, icon_data_uri: str) -> QPixmap:
        pixmap = QPixmap()
        pixmap.loadFromData(base64.b64decode(icon_data_uri.split(",")[1]))
        scaled_pixmap = pixmap.scaled(80, 80, QtCoreQt.AspectRatioMode.KeepAspectRatio,
                                      QtCoreQt.TransformationMode.SmoothTransformation)
        return scaled_pixmap

    def get_icon_fade_animation_group(self):
        grey_icon_fade_out_animation = QPropertyAnimation(self.grey_icon_opacity_effect, b"opacity")
        grey_icon_fade_out_animation.setDuration(1000)
        grey_icon_fade_out_animation.setStartValue(1.0)
        grey_icon_fade_out_animation.setEndValue(0.0)
        grey_icon_fade_out_animation.finished.connect(self.grey_icon_label.hide)

        self.orange_icon_label.show()
        self.orange_icon_label.raise_()
        orange_icon_fade_in_animation = QPropertyAnimation(self.orange_icon_opacity_effect, b"opacity")
        orange_icon_fade_in_animation.setDuration(1000)
        orange_icon_fade_in_animation.setStartValue(0.0)
        orange_icon_fade_in_animation.setEndValue(1.0)

        icon_fade_group = QParallelAnimationGroup()
        icon_fade_group.addAnimation(grey_icon_fade_out_animation)
        icon_fade_group.addAnimation(orange_icon_fade_in_animation)
        return icon_fade_group


class NumberAnimationWidget(QWidget):
    animation_finished = pyqtSignal()

    def __init__(self, parent=None, previous_streak=0, current_streak=0):
        super().__init__(parent)
        self.setFixedSize(250, 60)
        self.previous_streak = previous_streak
        self.current_streak = current_streak

        self.effective_right_margin = 20
        self.content_width = self.width() - self.effective_right_margin

        self.old_streak_number_label = QLabel(str(self.previous_streak) + "  ", self)
        self.new_streak_number_label = QLabel(str(self.current_streak) + "  ", self)

        number_font = QFont("Arial", 48, QFont.Weight.Bold)
        for lbl in [self.old_streak_number_label, self.new_streak_number_label]:
            lbl.setFont(number_font)
            lbl.setStyleSheet("color: white;")
            lbl.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
            lbl.setGeometry(
                (self.width() - self.content_width) // 2,
                0,
                self.content_width,
                self.height()
            )

        self.old_streak_number_label.show()
        self.new_streak_number_label.hide()

        self.old_number_opacity_effect = QGraphicsOpacityEffect(self.old_streak_number_label)
        self.old_streak_number_label.setGraphicsEffect(self.old_number_opacity_effect)
        self.old_number_opacity_effect.setOpacity(1.0)

        self.new_number_opacity_effect = QGraphicsOpacityEffect(self.new_streak_number_label)
        self.new_streak_number_label.setGraphicsEffect(self.new_number_opacity_effect)
        self.new_number_opacity_effect.setOpacity(0.0)

        self.old_streak_number_label.repaint()
        self.new_streak_number_label.repaint()

    def get_number_animation_group(self):
        if self.previous_streak != self.current_streak:
            self.new_streak_number_label.hide()
            self.new_streak_number_label.move(self.new_streak_number_label.x(), -self.height())

            common_easing_curve = QEasingCurve.Type.OutQuad

            self.old_number_pos_animation = QPropertyAnimation(self.old_streak_number_label, b"pos")
            self.old_number_pos_animation.setDuration(1000)
            self.old_number_pos_animation.setStartValue(QPoint(self.old_streak_number_label.x(), 0))
            self.old_number_pos_animation.setEndValue(QPoint(self.old_streak_number_label.x(), self.height()))
            self.old_number_pos_animation.setEasingCurve(common_easing_curve)
            self.old_number_pos_animation.finished.connect(self.old_streak_number_label.hide)

            self.old_number_opacity_animation = QPropertyAnimation(self.old_number_opacity_effect, b"opacity")
            self.old_number_opacity_animation.setDuration(1000)
            self.old_number_opacity_animation.setStartValue(1.0)
            self.old_number_opacity_animation.setEndValue(0.0)
            self.old_number_opacity_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

            old_number_group = QParallelAnimationGroup()
            old_number_group.addAnimation(self.old_number_pos_animation)
            old_number_group.addAnimation(self.old_number_opacity_animation)

            self.new_number_pos_animation = QPropertyAnimation(self.new_streak_number_label, b"pos")
            self.new_number_pos_animation.setDuration(1000)
            self.new_number_pos_animation.setStartValue(QPoint(self.new_streak_number_label.x(), -self.height()))
            self.new_number_pos_animation.setEndValue(QPoint(self.new_streak_number_label.x(), 0))
            self.new_number_pos_animation.setEasingCurve(common_easing_curve)

            self.new_number_opacity_animation = QPropertyAnimation(self.new_number_opacity_effect, b"opacity")
            self.new_number_opacity_animation.setDuration(1000)
            self.new_number_opacity_animation.setStartValue(0.0)
            self.new_number_opacity_animation.setEndValue(1.0)
            self.new_number_opacity_animation.setEasingCurve(QEasingCurve.Type.OutQuad)

            new_number_group = QParallelAnimationGroup()
            new_number_group.addAnimation(self.new_number_pos_animation)
            new_number_group.addAnimation(self.new_number_opacity_animation)

            self.new_streak_number_label.show()

            number_slide_group = QParallelAnimationGroup()
            number_slide_group.addAnimation(old_number_group)
            number_slide_group.addAnimation(new_number_group)

            return number_slide_group

        else:
            self.old_streak_number_label.hide()
            self.new_streak_number_label.setGeometry(
                (self.width() - self.content_width) // 2,
                0,
                self.content_width,
                self.height()
            )
            self.new_streak_number_label.show()
            self.new_number_opacity_effect.setOpacity(1.0)

            dummy_animation = QPropertyAnimation(self, b"pos")
            dummy_animation.setDuration(1)
            dummy_animation.setStartValue(QPoint(0, 0))
            dummy_animation.setEndValue(QPoint(0, 0))
            return dummy_animation


class StreakAnimationPopup(QDialog):
    def __init__(self, parent=None, previous_streak=0, current_streak=0):
        super().__init__(parent, QtCoreQt.WindowType.SplashScreen | QtCoreQt.WindowType.FramelessWindowHint)
        self.setAttribute(QtCoreQt.WidgetAttribute.WA_DeleteOnClose)
        self.setWindowModality(QtCoreQt.WindowModality.NonModal)
        self.setFixedSize(250, 250)

        self.previous_streak = previous_streak
        self.current_streak = current_streak

        self.setStyleSheet("background-color: #2e2e2e; border-radius: 15px;")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)
        main_layout.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(0)

        self.icon_animation_widget = IconAnimationWidget(self)
        main_layout.addWidget(self.icon_animation_widget, alignment=QtCoreQt.AlignmentFlag.AlignCenter)
        self.icon_animation_widget.raise_()

        main_layout.addSpacing(15)

        self.number_animation_widget = NumberAnimationWidget(self,
                                                             previous_streak=self.previous_streak,
                                                             current_streak=self.current_streak)
        main_layout.addWidget(self.number_animation_widget, alignment=QtCoreQt.AlignmentFlag.AlignCenter)

        main_layout.addSpacing(5)

        self.day_label = QLabel("day streak!", self)
        self.day_label.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        self.day_label.setStyleSheet("color: white;")
        self.day_label.setAlignment(QtCoreQt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.day_label, alignment=QtCoreQt.AlignmentFlag.AlignCenter)

        self.great_button = QPushButton("Great!", self)
        self.great_button.setFixedSize(120, 40)
        self.great_button.setStyleSheet("""
            QPushButton {
                background-color: #f47c00;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 10px;
                border: 1px solid #c96500;
            }
            QPushButton:hover {
                background-color: #ff9222;
            }
            QPushButton:pressed {
                background-color: #a85800;
            }
        """)
        self.great_button.clicked.connect(self.close)

        self.button_opacity_effect = QGraphicsOpacityEffect(self.great_button)
        self.great_button.setGraphicsEffect(self.button_opacity_effect)
        self.button_opacity_effect.setOpacity(0.0)

        main_layout.addWidget(self.great_button, alignment=QtCoreQt.AlignmentFlag.AlignCenter)

        self.setLayout(main_layout)

        QTimer.singleShot(10, self._start_initial_animations)

    def _update_background_color(self, color: QColor):
        self.setStyleSheet(f"background-color: {color.name()}; border-radius: 15px;")

    def _start_initial_animations(self):
        self.color_animator = ColorPropertyAnimator(self)
        self.background_animation = QPropertyAnimation(self.color_animator, b"color")
        self.background_animation.setDuration(1000)
        self.background_animation.setStartValue(QColor("#2e2e2e"))
        self.background_animation.setEndValue(QColor("#d67e00"))
        self.background_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.background_animation.valueChanged.connect(self._update_background_color)

        icon_fade_group = self.icon_animation_widget.get_icon_fade_animation_group()

        number_animation_group = self.number_animation_widget.get_number_animation_group()

        initial_parallel_animations = QParallelAnimationGroup()
        initial_parallel_animations.addAnimation(icon_fade_group)
        initial_parallel_animations.addAnimation(self.background_animation)
        initial_parallel_animations.addAnimation(number_animation_group)

        self.master_sequence = QSequentialAnimationGroup()
        self.master_sequence.addAnimation(initial_parallel_animations)

        self.master_sequence.finished.connect(self._show_great_button)

        QTimer.singleShot(300, self.master_sequence.start)

    def _show_great_button(self):
        self.button_opacity_animation = QPropertyAnimation(self.button_opacity_effect, b"opacity")
        self.button_opacity_animation.setDuration(400)
        self.button_opacity_animation.setStartValue(0.0)
        self.button_opacity_animation.setEndValue(1.0)
        self.button_opacity_animation.start()
