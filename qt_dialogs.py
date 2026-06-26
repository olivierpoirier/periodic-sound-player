from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QMovie, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QStackedWidget, QVBoxLayout, QWidget

from image_loader import load_pixmap
from qt_widgets import PaintedButton


HELP_DIALOG_QSS = """
QDialog { background: #100f19; color: #fff7ec; }
#helpShell {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #221a29, stop:0.58 #171724, stop:1 #302033);
    border: 2px solid rgba(249, 218, 190, 132);
    border-radius: 22px;
}
#helpHeading { color: #fff7ec; font-size: 24px; font-weight: 800; }
#helpSubheading { color: #dccfce; font-size: 14px; }
#helpSteps {
    background: rgba(9, 10, 17, 110);
    border: 2px solid rgba(247, 222, 203, 82);
    border-radius: 15px;
    padding: 7px;
    outline: 0;
}
#helpSteps::item {
    color: #eee2dd;
    border-radius: 10px;
    padding: 12px 10px;
    margin: 2px;
}
#helpSteps::item:selected { background: rgba(217, 159, 157, 98); color: #fff9ef; }
#helpSteps::item:hover { background: rgba(232, 191, 115, 44); }
#helpPage {
    background: rgba(12, 14, 22, 118);
    border: 2px solid rgba(245, 220, 200, 92);
    border-radius: 18px;
}
#helpPageTitle { color: #efc878; font-size: 21px; font-weight: 800; }
#helpPageText { color: #eee4df; font-size: 16px; line-height: 1.45; }
QPushButton {
    background: rgba(78, 61, 70, 188);
    border: 2px solid rgba(255, 225, 201, 102);
    border-radius: 11px;
    padding: 9px 16px;
    color: #fff7ee;
    font-weight: 700;
}
QPushButton:hover { background: rgba(112, 80, 86, 206); border-color: rgba(240, 197, 138, 146); }
QPushButton:disabled { color: rgba(255, 247, 238, 72); background: rgba(56, 49, 57, 90); }
QPushButton#secondaryButton { background: rgba(76, 91, 111, 184); }
"""


def build_help_dialog_qss(palette) -> str:
    rgba = palette.rgba
    text = palette.hex(palette.text)
    muted = palette.hex(palette.muted)
    accent = palette.hex(palette.accent)
    return f"""
QDialog {{ background: {rgba(palette.base, 238)}; color: {text}; }}
#helpShell {{
    background: {rgba(palette.base, 226)};
    border: 2px solid {rgba(palette.text, 148)};
    border-radius: 22px;
}}
#helpHeading {{ color: {text}; font-size: 24px; font-weight: 800; }}
#helpSubheading {{ color: {muted}; font-size: 14px; }}
#helpSteps {{
    background: {rgba(palette.surface, 220)};
    border: 2px solid {rgba(palette.text, 140)};
    border-radius: 15px;
    padding: 7px;
    outline: 0;
}}
#helpSteps::item {{
    color: {text};
    border-radius: 10px;
    padding: 12px 10px;
    margin: 2px;
}}
#helpSteps::item:selected {{ background: {rgba(palette.accent_alt, 176)}; color: {text}; }}
#helpSteps::item:hover {{ background: {rgba(palette.accent_alt, 102)}; }}
#helpPage {{
    background: {rgba(palette.surface_alt, 218)};
    border: 2px solid {rgba(palette.text, 146)};
    border-radius: 18px;
}}
#helpPageTitle {{ color: {accent}; font-size: 21px; font-weight: 800; }}
#helpPageText {{ color: {text}; font-size: 16px; line-height: 1.45; }}
QPushButton {{
    background: {rgba(palette.surface_alt, 224)};
    border: 2px solid {rgba(palette.text, 148)};
    border-radius: 10px;
    padding: 9px 16px;
    color: {text};
    font-weight: 700;
}}
QPushButton:hover {{ background: {rgba(palette.accent_alt, 198)}; border-color: {rgba(palette.accent, 172)}; }}
QPushButton:disabled {{ color: {rgba(palette.muted, 112)}; background: {rgba(palette.surface, 118)}; }}
QPushButton#secondaryButton {{ background: {rgba(palette.surface, 196)}; }}
"""


class HelpDialog(QDialog):
    """Friendly, clickable walkthrough for people discovering the app."""

    def __init__(self, parent: QWidget, language: str) -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle("SoundMaker Guide")
        self.setMinimumSize(850, 560)
        self.resize(940, 600)
        palette = getattr(parent, "theme_palette", None)
        self.theme_palette = palette
        self.setStyleSheet(build_help_dialog_qss(palette) if palette else HELP_DIALOG_QSS)

        outer = QFrame()
        outer.setObjectName("helpShell")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(22, 20, 22, 18)
        outer_layout.setSpacing(14)

        heading = QLabel("Guide rapide" if language == "fr" else "Quick guide")
        heading.setObjectName("helpHeading")
        subheading = QLabel(
            "On prépare votre prochaine farce, une étape à la fois."
            if language == "fr"
            else "Set up your next prank one simple step at a time."
        )
        subheading.setObjectName("helpSubheading")
        outer_layout.addWidget(heading)
        outer_layout.addWidget(subheading)

        body = QHBoxLayout()
        body.setSpacing(16)
        self.steps = QListWidget()
        self.steps.setObjectName("helpSteps")
        self.steps.setFixedWidth(205)
        self.pages = QStackedWidget()
        self.pages.setObjectName("helpPages")
        self.step_data = self._guide_steps()
        for title, text in self.step_data:
            self.steps.addItem(title)
            self.pages.addWidget(self._page(title, text))
        self.steps.currentRowChanged.connect(self._set_step)
        body.addWidget(self.steps)
        body.addWidget(self.pages, 1)
        outer_layout.addLayout(body, 1)

        controls = QHBoxLayout()
        self.previous_button = PaintedButton("Précédent" if language == "fr" else "Previous")
        self.next_button = PaintedButton("Suivant" if language == "fr" else "Next")
        close_button = PaintedButton("Fermer le guide" if language == "fr" else "Close guide")
        close_button.setObjectName("secondaryButton")
        self.previous_button.clicked.connect(lambda: self._set_step(self.pages.currentIndex() - 1))
        self.next_button.clicked.connect(lambda: self._set_step(self.pages.currentIndex() + 1))
        close_button.clicked.connect(self.accept)
        controls.addWidget(self.previous_button)
        controls.addWidget(self.next_button)
        controls.addStretch(1)
        controls.addWidget(close_button)
        outer_layout.addLayout(controls)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(outer)
        self._set_step(0)

    def _guide_steps(self) -> list[tuple[str, str]]:
        if self.language == "fr":
            return [
                ("1. Bienvenue", "SoundMaker crée des surprises sonores et visuelles à intervalle choisi. Commencez tranquillement : un seul mode est actif à la fois."),
                ("2. Choisissez un mode", "Dans le panneau de droite, choisissez ce que vous voulez déclencher : sons, meme, fausse erreur, notification ou chaos. Les options de gauche changent immédiatement pour vous montrer seulement ce qui est utile."),
                ("3. Réglez le rythme", "À gauche, ajustez le minimum et le maximum. Les deux curseurs restent toujours cohérents : le minimum ne dépassera jamais le maximum. Utilisez Tester maintenant pour essayer sans attendre."),
                ("4. Préparez vos médias", "Ajoutez vos images, GIFs et sons dans la bibliothèque. Les sous-dossiers deviennent des catégories. Pour un meme, choisissez votre texte, sa couleur, sa position et, si vous le souhaitez, un son précis."),
                ("5. Gardez le contrôle", "Pause arrête temporairement les déclenchements. Le bouton de langue garde votre choix pour la prochaine ouverture. Le menu contient le mode camouflage, l'aide et la vérification des mises à jour."),
            ]
        return [
            ("1. Welcome", "SoundMaker creates timed sound and visual surprises. Start simply: only one mode is active at a time."),
            ("2. Choose a mode", "Use the right panel to choose sounds, a meme, a fake error, a notification, or chaos. The left panel immediately shows only the controls that belong to that mode."),
            ("3. Set the timing", "Adjust the minimum and maximum on the left. The sliders stay in sync, so the minimum never exceeds the maximum. Use Test now to try a setup without waiting."),
            ("4. Add your media", "Import images, GIFs, and sounds through the library. Subfolders become categories. For memes, choose the caption, color, placement, and an optional matching sound."),
            ("5. Stay in control", "Pause temporarily stops events. Your language is remembered for next time. The menu includes camouflage, this guide, and the update check."),
        ]

    def _page(self, title: str, text: str) -> QWidget:
        page = QFrame()
        page.setObjectName("helpPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(14)
        title_label = QLabel(title)
        title_label.setObjectName("helpPageTitle")
        text_label = QLabel(text)
        text_label.setObjectName("helpPageText")
        text_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(text_label)
        layout.addStretch(1)
        return page

    def _set_step(self, index: int) -> None:
        index = max(0, min(index, len(self.step_data) - 1))
        self.steps.blockSignals(True)
        self.steps.setCurrentRow(index)
        self.steps.blockSignals(False)
        self.pages.setCurrentIndex(index)
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index < len(self.step_data) - 1)


class MemeCanvas(QWidget):
    """Draws an image or GIF with classic outlined meme text on top of it."""

    def __init__(self, image_path: Path, top_text: str, bottom_text: str, text_color: str) -> None:
        super().__init__()
        self.top_text = top_text.strip()[:120]
        self.bottom_text = bottom_text.strip()[:120]
        self.text_color = QColor(text_color)
        self.pixmap = QPixmap()
        self.movie: QMovie | None = None

        if image_path.suffix.lower() == ".gif":
            self.movie = QMovie(str(image_path))
            self.movie.jumpToFrame(0)
            source_size = self.movie.frameRect().size()
            if source_size.isEmpty():
                source_size = self.movie.currentPixmap().size()
            self.movie.frameChanged.connect(self.update)
            self.movie.start()
        else:
            self.pixmap = load_pixmap(image_path)
            source_size = self.pixmap.size()

        if source_size.isEmpty():
            source_size = QSize(640, 400)
        source_size.scale(QSize(760, 560), Qt.KeepAspectRatio)
        self.setFixedSize(source_size)

    def paintEvent(self, event) -> None:  # noqa: N802 - Qt API name
        painter = QPainter(self)
        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.fillRect(self.rect(), Qt.black)
        pixmap = self.movie.currentPixmap() if self.movie else self.pixmap
        if pixmap.isNull():
            return
        target = QRectF(self.rect())
        source = pixmap.size()
        source.scale(self.size(), Qt.KeepAspectRatio)
        target.setSize(source)
        target.moveCenter(QPointF(self.width() / 2, self.height() / 2))
        painter.drawPixmap(target, pixmap, QRectF(pixmap.rect()))
        self._draw_caption(painter, target, self.top_text, top=True)
        self._draw_caption(painter, target, self.bottom_text, top=False)

    def _draw_caption(self, painter: QPainter, image_rect: QRectF, text: str, top: bool) -> None:
        if not text:
            return
        font = QFont("Impact")
        font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
        font.setPixelSize(max(24, int(image_rect.height() * (0.105 if len(text) < 42 else 0.078))))
        font.setWeight(QFont.Weight.Black)
        painter.setFont(font)
        margin = max(16, int(image_rect.width() * 0.035))
        height = image_rect.height() * 0.34
        text_rect = QRectF(
            image_rect.left() + margin,
            image_rect.top() + 10 if top else image_rect.bottom() - height - 10,
            image_rect.width() - margin * 2,
            height,
        )
        alignment = Qt.AlignHCenter | (Qt.AlignTop if top else Qt.AlignBottom) | Qt.TextWordWrap
        display_text = text.upper()
        painter.setPen(QColor(0, 0, 0, 235))
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)):
            painter.drawText(text_rect.translated(dx, dy), alignment, display_text)
        painter.setPen(self.text_color)
        painter.drawText(text_rect, alignment, display_text)

    def stop(self) -> None:
        if self.movie:
            self.movie.stop()


class MemeDialog(QDialog):
    def __init__(
        self,
        parent: QWidget | None,
        image_path: Path,
        top_text: str,
        bottom_text: str,
        duration_seconds: float,
        text_color: str,
        stop_sound: Callable[[], None] | None,
    ) -> None:
        super().__init__(parent)
        self.stop_sound = stop_sound
        self.canvas = MemeCanvas(image_path, top_text, bottom_text, text_color)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setStyleSheet("QDialog { background: #000000; }")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self.setFixedSize(self.canvas.size())
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.center() - self.rect().center())
        QTimer.singleShot(max(250, int(duration_seconds * 1000)), self.close)

    def closeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        self.canvas.stop()
        if self.stop_sound:
            self.stop_sound()
        event.accept()
