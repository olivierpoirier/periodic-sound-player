from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFontMetrics, QIcon, QPainter, QPen
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSlider,
    QTabBar,
    QStyle,
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
    "helpShell": ("base", 226, "text", 148, 0, 1.7),
    "helpStepsPanel": ("surface", 220, "text", 140, 15, 1.6),
    "helpPage": ("surface_alt", 218, "text", 146, 18, 1.6),
    "helpExample": ("surface", 158, "text", 112, 12, 1.45),
    "updateShell": ("base", 232, "text", 144, 0, 1.7),
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

LABEL_SURFACE_STYLES = {
    "filePill": ("surface_alt", 82, "text", 108, 10, 1.5),
    "imagePreview": ("base", 112, "text", 106, 15, 1.5),
    "modeChip": ("base", 184, "accent", 160, 12, 1.5),
    "updateDetail": ("surface", 152, "text", 112, 11, 1.45),
}


def _with_alpha(color: QColor, alpha: int) -> QColor:
    result = QColor(color)
    result.setAlpha(alpha)
    return result


def _palette_color(palette, name: str, fallback: str) -> QColor:
    return QColor(getattr(palette, name, QColor(fallback)))


def _draw_smooth_panel(
    painter: QPainter,
    widget: QWidget,
    rect: QRectF,
    bg_name: str,
    bg_alpha: int,
    border_name: str,
    border_alpha: int,
    radius: float,
    pen_width: float,
) -> None:
    palette = getattr(widget.window(), "theme_palette", None)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setBrush(_with_alpha(_palette_color(palette, bg_name, "#111111"), bg_alpha))
    border_color = widget.property("smoothBorderColor")
    if isinstance(border_color, QColor):
        pen_color = _with_alpha(border_color, border_alpha)
    else:
        pen_color = _with_alpha(_palette_color(palette, border_name, "#edf3f5"), border_alpha)
    pen = QPen(pen_color, pen_width)
    pen.setJoinStyle(Qt.RoundJoin)
    painter.setPen(pen)
    painter.drawRoundedRect(rect, radius, radius)


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
        if not style:
            super().paintEvent(event)
            return

        bg_name, bg_alpha, border_name, border_alpha, radius, pen_width = style
        if object_name == "modeCard":
            if self.property("active") is True:
                bg_name, bg_alpha, border_name, border_alpha = "surface_alt", 132, "accent", 162
            elif self.underMouse():
                bg_name, bg_alpha, border_name, border_alpha = "surface", 122, "accent", 142

        painter = QPainter(self)
        inset = pen_width / 2 + 0.6
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        _draw_smooth_panel(painter, self, rect, bg_name, bg_alpha, border_name, border_alpha, radius, pen_width)
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
        pen_width = 1.6
        top = 10.0
        rect = QRectF(0.9, top, self.width() - 1.8, self.height() - top - 0.9)
        _draw_smooth_panel(painter, self, rect, "base", 108, "text", 86, 18, pen_width)

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
        pen_width = 1.6
        inset = pen_width / 2 + 0.35
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        _draw_smooth_panel(painter, self, rect, bg_name, bg_alpha, border_name, border_alpha, radius, pen_width)
        self._paint_centered_label(painter)
        painter.end()

    def _paint_centered_label(self, painter: QPainter) -> None:
        palette = getattr(self.window(), "theme_palette", None)
        text_color = _palette_color(palette, "text", "#edf3f5")
        if not self.isEnabled():
            text_color = _with_alpha(text_color, 118)
        painter.setPen(text_color)
        painter.setFont(self.font())

        text = self.text()
        icon = self.icon()
        has_icon = not icon.isNull()
        has_text = bool(text)
        content_rect = self.rect().adjusted(12, 0, -12, 0)
        icon_size = self.iconSize() if has_icon else QSize()
        metrics = QFontMetrics(self.font())
        spacing = 7 if has_icon and has_text else 0
        available_text_width = max(0, content_rect.width() - (icon_size.width() if has_icon else 0) - spacing)
        display_text = metrics.elidedText(text, Qt.ElideRight, available_text_width) if has_text else ""
        text_width = metrics.horizontalAdvance(display_text) if has_text else 0
        total_width = (icon_size.width() if has_icon else 0) + spacing + text_width
        x = content_rect.left() + max(0, (content_rect.width() - total_width) / 2)

        if has_icon:
            mode = QIcon.Mode.Normal if self.isEnabled() else QIcon.Mode.Disabled
            pixmap = icon.pixmap(icon_size, mode)
            y = content_rect.top() + (content_rect.height() - icon_size.height()) / 2
            painter.drawPixmap(int(x), int(y), pixmap)
            x += icon_size.width() + spacing

        if has_text:
            text_rect = QRectF(x, content_rect.top(), text_width, content_rect.height())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, display_text)


class SmoothLabel(QLabel):
    """Label surface with painter-drawn rounded borders for preview and chip UI."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        style = LABEL_SURFACE_STYLES.get(self.objectName())
        if style:
            bg_name, bg_alpha, border_name, border_alpha, radius, pen_width = style
            if self.underMouse() and self.objectName() == "imagePreview":
                bg_alpha += 10
                border_name = "accent"
                border_alpha += 28
            painter = QPainter(self)
            inset = pen_width / 2 + 0.45
            rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
            _draw_smooth_panel(painter, self, rect, bg_name, bg_alpha, border_name, border_alpha, radius, pen_width)
            painter.end()
        super().paintEvent(event)

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.update()
        super().leaveEvent(event)


class SmoothLineEdit(QLineEdit):
    """Line edit with antialiased rounded border painted outside the text layer."""

    def __init__(self, text: str = "", parent: QWidget | None = None) -> None:
        super().__init__(text, parent)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        bg_name, bg_alpha, border_name, border_alpha, radius = "base", 120, "text", 116, 10
        if self.objectName() == "gardenInput":
            bg_name, bg_alpha, border_alpha, radius = "surface", 128, 122, 11
        if self.hasFocus():
            border_name, border_alpha, bg_alpha = "accent", 188, max(bg_alpha, 134)
        elif self.underMouse():
            border_name, border_alpha = "accent", 150
        if not self.isEnabled():
            bg_alpha, border_alpha = 62, 58

        painter = QPainter(self)
        pen_width = 1.55
        inset = pen_width / 2 + 0.45
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        _draw_smooth_panel(painter, self, rect, bg_name, bg_alpha, border_name, border_alpha, radius, pen_width)
        painter.end()

        super().paintEvent(event)


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
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        bg_name, bg_alpha, border_name, border_alpha, radius = "surface", 128, "text", 122, 11
        if self.hasFocus():
            border_name, border_alpha, bg_alpha = "accent", 188, 134
        elif self.underMouse():
            border_name, border_alpha = "accent", 150
        if not self.isEnabled():
            bg_alpha, border_alpha = 62, 58

        painter = QPainter(self)
        pen_width = 1.55
        inset = pen_width / 2 + 0.45
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        _draw_smooth_panel(painter, self, rect, bg_name, bg_alpha, border_name, border_alpha, radius, pen_width)
        painter.end()
        super().paintEvent(event)

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

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.setCursor(Qt.PointingHandCursor)
        self.setMouseTracking(True)
        self.setMinimumHeight(26)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        palette = getattr(self.window(), "theme_palette", None)
        text_color = _palette_color(palette, "text", "#edf3f5")
        muted_color = _palette_color(palette, "muted", "#718092")
        accent_color = _palette_color(palette, "accent", "#79a8a8")
        accent_alt_color = _palette_color(palette, "accent_alt", "#4f8cff")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        center_y = self.height() / 2
        handle_radius = 11.0
        track_left = handle_radius + 1.0
        track_right = max(track_left + 1.0, self.width() - handle_radius - 1.0)
        track_width = track_right - track_left
        position = QStyle.sliderPositionFromValue(
            self.minimum(),
            self.maximum(),
            self.sliderPosition(),
            int(track_width),
            self.invertedAppearance(),
        )
        handle_center = QPointF(track_left + position, center_y)
        track_rect = QRectF(track_left, center_y - 3.4, track_width, 6.8)
        fill_rect = QRectF(track_left, track_rect.top(), max(0.0, handle_center.x() - track_left), track_rect.height())

        painter.setPen(QPen(_with_alpha(text_color, 86), 1.35))
        painter.setBrush(_with_alpha(muted_color, 86))
        painter.drawRoundedRect(track_rect, 3.4, 3.4)

        if fill_rect.width() > 0.5:
            painter.setPen(Qt.NoPen)
            painter.setBrush(_with_alpha(accent_alt_color, 184))
            painter.drawRoundedRect(fill_rect, 3.4, 3.4)

        if self.underMouse() and self.isEnabled():
            outer_alpha = 230
            inner_alpha = 232
            outer_width = 1.8
        else:
            outer_alpha = 198
            inner_alpha = 214
            outer_width = 1.55
        if not self.isEnabled():
            outer_alpha = 102
            inner_alpha = 94

        painter.setPen(QPen(_with_alpha(text_color, outer_alpha), outer_width))
        painter.setBrush(_with_alpha(accent_color, inner_alpha))
        painter.drawEllipse(handle_center, handle_radius, handle_radius)

        painter.setPen(QPen(_with_alpha(text_color, 62), 1.0))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(handle_center, handle_radius - 3.2, handle_radius - 3.2)
        painter.end()

    def enterEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.update()
        super().leaveEvent(event)

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
