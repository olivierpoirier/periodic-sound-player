from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QPushButton,
    QRadioButton,
    QSlider,
    QTabBar,
    QStyle,
    QStyleOptionButton,
    QStyleOptionTab,
    QWidget,
)


SMOOTH_FRAME_STYLES = {
    "panel": ("base", 140, "text", 96, 22, 1.55),
    "settingsShell": ("base", 116, "text", 80, 20, 1.5),
    "timerCard": ("surface_alt", 136, "accent", 126, 20, 1.55),
    "tabSurface": ("surface", 120, "text", 88, 16, 1.45),
    "previewCard": ("base", 128, "text", 92, 17, 1.45),
    "imagePreview": ("base", 128, "text", 92, 17, 1.45),
    "modeCard": ("base", 106, "text", 78, 16, 1.45),
}

BUTTON_ROLE_STYLES = {
    "ghostButton": ("text", 18, "text", 86, 10),
    "secondaryButton": ("surface", 96, "text", 108, 10),
    "warningButton": ("accent", 122, "text", 104, 10),
    "dangerButton": ("surface_alt", 112, "accent", 116, 10),
    "successButton": ("accent_alt", 122, "accent", 162, 11),
    "timerButton": ("surface_alt", 100, "text", 118, 11),
    "helpButton": ("surface_alt", 106, "text", 116, 11),
    "coffeeButton": ("accent_alt", 118, "text", 116, 11),
    "dockToggle": ("base", 104, "text", 96, 14),
}


def _with_alpha(color: QColor, alpha: int) -> QColor:
    result = QColor(color)
    result.setAlpha(alpha)
    return result


def _palette_color(palette, name: str, fallback: str) -> QColor:
    return QColor(getattr(palette, name, QColor(fallback)))


class SmoothFrame(QFrame):
    """Antialiased rounded frame for the large translucent panels."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        palette = getattr(self.window(), "theme_palette", None)
        object_name = self.objectName()
        style = SMOOTH_FRAME_STYLES.get(object_name)
        if not palette or not style:
            super().paintEvent(event)
            return

        bg_name, bg_alpha, border_name, border_alpha, radius, pen_width = style
        if object_name == "modeCard":
            if self.property("active") is True:
                bg_name, bg_alpha, border_name, border_alpha = "surface_alt", 132, "accent", 162
            elif self.underMouse():
                bg_name, bg_alpha, border_name, border_alpha = "surface", 122, "accent", 142

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setBrush(_with_alpha(_palette_color(palette, bg_name, "#111111"), bg_alpha))
        pen = QPen(_with_alpha(_palette_color(palette, border_name, "#edf3f5"), border_alpha), pen_width)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        inset = pen_width / 2 + 0.6
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        painter.drawRoundedRect(rect, radius, radius)
        painter.end()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.update()
        super().leaveEvent(event)


class SmoothGroupBox(QGroupBox):
    """QGroupBox with painter-drawn rounded borders to avoid jagged stylesheet corners."""

    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(title, parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        palette = getattr(self.window(), "theme_palette", None)
        if not palette:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen_width = 1.6
        top = 10.0
        rect = QRectF(0.9, top, self.width() - 1.8, self.height() - top - 0.9)
        painter.setBrush(_with_alpha(_palette_color(palette, "base", "#111111"), 108))
        pen = QPen(_with_alpha(_palette_color(palette, "text", "#edf3f5"), 86), pen_width)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, 18, 18)

        title = self.title()
        if title:
            metrics = QFontMetrics(self.font())
            title_rect = metrics.boundingRect(title)
            label_rect = QRectF(24, 0, title_rect.width() + 18, metrics.height() + 4)
            painter.setPen(Qt.NoPen)
            painter.setBrush(_with_alpha(_palette_color(palette, "base", "#111111"), 126))
            painter.drawRect(label_rect)
            painter.setPen(_palette_color(palette, "text", "#edf3f5"))
            painter.drawText(label_rect.adjusted(9, 0, -9, 0), Qt.AlignVCenter | Qt.AlignLeft, title)
        painter.end()


class PaintedButton(QPushButton):
    """Push button with the same painter-drawn border language as the panels."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        palette = getattr(self.window(), "theme_palette", None)
        if not palette:
            super().paintEvent(event)
            return

        role = self.objectName()
        bg_name, bg_alpha, border_name, border_alpha, radius = BUTTON_ROLE_STYLES.get(
            role,
            ("surface_alt", 108, "text", 108, 10),
        )

        if self.underMouse() and self.isEnabled():
            bg_alpha += 18
            border_name = "accent"
            border_alpha += 28
        if self.isDown():
            bg_name = "base"
            bg_alpha = max(92, bg_alpha - 12)
        if not self.isEnabled():
            bg_name = "surface"
            bg_alpha = 64
            border_alpha = 46

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        pen_width = 1.6
        inset = pen_width / 2 + 0.35
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        painter.setBrush(_with_alpha(_palette_color(palette, bg_name, "#111111"), bg_alpha))
        pen = QPen(_with_alpha(_palette_color(palette, border_name, "#edf3f5"), border_alpha), pen_width)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.drawRoundedRect(rect, radius, radius)

        option = QStyleOptionButton()
        self.initStyleOption(option)
        option.rect = self.rect().adjusted(2, 0, -2, 0)
        option.features &= ~QStyleOptionButton.ButtonFeature.DefaultButton
        painter.setPen(_palette_color(palette, "text", "#edf3f5"))
        self.style().drawControl(QStyle.ControlElement.CE_PushButtonLabel, option, painter, self)
        painter.end()


class SmoothTabBar(QTabBar):
    """Antialiased tabs painted to match the app's rounded panel borders."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDrawBase(False)
        self.setMouseTracking(True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        palette = getattr(self.window(), "theme_palette", None)
        if not palette:
            super().paintEvent(event)
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        for index in range(self.count()):
            option = QStyleOptionTab()
            self.initStyleOption(option, index)
            selected = index == self.currentIndex()
            hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
            bg_name = "accent_alt" if selected else "surface_alt"
            bg_alpha = 108 if selected else 78
            border_name = "accent" if selected else "text"
            border_alpha = 154 if selected else 92
            if hovered and not selected:
                bg_name, bg_alpha, border_name, border_alpha = "accent_alt", 72, "accent", 118

            rect = QRectF(self.tabRect(index)).adjusted(0.7, 0.7, -0.7, -0.7)
            painter.setBrush(_with_alpha(_palette_color(palette, bg_name, "#111111"), bg_alpha))
            pen = QPen(_with_alpha(_palette_color(palette, border_name, "#edf3f5"), border_alpha), 1.45)
            pen.setJoinStyle(Qt.RoundJoin)
            painter.setPen(pen)
            painter.drawRoundedRect(rect, 8, 8)

            text_color = _palette_color(palette, "text" if selected else "muted", "#edf3f5")
            painter.setPen(text_color)
            painter.drawText(option.rect.adjusted(10, 0, -10, 0), Qt.AlignCenter, self.tabText(index))
        painter.end()


def _paint_option_indicator(button: QCheckBox | QRadioButton, radio: bool) -> None:
    palette = getattr(button.window(), "theme_palette", None)
    text_color = _palette_color(palette, "text", "#edf3f5") if palette else QColor("#edf3f5")
    muted_color = _palette_color(palette, "muted", "#9aa1a4") if palette else QColor("#9aa1a4")
    accent_color = _palette_color(palette, "accent", "#79a8a8") if palette else QColor("#79a8a8")
    fill_color = _with_alpha(accent_color if button.isChecked() else text_color, 210 if button.isChecked() else 28)
    border_color = _with_alpha(text_color, 220 if button.isChecked() else 168)
    if button.underMouse() and button.isEnabled():
        border_color = _with_alpha(accent_color, 220)
        if not button.isChecked():
            fill_color = _with_alpha(accent_color, 42)
    if not button.isEnabled():
        text_color = _with_alpha(muted_color, 130)
        border_color = _with_alpha(muted_color, 110)
        fill_color = _with_alpha(muted_color, 32)

    painter = QPainter(button)
    painter.setRenderHint(QPainter.Antialiasing, True)
    indicator_size = 20
    y = (button.height() - indicator_size) / 2
    rect = QRectF(1.0, y, indicator_size, indicator_size)
    pen = QPen(border_color, 1.5)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(fill_color)
    if radio:
        painter.drawEllipse(rect.adjusted(0.8, 0.8, -0.8, -0.8))
        if button.isChecked():
            painter.setPen(Qt.NoPen)
            painter.setBrush(_with_alpha(text_color, 235))
            painter.drawEllipse(QPointF(rect.center()), 4.1, 4.1)
    else:
        painter.drawRoundedRect(rect.adjusted(0.8, 0.8, -0.8, -0.8), 6.0, 6.0)
        if button.isChecked():
            painter.setPen(QPen(_with_alpha(text_color, 235), 2.0, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.drawLine(QPointF(rect.left() + 5.6, rect.center().y()), QPointF(rect.left() + 9.0, rect.bottom() - 6.0))
            painter.drawLine(QPointF(rect.left() + 9.0, rect.bottom() - 6.0), QPointF(rect.right() - 4.8, rect.top() + 5.2))

    painter.setPen(text_color)
    text_rect = QRectF(30, 0, max(0, button.width() - 30), button.height())
    painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, button.text())
    painter.end()


class SmoothRadioButton(QRadioButton):
    """Radio button with an antialiased indicator."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(25)
        self.toggled.connect(lambda _checked: self.update())

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API name
        metrics = QFontMetrics(self.font())
        return QSize(metrics.horizontalAdvance(self.text()) + 34, max(25, metrics.height() + 8))

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        _paint_option_indicator(self, radio=True)


class SmoothCheckBox(QCheckBox):
    """Checkbox with an antialiased indicator."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(25)
        self.toggled.connect(lambda _checked: self.update())

    def sizeHint(self) -> QSize:  # noqa: N802 - Qt API name
        metrics = QFontMetrics(self.font())
        return QSize(metrics.horizontalAdvance(self.text()) + 34, max(25, metrics.height() + 8))

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        _paint_option_indicator(self, radio=False)


class GardenComboBox(QComboBox):
    """Combo box that pauses ambient repainting while its popup is open."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("gardenSelect")

    def showPopup(self) -> None:  # noqa: N802 - Qt API name
        backdrop = getattr(self.window(), "backdrop", None)
        if backdrop:
            backdrop.set_ambient_running(False)
        super().showPopup()

    def hidePopup(self) -> None:  # noqa: N802 - Qt API name
        super().hidePopup()
        backdrop = getattr(self.window(), "backdrop", None)
        if backdrop:
            QTimer.singleShot(80, lambda: backdrop.set_ambient_running(True))

    def wheelEvent(self, event) -> None:  # noqa: N802 - Qt API name
        # Keep the selected category stable while the user scrolls the settings page.
        event.ignore()


class SafeSlider(QSlider):
    """A slider changed by drag/click only, never by an accidental wheel event."""

    def wheelEvent(self, event) -> None:  # noqa: N802 - Qt API name
        event.ignore()


class GardenToggle(QCheckBox):
    """Compact No/Yes switch used where a full checkbox would feel heavy."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText("")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(42, 22)
        self.toggled.connect(lambda _checked: self.update())

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        palette = getattr(self.window(), "theme_palette", None)
        track = palette.accent_alt if palette and self.isChecked() else (palette.muted if palette else QColor("#718092"))
        outline = palette.text if palette else QColor("#edf3f5")
        knob = palette.text if palette else QColor("#ffffff")
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(outline, 2.2))
        painter.setBrush(track)
        painter.drawRoundedRect(QRectF(1, 2, 40, 18), 9, 9)
        painter.setPen(Qt.NoPen)
        painter.setBrush(knob)
        painter.drawEllipse(QPointF(31 if self.isChecked() else 11, 11), 7, 7)
        painter.end()
