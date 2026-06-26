from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap, QRadialGradient

from qt_theme import ThemePalette


def prank_app_icon(palette: ThemePalette) -> QIcon:
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    halo = QRadialGradient(QPointF(32, 33), 30)
    halo.setColorAt(0.00, QColor(palette.accent.red(), palette.accent.green(), palette.accent.blue(), 92))
    halo.setColorAt(0.55, QColor(palette.accent_alt.red(), palette.accent_alt.green(), palette.accent_alt.blue(), 52))
    halo.setColorAt(1.00, QColor(palette.base.red(), palette.base.green(), palette.base.blue(), 0))
    painter.fillRect(QRectF(0, 0, 64, 64), halo)

    painter.setPen(QPen(QColor(palette.text.red(), palette.text.green(), palette.text.blue(), 210), 2))
    painter.setBrush(QColor(palette.base.red(), palette.base.green(), palette.base.blue(), 232))
    painter.drawRoundedRect(QRectF(12, 17, 40, 33), 9, 9)

    painter.setPen(QPen(QColor(palette.accent.red(), palette.accent.green(), palette.accent.blue(), 210), 2))
    painter.drawLine(QPointF(17, 28), QPointF(47, 28))
    painter.drawLine(QPointF(24, 17), QPointF(24, 50))
    painter.drawLine(QPointF(40, 17), QPointF(40, 50))

    painter.setPen(QPen(QColor(palette.text.red(), palette.text.green(), palette.text.blue(), 235), 2))
    question_font = QFont("Segoe UI")
    question_font.setPixelSize(22)
    question_font.setWeight(QFont.Weight.Black)
    painter.setFont(question_font)
    painter.drawText(QRectF(13, 14, 38, 34), Qt.AlignCenter, "?")

    painter.setPen(Qt.NoPen)
    flower_center = QPointF(47, 16)
    painter.setBrush(QColor(palette.accent_alt.red(), palette.accent_alt.green(), palette.accent_alt.blue(), 235))
    for angle in range(0, 360, 72):
        painter.save()
        painter.translate(flower_center)
        painter.rotate(angle)
        painter.drawEllipse(QRectF(-2.2, -7.0, 4.4, 7.0))
        painter.restore()
    painter.setBrush(QColor(palette.accent.red(), palette.accent.green(), palette.accent.blue(), 245))
    painter.drawEllipse(flower_center, 2.0, 2.0)

    painter.setBrush(QColor(palette.muted.red(), palette.muted.green(), palette.muted.blue(), 220))
    painter.drawEllipse(QRectF(16, 44, 9, 5))
    painter.drawEllipse(QRectF(39, 45, 8, 4))
    painter.end()
    return QIcon(pixmap)


def coffee_sakura_icon(palette: ThemePalette) -> QIcon:
    pixmap = QPixmap(34, 34)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing, True)

    painter.setPen(QPen(QColor(palette.text.red(), palette.text.green(), palette.text.blue(), 214), 1.3))
    painter.setBrush(QColor(palette.text.red(), palette.text.green(), palette.text.blue(), 232))
    painter.drawRoundedRect(QRectF(7, 13, 17, 13), 4, 4)
    painter.setPen(QPen(QColor(palette.text.red(), palette.text.green(), palette.text.blue(), 190), 1.4))
    painter.setBrush(Qt.NoBrush)
    painter.drawArc(QRectF(20, 15, 8, 8), -70 * 16, 220 * 16)

    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(palette.base.red(), palette.base.green(), palette.base.blue(), 210))
    painter.drawEllipse(QRectF(9.5, 15.2, 12.5, 4.4))
    painter.setBrush(QColor(palette.accent.red(), palette.accent.green(), palette.accent.blue(), 140))
    painter.drawEllipse(QRectF(12, 15.8, 5.5, 1.8))

    painter.setPen(QPen(QColor(palette.text.red(), palette.text.green(), palette.text.blue(), 150), 1.2))
    for x in (11, 16, 21):
        painter.drawLine(QPointF(x, 10), QPointF(x + 1.8, 6.4))

    flower_center = QPointF(22.8, 12.8)
    painter.setPen(Qt.NoPen)
    painter.setBrush(QColor(palette.accent_alt.red(), palette.accent_alt.green(), palette.accent_alt.blue(), 235))
    for angle in range(0, 360, 72):
        painter.save()
        painter.translate(flower_center)
        painter.rotate(angle)
        painter.drawEllipse(QRectF(-1.4, -5.2, 2.8, 5.2))
        painter.restore()
    painter.setBrush(QColor(palette.accent.red(), palette.accent.green(), palette.accent.blue(), 245))
    painter.drawEllipse(flower_center, 1.35, 1.35)

    painter.setPen(QPen(QColor(palette.base.red(), palette.base.green(), palette.base.blue(), 105), 1.2))
    painter.drawLine(QPointF(6, 27), QPointF(26, 27))
    painter.end()
    return QIcon(pixmap)
