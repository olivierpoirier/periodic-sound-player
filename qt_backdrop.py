from __future__ import annotations

import math
import random
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPixmap, QRadialGradient
from PySide6.QtWidgets import QWidget

from app_config import MODES
from image_loader import load_qimage, load_pixmap
from qt_theme import ThemePalette


class PrankBackdrop(QWidget):
    """Animated night-garden backdrop kept intentionally low-cost."""

    def __init__(self, themes_dir: Path, selected_theme: str = "") -> None:
        super().__init__()
        self.tick = 0
        self.ambient_enabled = True
        self.ambient_running = True
        self.themes_dir = themes_dir
        self.themes = self._discover_themes()
        self.current_theme = ""
        self.background = QPixmap()
        self.palette = self._palette_from_image(QImage())
        self._cached_background_size = QSize()
        self._cached_background = QPixmap()
        self.set_theme(selected_theme)
        self.petals = [
            (
                random.random(),
                random.random(),
                random.uniform(0.18, 0.55),
                random.randrange(4),
                random.uniform(-0.55, 0.55),
            )
            for _ in range(16)
        ]
        self.fireflies = [
            (
                random.random(),
                random.random(),
                random.uniform(0.35, 0.95),
                random.uniform(0.0, math.pi * 2),
            )
            for _ in range(10)
        ]
        self.backdrop_timer = QTimer(self)
        self.backdrop_timer.timeout.connect(self._advance)
        self._sync_ambient_timer()

    def next_theme_name(self) -> str:
        if not self.themes:
            return ""
        current_index = next((index for index, path in enumerate(self.themes) if path.name == self.current_theme), -1)
        return self.themes[(current_index + 1) % len(self.themes)].name

    def theme_path(self, theme_name: str) -> Path | None:
        return next((path for path in self.themes if path.name == theme_name), None)

    @staticmethod
    def _hsv(hue: int, saturation: int, value: int) -> QColor:
        color = QColor()
        color.setHsv(hue % 360, max(0, min(255, saturation)), max(0, min(255, value)))
        return color

    @staticmethod
    def _blend(first: QColor, second: QColor, amount: float) -> QColor:
        amount = max(0.0, min(1.0, amount))
        return QColor(
            round(first.red() + (second.red() - first.red()) * amount),
            round(first.green() + (second.green() - first.green()) * amount),
            round(first.blue() + (second.blue() - first.blue()) * amount),
        )

    def _palette_from_image(self, image: QImage) -> ThemePalette:
        if image.isNull():
            image = QImage(1, 1, QImage.Format.Format_RGB32)
            image.fill(QColor.fromHsv(260, 110, 60))
        image = image.convertToFormat(QImage.Format.Format_RGB32)
        step_x = max(1, image.width() // 48)
        step_y = max(1, image.height() // 32)
        buckets: dict[tuple[int, int, int], int] = {}
        hue_total = saturation_total = value_total = samples = 0
        for y in range(0, image.height(), step_y):
            for x in range(0, image.width(), step_x):
                color = image.pixelColor(x, y)
                hue, saturation, value, _ = color.getHsv()
                hue = 0 if hue < 0 else hue
                bucket = (hue // 12, saturation // 32, value // 32)
                buckets[bucket] = buckets.get(bucket, 0) + 1
                hue_total += hue
                saturation_total += saturation
                value_total += value
                samples += 1

        average_hue = hue_total // max(1, samples)
        average_saturation = saturation_total // max(1, samples)
        average_value = value_total // max(1, samples)
        colorful = [
            (count * (saturation + 24) * (value + 18), hue * 12, saturation * 32, value * 32)
            for (hue, saturation, value), count in buckets.items()
            if saturation >= 2 and value >= 2
        ]
        colorful.sort(reverse=True)
        _, accent_hue, accent_saturation, accent_value = colorful[0] if colorful else (1, average_hue, average_saturation, average_value)
        secondary = next(
            (
                item
                for item in colorful[1:]
                if abs(item[1] - accent_hue) > 44
            ),
            colorful[1] if len(colorful) > 1 else (1, (accent_hue + 46) % 360, accent_saturation, accent_value),
        )
        _, secondary_hue, secondary_saturation, secondary_value = secondary

        base = self._hsv(average_hue, max(14, average_saturation // 3), max(14, min(48, average_value // 5)))
        surface = self._hsv(average_hue, max(12, average_saturation // 3), max(24, min(66, average_value // 4)))
        surface_alt = self._hsv(secondary_hue, max(12, secondary_saturation // 3), max(30, min(82, secondary_value // 3)))
        accent = self._hsv(accent_hue, max(78, accent_saturation), max(142, accent_value))
        accent_alt = self._hsv(secondary_hue, max(68, secondary_saturation), max(136, secondary_value))
        text = self._hsv(accent_hue, min(20, max(6, accent_saturation // 8)), 250)
        muted = self._hsv(average_hue, min(34, max(8, average_saturation // 5)), 210)
        mode_colors = (
            accent,
            self._blend(accent, accent_alt, 0.22),
            self._blend(accent, text, 0.16),
            accent_alt,
            self._blend(accent_alt, text, 0.18),
            self._blend(accent, accent_alt, 0.58),
            self._blend(accent_alt, text, 0.36),
        )
        mode_accents = {mode.key: mode_colors[index] for index, mode in enumerate(MODES)}
        return ThemePalette(base, surface, surface_alt, accent, accent_alt, text, muted, mode_accents)

    def _discover_themes(self) -> list[Path]:
        return sorted(
            [path for path in self.themes_dir.iterdir() if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".avif"}],
            key=lambda path: path.name.casefold(),
        ) if self.themes_dir.is_dir() else []

    def refresh_themes(self) -> None:
        self.themes = self._discover_themes()

    def set_theme(self, theme_name: str) -> str:
        if not self.themes:
            return ""
        fallback = next((path for path in self.themes if path.name == "pexels-jordicosta-32167957.jpg"), self.themes[0])
        theme = next((path for path in self.themes if path.name == theme_name), fallback)
        pixmap = load_pixmap(theme)
        if pixmap.isNull():
            return self.current_theme
        self.background = pixmap
        self.palette = self._palette_from_image(pixmap.toImage())
        self.current_theme = theme.name
        self._cached_background_size = QSize()
        self._cached_background = QPixmap()
        self.update()
        return self.current_theme

    def apply_theme_image(self, theme_name: str, image: QImage) -> str:
        if image.isNull() or not self.theme_path(theme_name):
            return self.current_theme
        self.background = QPixmap.fromImage(image)
        self.palette = self._palette_from_image(image)
        self.current_theme = theme_name
        self._cached_background_size = QSize()
        self._cached_background = QPixmap()
        self.update()
        return self.current_theme

    def next_theme(self) -> str:
        if not self.themes:
            return ""
        return self.set_theme(self.next_theme_name())

    def _advance(self) -> None:
        self.tick += 1
        self.update()

    def set_ambient_running(self, running: bool) -> None:
        self.ambient_running = running
        self._sync_ambient_timer()

    def set_ambient_enabled(self, enabled: bool) -> None:
        self.ambient_enabled = enabled
        self._sync_ambient_timer()
        self.update()

    def _sync_ambient_timer(self) -> None:
        should_run = self.ambient_enabled and self.ambient_running
        if should_run and not self.backdrop_timer.isActive():
            self.backdrop_timer.start(50)
        elif not should_run and self.backdrop_timer.isActive():
            self.backdrop_timer.stop()

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        width = max(1, self.width())
        height = max(1, self.height())

        if not self.background.isNull():
            target_size = QSize(width, height)
            if self._cached_background_size != target_size:
                self._cached_background = self.background.scaled(
                    target_size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
                )
                self._cached_background_size = target_size
            x = (width - self._cached_background.width()) // 2
            y = (height - self._cached_background.height()) // 2
            painter.drawPixmap(x, y, self._cached_background)
        else:
            base = QLinearGradient(0, 0, width, height)
            base.setColorAt(0.00, self.palette.base)
            base.setColorAt(0.45, self.palette.surface)
            base.setColorAt(1.00, self.palette.surface_alt)
            painter.fillRect(self.rect(), base)

        self._draw_lantern_glow(painter, width, height)

        painter.fillRect(self.rect(), QColor(self.palette.base.red(), self.palette.base.green(), self.palette.base.blue(), 56))

        focus = QRadialGradient(QPointF(width * 0.50, height * 0.43), width * 0.56)
        focus.setColorAt(0.00, QColor(self.palette.text.red(), self.palette.text.green(), self.palette.text.blue(), 12))
        focus.setColorAt(0.46, QColor(self.palette.accent_alt.red(), self.palette.accent_alt.green(), self.palette.accent_alt.blue(), 8))
        focus.setColorAt(1.00, QColor(self.palette.base.red(), self.palette.base.green(), self.palette.base.blue(), 0))
        painter.fillRect(self.rect(), focus)

        vignette = QRadialGradient(QPointF(width * 0.50, height * 0.48), width * 0.82)
        vignette.setColorAt(0.00, QColor(self.palette.base.red(), self.palette.base.green(), self.palette.base.blue(), 0))
        vignette.setColorAt(0.62, QColor(self.palette.base.red(), self.palette.base.green(), self.palette.base.blue(), 18))
        vignette.setColorAt(1.00, QColor(self.palette.base.red(), self.palette.base.green(), self.palette.base.blue(), 88))
        painter.fillRect(self.rect(), vignette)

        if not self.ambient_enabled:
            return

        for index, (x_ratio, y_ratio, speed, phase) in enumerate(self.fireflies):
            x = x_ratio * width + math.sin(self.tick / 32 + phase) * 22
            y = y_ratio * height + math.cos(self.tick / 40 + phase) * 14
            pulse = 0.38 + 0.28 * math.sin(self.tick / 13 + phase)
            glow = QRadialGradient(QPointF(x, y), 14)
            glow.setColorAt(0.00, QColor(self.palette.accent.red(), self.palette.accent.green(), self.palette.accent.blue(), int(54 * pulse)))
            glow.setColorAt(0.45, QColor(self.palette.accent_alt.red(), self.palette.accent_alt.green(), self.palette.accent_alt.blue(), int(18 * pulse)))
            glow.setColorAt(1.00, QColor(self.palette.accent_alt.red(), self.palette.accent_alt.green(), self.palette.accent_alt.blue(), 0))
            painter.fillRect(QRectF(x - 14, y - 14, 28, 28), glow)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self.palette.text.red(), self.palette.text.green(), self.palette.text.blue(), int(82 * pulse)))
            painter.drawEllipse(QPointF(x, y), 1.6, 1.6)

        petal_colors = (self.palette.accent, self.palette.accent_alt, self.palette.text, self.palette.muted)
        for index, (x_ratio, y_ratio, speed, color_index, tilt) in enumerate(self.petals):
            y = (y_ratio * height + self.tick * speed * 1.05) % (height + 46) - 23
            x = x_ratio * width + math.sin((self.tick + index * 13) / 31) * 20
            painter.save()
            painter.translate(x, y)
            painter.rotate((self.tick * tilt + index * 19) % 360)
            painter.setPen(Qt.NoPen)
            petal_color = petal_colors[color_index % len(petal_colors)]
            painter.setBrush(QColor(petal_color.red(), petal_color.green(), petal_color.blue(), 105))
            painter.setOpacity(0.30)
            painter.drawEllipse(QRectF(-5, -2.2, 10, 4.4))
            painter.restore()

    def _draw_lantern_glow(self, painter: QPainter, width: int, height: int) -> None:
        """Paint soft breathing light near the illustrated lantern areas."""
        pulse = 0.72 + 0.18 * math.sin(self.tick / 22)
        lanterns = (
            (0.045, 0.64, 0.17, 24),
            (0.18, 0.12, 0.20, 14),
            (0.79, 0.16, 0.20, 12),
        )
        for x_ratio, y_ratio, radius_ratio, alpha in lanterns:
            center = QPointF(width * x_ratio, height * y_ratio)
            radius = max(width, height) * radius_ratio
            glow = QRadialGradient(center, radius)
            glow.setColorAt(0.00, QColor(self.palette.accent.red(), self.palette.accent.green(), self.palette.accent.blue(), int(alpha * pulse)))
            glow.setColorAt(0.36, QColor(self.palette.accent_alt.red(), self.palette.accent_alt.green(), self.palette.accent_alt.blue(), int(alpha * 0.38 * pulse)))
            glow.setColorAt(1.00, QColor(self.palette.accent_alt.red(), self.palette.accent_alt.green(), self.palette.accent_alt.blue(), 0))
            painter.fillRect(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), glow)
