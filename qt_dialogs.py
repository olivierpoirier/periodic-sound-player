from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, QTimer
from PySide6.QtGui import QColor, QFont, QMovie, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QListWidget, QScrollArea, QStackedWidget, QVBoxLayout, QWidget

from image_loader import load_pixmap
from qt_widgets import PaintedButton, SmoothFrame, SmoothLabel


HELP_DIALOG_QSS = """
QDialog { background: #100f19; color: #fff7ec; }
#helpShell {
    background: transparent;
    border: 0;
}
#helpHeading { color: #fff7ec; font-size: 24px; font-weight: 800; }
#helpSubheading { color: #dccfce; font-size: 14px; }
#helpStepsPanel { background: transparent; border: 0; }
#helpSteps {
    background: transparent;
    border: 0;
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
    background: transparent;
    border: 0;
}
#helpPageTitle { color: #efc878; font-size: 21px; font-weight: 800; }
#helpPageText { color: #eee4df; font-size: 16px; line-height: 1.45; }
#helpScroll { background: transparent; border: 0; }
#helpExample {
    background: transparent;
    border: 0;
}
#helpExampleTitle { color: #f2d18a; font-size: 14px; font-weight: 800; }
#helpExampleText { color: #eee4df; font-size: 14px; line-height: 1.35; }
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


UPDATE_DIALOG_QSS = """
QDialog { background: #100f19; color: #fff7ec; font-family: Segoe UI; }
#updateShell {
    background: transparent;
    border: 0;
}
#updateAccent {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #efc878, stop:0.58 #d99f9d, stop:1 #fff7ec);
    border-radius: 3px;
}
#updateKicker { color: #efc878; font-size: 11px; font-weight: 900; }
#updateHeading { color: #fff7ec; font-size: 22px; font-weight: 850; }
#updateMessage { color: #eee4df; font-size: 15px; line-height: 1.4; }
#updateDetail {
    color: #fff7ec;
    background: transparent;
    border: 0;
    padding: 8px 12px;
    font-weight: 750;
}
QPushButton { min-height: 38px; padding: 9px 16px; font-weight: 700; }
"""


def build_help_dialog_qss(palette) -> str:
    rgba = palette.rgba
    text = palette.hex(palette.text)
    muted = palette.hex(palette.muted)
    accent = palette.hex(palette.accent)
    return f"""
QDialog {{ background: {rgba(palette.base, 238)}; color: {text}; font-family: Segoe UI; }}
#helpShell {{
    background: transparent;
    border: 0;
}}
#helpHeading {{ color: {text}; font-size: 24px; font-weight: 800; }}
#helpSubheading {{ color: {muted}; font-size: 14px; }}
#helpStepsPanel {{ background: transparent; border: 0; }}
#helpSteps {{
    background: transparent;
    border: 0;
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
    background: transparent;
    border: 0;
}}
#helpPageTitle {{ color: {accent}; font-size: 21px; font-weight: 800; }}
#helpPageText {{ color: {text}; font-size: 16px; line-height: 1.45; }}
#helpScroll {{ background: transparent; border: 0; }}
#helpExample {{
    background: transparent;
    border: 0;
}}
#helpExampleTitle {{ color: {accent}; font-size: 14px; font-weight: 800; }}
#helpExampleText {{ color: {text}; font-size: 14px; line-height: 1.35; }}
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


def build_update_dialog_qss(palette) -> str:
    rgba = palette.rgba
    text = palette.hex(palette.text)
    muted = palette.hex(palette.muted)
    accent = palette.hex(palette.accent)
    return f"""
QDialog {{ background: {rgba(palette.base, 238)}; color: {text}; }}
#updateShell {{
    background: transparent;
    border: 0;
}}
#updateAccent {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {accent}, stop:0.58 {palette.hex(palette.accent_alt)}, stop:1 {text});
    border-radius: 3px;
}}
#updateKicker {{ color: {accent}; font-size: 11px; font-weight: 900; }}
#updateHeading {{ color: {text}; font-size: 22px; font-weight: 850; }}
#updateMessage {{ color: {text}; font-size: 15px; line-height: 1.4; }}
#updateDetail {{
    color: {text};
    background: transparent;
    border: 0;
    padding: 8px 12px;
    font-weight: 750;
}}
#updateMuted {{ color: {muted}; font-size: 12px; }}
QPushButton {{ min-height: 38px; padding: 9px 16px; font-weight: 700; }}
"""


class UpdateDialog(QDialog):
    """Theme-matched confirmation and status dialog for update checks."""

    def __init__(
        self,
        parent: QWidget,
        title: str,
        kicker: str,
        heading: str,
        message: str,
        primary_text: str,
        secondary_text: str = "",
        detail: str = "",
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        self.resize(560, 260)
        palette = getattr(parent, "theme_palette", None)
        self.theme_palette = palette
        self.setStyleSheet(build_update_dialog_qss(palette) if palette else UPDATE_DIALOG_QSS)

        outer = SmoothFrame()
        outer.setObjectName("updateShell")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(24, 22, 24, 20)
        outer_layout.setSpacing(13)

        accent_line = QFrame()
        accent_line.setObjectName("updateAccent")
        accent_line.setFixedHeight(6)
        outer_layout.addWidget(accent_line)

        kicker_label = QLabel(kicker.upper())
        kicker_label.setObjectName("updateKicker")
        outer_layout.addWidget(kicker_label)

        heading_label = QLabel(heading)
        heading_label.setObjectName("updateHeading")
        heading_label.setWordWrap(True)
        outer_layout.addWidget(heading_label)

        message_label = QLabel(message)
        message_label.setObjectName("updateMessage")
        message_label.setWordWrap(True)
        outer_layout.addWidget(message_label)

        if detail:
            detail_label = SmoothLabel(detail)
            detail_label.setObjectName("updateDetail")
            detail_label.setWordWrap(True)
            outer_layout.addWidget(detail_label)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addStretch(1)
        if secondary_text:
            secondary_button = PaintedButton(secondary_text)
            secondary_button.setObjectName("secondaryButton")
            secondary_button.clicked.connect(self.reject)
            controls.addWidget(secondary_button)
        primary_button = PaintedButton(primary_text)
        primary_button.setObjectName("successButton")
        primary_button.setDefault(True)
        primary_button.clicked.connect(self.accept)
        controls.addWidget(primary_button)
        outer_layout.addLayout(controls)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(outer)


class HelpDialog(QDialog):
    """Friendly, clickable walkthrough for people discovering the app."""

    def __init__(self, parent: QWidget, language: str) -> None:
        super().__init__(parent)
        self.language = language
        self.setWindowTitle("Guide d'aide SoundMaker" if language == "fr" else "SoundMaker Help Guide")
        self.setMinimumSize(980, 680)
        self.resize(1080, 720)
        palette = getattr(parent, "theme_palette", None)
        self.theme_palette = palette
        self.setStyleSheet(build_help_dialog_qss(palette) if palette else HELP_DIALOG_QSS)

        outer = SmoothFrame()
        outer.setObjectName("helpShell")
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(22, 20, 22, 18)
        outer_layout.setSpacing(14)

        heading = QLabel("Guide d'aide SoundMaker" if language == "fr" else "SoundMaker Help Guide")
        heading.setObjectName("helpHeading")
        subheading = QLabel(
            "Comprendre les modes, les dossiers, le timer et les options sans devoir deviner."
            if language == "fr"
            else "Understand modes, folders, timing, and options without guessing."
        )
        subheading.setObjectName("helpSubheading")
        outer_layout.addWidget(heading)
        outer_layout.addWidget(subheading)

        body = QHBoxLayout()
        body.setSpacing(16)
        steps_panel = SmoothFrame()
        steps_panel.setObjectName("helpStepsPanel")
        steps_panel.setFixedWidth(245)
        steps_layout = QVBoxLayout(steps_panel)
        steps_layout.setContentsMargins(7, 7, 7, 7)
        steps_layout.setSpacing(0)
        self.steps = QListWidget()
        self.steps.setObjectName("helpSteps")
        self.steps.setFrameShape(QFrame.NoFrame)
        self.steps.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        steps_layout.addWidget(self.steps)
        self.pages = QStackedWidget()
        self.pages.setObjectName("helpPages")
        self.step_data = self._guide_steps()
        for step in self.step_data:
            self.steps.addItem(step["nav"])
            self.pages.addWidget(self._page(step["title"], step["body"], step["example"]))
        self.steps.currentRowChanged.connect(self._set_step)
        body.addWidget(steps_panel)
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

    def _guide_steps(self) -> list[dict[str, str]]:
        if self.language == "fr":
            return [
                {
                    "nav": "1. Vue d'ensemble",
                    "title": "Vue d'ensemble",
                    "body": """
                        <p><b>SoundMaker déclenche une seule mécanique active à la fois.</b> Vous choisissez le mode à droite, puis les réglages utiles apparaissent à gauche.</p>
                        <p>Le haut de la fenêtre montre l'état actuel: le mode choisi, le prochain déclenchement, la pause, la langue et le thème. Le bouton <b>Tester ce mode maintenant</b> lance la mécanique sans attendre le timer.</p>
                        <ul>
                            <li><b>Panneau gauche:</b> réglages du mode, timer, volume, image, texte ou alerte.</li>
                            <li><b>Panneau droit:</b> choix du mode, aide et raccourci Ko-fi.</li>
                            <li><b>Menu:</b> pause, camouflage systeme, dossiers, mise à jour et fermeture.</li>
                        </ul>
                    """,
                    "example": "Exemple: choisissez <b>Pop-up meme</b> à droite, écrivez le texte à gauche, puis cliquez sur <b>Prévisualiser le meme</b> ou <b>Tester ce mode maintenant</b>.",
                },
                {
                    "nav": "2. Modes",
                    "title": "Choisir le bon mode",
                    "body": """
                        <p>Chaque mode correspond à un type de surprise. Changer de mode ne supprime pas vos réglages: l'app garde vos préférences et recharge les bons contrôles quand vous revenez dessus.</p>
                        <ul>
                            <li><b>Sons aléatoires:</b> choisit un son au hasard dans le dossier sélectionné.</li>
                            <li><b>Son unique:</b> rejoue toujours le fichier exact que vous avez choisi.</li>
                            <li><b>Pop-up meme:</b> affiche une image ou un GIF avec du texte en haut et/ou en bas.</li>
                            <li><b>Fausse erreur:</b> affiche une alerte système avec votre message.</li>
                            <li><b>Chaos:</b> mélange plusieurs mécaniques et accélère progressivement.</li>
                            <li><b>Son erreur systeme:</b> joue le son d'erreur natif quand il existe, sinon un bip portable.</li>
                            <li><b>Notification chat:</b> joue un son court style Discord ou Teams.</li>
                        </ul>
                    """,
                    "example": "Exemple: pour une farce discrète, utilisez <b>Notification chat</b>. Pour une surprise visuelle claire, utilisez <b>Pop-up meme</b>. Pour quelque chose d'imprévisible, utilisez <b>Chaos</b>.",
                },
                {
                    "nav": "3. Timer",
                    "title": "Rythme, timer et déclenchements",
                    "body": """
                        <p>Le timer décide quand le mode actif se déclenche automatiquement. Pour les modes normaux, vous réglez un <b>minimum</b> et un <b>maximum</b> en minutes.</p>
                        <ul>
                            <li>L'app choisit un délai aléatoire entre le minimum et le maximum.</li>
                            <li>Le minimum ne peut pas dépasser le maximum.</li>
                            <li><b>Recalculer le minuteur</b> redémarre l'attente avec les valeurs actuelles.</li>
                            <li><b>Pause</b> bloque les déclenchements automatiques sans fermer l'app.</li>
                            <li><b>Tester ce mode maintenant</b> lance l'effet immédiatement sans attendre.</li>
                        </ul>
                    """,
                    "example": "Exemple: minimum 2 min et maximum 6 min signifie que la prochaine farce arrivera quelque part entre 2 et 6 minutes, puis un nouveau délai sera choisi.",
                },
                {
                    "nav": "4. Bibliothèque",
                    "title": "Images, sons et catégories",
                    "body": """
                        <p>SoundMaker lit vos médias depuis les dossiers <b>Images</b> et <b>Sounds</b>. Les sous-dossiers deviennent des catégories dans les listes de l'app.</p>
                        <ul>
                            <li><b>Importer une image</b> copie une image ou un GIF dans la bibliothèque.</li>
                            <li><b>Importer un son</b> copie un fichier MP3, WAV ou OGG dans la bibliothèque.</li>
                            <li><b>Rafraîchir</b> relit les dossiers si vous avez ajouté des fichiers manuellement.</li>
                            <li>Les modes aléatoires utilisent seulement la catégorie sélectionnée.</li>
                            <li>Le menu peut ouvrir directement les dossiers Images, Sounds et le fichier de textes de memes.</li>
                        </ul>
                    """,
                    "example": "Exemple: créez <b>Sounds/Jeux</b>, ajoutez plusieurs sons dedans, puis choisissez la catégorie <b>Jeux</b> en mode <b>Sons aléatoires</b>.",
                },
                {
                    "nav": "5. Sons",
                    "title": "Sons aléatoires, son unique et volume",
                    "body": """
                        <p>Les modes sonores partagent le réglage de volume. Le volume change ce que SoundMaker joue, sans modifier vos fichiers d'origine.</p>
                        <ul>
                            <li><b>Sons aléatoires:</b> pioche un fichier différent dans le dossier choisi à chaque déclenchement.</li>
                            <li><b>Son unique:</b> garde toujours le même fichier, utile pour un effet précis.</li>
                            <li><b>Jouer ce son</b> permet de vérifier un son avant de lancer le timer.</li>
                            <li>Si aucun son n'est disponible, le mode reste silencieux au lieu d'inventer un fichier.</li>
                        </ul>
                    """,
                    "example": "Exemple: pour une ambiance imprévisible, mettez 10 sons dans une catégorie. Pour un gag signature, utilisez <b>Son unique</b> avec un seul fichier.",
                },
                {
                    "nav": "6. Meme",
                    "title": "Pop-up meme: image, texte et son",
                    "body": """
                        <p>Le mode meme affiche une image ou un GIF au centre de l'écran, avec du texte style meme. Vous pouvez préparer l'image, le texte, la couleur, la durée et un son optionnel.</p>
                        <ul>
                            <li><b>Image unique:</b> affiche toujours la même image.</li>
                            <li><b>Image aléatoire du dossier:</b> choisit une image dans la catégorie sélectionnée.</li>
                            <li><b>Texte en haut / en bas:</b> vous pouvez remplir l'un, l'autre, ou les deux.</li>
                            <li><b>Couleur du texte:</b> change la couleur du texte affiché sur le meme.</li>
                            <li><b>Durée du meme:</b> définit combien de temps le pop-up reste visible.</li>
                            <li><b>Jouer un son avec ce meme:</b> peut rester désactivé, utiliser un son choisi, ou piocher un son au hasard.</li>
                            <li>Les textes sauvegardés peuvent être réutilisés, modifiés ou supprimés.</li>
                        </ul>
                    """,
                    "example": "Exemple: mettez un GIF en image unique, écrivez une punchline en bas, activez un son court, puis utilisez <b>Prévisualiser le meme</b> pour vérifier le résultat.",
                },
                {
                    "nav": "7. Alertes",
                    "title": "Fausse erreur, son systeme et notification chat",
                    "body": """
                        <p>Ces modes sont faits pour des surprises plus courtes et plus proches du système.</p>
                        <ul>
                            <li><b>Fausse erreur:</b> affiche une fenêtre d'erreur avec le message que vous écrivez.</li>
                            <li><b>Son erreur systeme:</b> déclenche le son d'erreur natif quand il existe, sinon un bip portable.</li>
                            <li><b>Notification chat:</b> joue un son de notification Discord ou Teams.</li>
                            <li>Ces modes utilisent aussi le timer général, sauf quand ils sont lancés par Chaos.</li>
                        </ul>
                    """,
                    "example": "Exemple: écrivez un message crédible dans <b>Fausse erreur</b>, testez-le, puis augmentez le délai pour que l'alerte arrive rarement.",
                },
                {
                    "nav": "8. Chaos",
                    "title": "Chaos: mélange et accélération",
                    "body": """
                        <p>Chaos ne suit pas le délai minimum/maximum classique. Il part d'un délai de départ, puis réduit progressivement le temps entre les farces.</p>
                        <ul>
                            <li><b>Départ du chaos:</b> délai du premier déclenchement.</li>
                            <li><b>Plancher:</b> délai minimum que Chaos ne dépassera pas, même après accélération.</li>
                            <li><b>Chaos peut utiliser:</b> liste des mécaniques autorisées.</li>
                            <li>Si un type de farce n'a pas les fichiers nécessaires, Chaos l'ignore.</li>
                            <li>Si aucune option utilisable n'est disponible, Chaos retombe sur la fausse erreur.</li>
                        </ul>
                    """,
                    "example": "Exemple: autorisez <b>Notification chat</b>, <b>Son erreur systeme</b> et <b>Pop-up meme</b>. Chaos choisira parmi ces effets et deviendra plus rapide avec le temps.",
                },
                {
                    "nav": "9. Contrôle",
                    "title": "Pause, test, langue et sécurité d'utilisation",
                    "body": """
                        <p>SoundMaker est pensé pour rester contrôlable pendant qu'il tourne.</p>
                        <ul>
                            <li><b>Pause / Reprendre:</b> stoppe ou relance les déclenchements automatiques.</li>
                            <li><b>Tester ce mode maintenant:</b> vérifie le mode actif sans attendre le timer.</li>
                            <li><b>Langue:</b> bascule entre français et anglais, puis garde ce choix au prochain lancement.</li>
                            <li><b>Camouflage systeme:</b> change le nom et l'icône de la fenêtre pour un style plus discret.</li>
                            <li><b>Quitter:</b> ferme l'application au lieu de la laisser tourner en arrière-plan.</li>
                        </ul>
                    """,
                    "example": "Exemple: mettez l'app en pause pendant que vous ajustez les médias, testez le résultat, puis cliquez sur <b>Reprendre</b> quand tout est prêt.",
                },
                {
                    "nav": "10. Personnalisation",
                    "title": "Thèmes, animations, mises à jour et dépannage",
                    "body": """
                        <p>Les réglages visuels changent l'apparence de l'app, pas les mécaniques de déclenchement.</p>
                        <ul>
                            <li><b>Thème:</b> change le fond et les couleurs de l'interface.</li>
                            <li><b>Ajouter un thème personnalisé:</b> ajoute une image de fond personnelle.</li>
                            <li><b>Animations du jardin:</b> active ou désactive les lucioles et pétales.</li>
                            <li><b>Vérifier les mises à jour:</b> cherche une nouvelle version disponible.</li>
                            <li>Si un média n'apparaît pas, utilisez <b>Rafraîchir</b> ou vérifiez qu'il est dans le bon dossier.</li>
                            <li>Si un mode ne déclenche rien, vérifiez qu'il possède bien une image, un son ou un message selon le mode.</li>
                        </ul>
                    """,
                    "example": "Exemple: si <b>Pop-up meme</b> ne montre rien, choisissez une image unique ou sélectionnez une catégorie contenant au moins une image compatible.",
                },
            ]
        return [
            {
                "nav": "1. Overview",
                "title": "Overview",
                "body": """
                    <p><b>SoundMaker runs one active prank mechanic at a time.</b> Choose the mode on the right, then the useful controls appear on the left.</p>
                    <p>The top of the window shows the current mode, next trigger, pause state, language, and theme. <b>Test this mode now</b> runs the mechanic immediately.</p>
                    <ul>
                        <li><b>Left panel:</b> mode settings, timer, volume, image, caption, or alert text.</li>
                        <li><b>Right panel:</b> mode selection, help, and Ko-fi shortcut.</li>
                        <li><b>Menu:</b> pause, system camouflage, folders, updates, and quit.</li>
                    </ul>
                """,
                "example": "Example: choose <b>Meme pop-up</b> on the right, write the caption on the left, then use <b>Preview meme</b> or <b>Test this mode now</b>.",
            },
            {
                "nav": "2. Modes",
                "title": "Choose the right mode",
                "body": """
                    <p>Each mode is a different kind of surprise. Switching mode does not wipe your setup: the app remembers preferences and reloads the matching controls when you return.</p>
                    <ul>
                        <li><b>Random sounds:</b> picks one sound from the selected folder.</li>
                        <li><b>Single sound:</b> always plays the exact file you chose.</li>
                        <li><b>Meme pop-up:</b> shows an image or GIF with top and/or bottom caption text.</li>
                        <li><b>Fake error:</b> shows a system-style alert with your message.</li>
                        <li><b>Chaos:</b> mixes several mechanics and speeds up over time.</li>
                        <li><b>System error sound:</b> plays the native error sound when available, otherwise a portable beep.</li>
                        <li><b>Chat notification:</b> plays a short Discord- or Teams-style sound.</li>
                    </ul>
                """,
                "example": "Example: use <b>Chat notification</b> for something subtle, <b>Meme pop-up</b> for a visual gag, or <b>Chaos</b> when you want unpredictability.",
            },
            {
                "nav": "3. Timing",
                "title": "Timing, timer, and triggers",
                "body": """
                    <p>The timer decides when the active mode triggers automatically. Normal modes use a <b>minimum</b> and <b>maximum</b> delay in minutes.</p>
                    <ul>
                        <li>The app chooses a random delay between minimum and maximum.</li>
                        <li>The minimum can never go above the maximum.</li>
                        <li><b>Recalculate timer</b> restarts the wait using the current values.</li>
                        <li><b>Pause</b> stops automatic triggers without closing the app.</li>
                        <li><b>Test this mode now</b> runs the effect immediately.</li>
                    </ul>
                """,
                "example": "Example: minimum 2 min and maximum 6 min means the next prank happens somewhere between 2 and 6 minutes, then a new delay is chosen.",
            },
            {
                "nav": "4. Library",
                "title": "Images, sounds, and categories",
                "body": """
                    <p>SoundMaker reads media from the <b>Images</b> and <b>Sounds</b> folders. Subfolders become categories inside the app.</p>
                    <ul>
                        <li><b>Import image</b> copies an image or GIF into the library.</li>
                        <li><b>Import sound</b> copies an MP3, WAV, or OGG file into the library.</li>
                        <li><b>Refresh</b> rescans folders after manual changes.</li>
                        <li>Random modes only use the selected category.</li>
                        <li>The menu can open Images, Sounds, and the meme text file directly.</li>
                    </ul>
                """,
                "example": "Example: create <b>Sounds/Games</b>, add several sounds there, then choose <b>Games</b> in <b>Random sounds</b> mode.",
            },
            {
                "nav": "5. Sounds",
                "title": "Random sounds, single sound, and volume",
                "body": """
                    <p>Sound modes share the volume control. Volume changes playback from SoundMaker, not your original files.</p>
                    <ul>
                        <li><b>Random sounds:</b> picks a file from the chosen folder every time.</li>
                        <li><b>Single sound:</b> keeps one exact file, useful for a precise effect.</li>
                        <li><b>Play this sound</b> lets you verify a sound before starting the timer.</li>
                        <li>If no sound is available, the mode stays silent instead of inventing a file.</li>
                    </ul>
                """,
                "example": "Example: put 10 sounds in one category for variety, or use <b>Single sound</b> when you want one signature gag.",
            },
            {
                "nav": "6. Meme",
                "title": "Meme pop-up: image, caption, and sound",
                "body": """
                    <p>Meme mode shows an image or GIF in the center of the screen with meme-style caption text. You can prepare the image, text, color, duration, and optional sound.</p>
                    <ul>
                        <li><b>Single image:</b> always shows the same image.</li>
                        <li><b>Random image from this folder:</b> picks from the selected category.</li>
                        <li><b>Top / bottom text:</b> fill either one or both.</li>
                        <li><b>Caption color:</b> changes the displayed text color.</li>
                        <li><b>Meme duration:</b> controls how long the pop-up stays visible.</li>
                        <li><b>Play a sound with this meme:</b> can stay off, use a selected sound, or pick one at random.</li>
                        <li>Saved captions can be reused, edited, or deleted.</li>
                    </ul>
                """,
                "example": "Example: choose one GIF, write the punchline at the bottom, enable a short sound, then use <b>Preview meme</b> to verify it.",
            },
            {
                "nav": "7. Alerts",
                "title": "Fake error, system beep, and chat notification",
                "body": """
                    <p>These modes are built for shorter, system-adjacent surprises.</p>
                    <ul>
                        <li><b>Fake error:</b> shows an error window with the message you write.</li>
                        <li><b>System error sound:</b> plays the native error sound when available, otherwise a portable beep.</li>
                        <li><b>Chat notification:</b> plays a Discord or Teams notification sound.</li>
                        <li>These modes use the normal timer unless Chaos launches them.</li>
                    </ul>
                """,
                "example": "Example: write a believable <b>Fake error</b> message, test it, then use a longer delay so the alert stays rare.",
            },
            {
                "nav": "8. Chaos",
                "title": "Chaos: mixing and acceleration",
                "body": """
                    <p>Chaos does not use the normal minimum/maximum delay. It starts from an initial delay, then gradually reduces the time between pranks.</p>
                    <ul>
                        <li><b>Chaos start:</b> delay before the first trigger.</li>
                        <li><b>Minimum floor:</b> shortest delay Chaos is allowed to reach.</li>
                        <li><b>Chaos can use:</b> the allowed mechanics list.</li>
                        <li>If a prank type has no required media, Chaos skips it.</li>
                        <li>If nothing usable is available, Chaos falls back to the fake error.</li>
                    </ul>
                """,
                "example": "Example: allow <b>Chat notification</b>, <b>System error sound</b>, and <b>Meme pop-up</b>. Chaos will choose between them and get faster over time.",
            },
            {
                "nav": "9. Control",
                "title": "Pause, test, language, and control",
                "body": """
                    <p>SoundMaker is designed to remain controllable while it runs.</p>
                    <ul>
                        <li><b>Pause / resume:</b> stops or restarts automatic triggers.</li>
                        <li><b>Test this mode now:</b> checks the active mode without waiting.</li>
                        <li><b>Language:</b> switches between English and French and remembers the choice.</li>
                        <li><b>System camouflage:</b> changes the window title and icon to look more discreet.</li>
                        <li><b>Quit:</b> closes the app instead of leaving it running.</li>
                    </ul>
                """,
                "example": "Example: pause the app while adjusting media, test the result, then click <b>Resume</b> when everything is ready.",
            },
            {
                "nav": "10. Customize",
                "title": "Themes, animations, updates, and troubleshooting",
                "body": """
                    <p>Visual settings change the app's appearance, not the trigger mechanics.</p>
                    <ul>
                        <li><b>Theme:</b> changes the background and interface colors.</li>
                        <li><b>Add custom theme:</b> adds a personal background image.</li>
                        <li><b>Garden animations:</b> toggles fireflies and falling petals.</li>
                        <li><b>Check for updates:</b> looks for a newer version.</li>
                        <li>If media does not appear, use <b>Refresh</b> or check that it is in the right folder.</li>
                        <li>If a mode does nothing, check that it has the required image, sound, or message.</li>
                    </ul>
                """,
                "example": "Example: if <b>Meme pop-up</b> shows nothing, choose a single image or select a category containing at least one compatible image.",
            },
        ]

    def _page(self, title: str, body: str, example: str) -> QWidget:
        scroll = QScrollArea()
        scroll.setObjectName("helpScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        page = SmoothFrame()
        page.setObjectName("helpPage")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(28, 26, 28, 26)
        layout.setSpacing(16)
        title_label = QLabel(title)
        title_label.setObjectName("helpPageTitle")
        text_label = QLabel(body)
        text_label.setObjectName("helpPageText")
        text_label.setTextFormat(Qt.RichText)
        text_label.setWordWrap(True)

        example_frame = SmoothFrame()
        example_frame.setObjectName("helpExample")
        example_layout = QVBoxLayout(example_frame)
        example_layout.setContentsMargins(16, 13, 16, 13)
        example_layout.setSpacing(6)
        example_title = QLabel("Exemple" if self.language == "fr" else "Example")
        example_title.setObjectName("helpExampleTitle")
        example_text = QLabel(example)
        example_text.setObjectName("helpExampleText")
        example_text.setTextFormat(Qt.RichText)
        example_text.setWordWrap(True)
        example_layout.addWidget(example_title)
        example_layout.addWidget(example_text)

        layout.addWidget(title_label)
        layout.addWidget(text_label)
        layout.addWidget(example_frame)
        layout.addStretch(1)
        scroll.setWidget(page)
        return scroll

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
