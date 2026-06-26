from __future__ import annotations

import ctypes
import html
import json
import os
import random
import shutil
import sys
import webbrowser
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QObject,
    QParallelAnimationGroup,
    QPointF,
    QPropertyAnimation,
    QRectF,
    QRunnable,
    QSize,
    Qt,
    QThreadPool,
    QTimer,
    QEvent,
    Signal,
)
from PySide6.QtGui import (
    QAction,
    QColor,
    QCloseEvent,
    QIcon,
    QImage,
    QMovie,
    QPainter,
    QPen,
    QPixmap,
)
from PySide6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QGraphicsDropShadowEffect,
    QGraphicsOpacityEffect,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QStyle,
    QSystemTrayIcon,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide"

from app_config import (
    APP_TITLE,
    APP_VERSION,
    CHAT_NOTIFICATION_DIR,
    CHAT_NOTIFICATION_FILES,
    DEFAULT_LANGUAGE,
    DEFAULT_MODE,
    KO_FI_URL,
    MODE_BY_KEY,
    MODE_CHAOS,
    MODE_CHAT_NOTIFICATION,
    MODE_FAKE_ERROR,
    MODE_MEME_POPUP,
    MODE_RANDOM_SOUND,
    MODE_SINGLE_SOUND,
    MODE_WINDOWS_ERROR,
    MODES,
    STEALTH_TITLE,
    TRANSLATIONS,
)
from asset_library import AssetLibrary
from audio_manager import AudioManager
from image_loader import load_pixmap, load_qimage
from update_manager import UpdateResult
from qt_backdrop import PrankBackdrop
from qt_components import (
    TabSpec,
    add_button_row,
    add_tab,
    label as component_label,
)
from qt_dialogs import HelpDialog, MemeDialog
from qt_file_actions import active_sound_folder, choose_meme_image, choose_sound_in_library, import_images, import_sound_files
from qt_icons import coffee_sakura_icon, prank_app_icon
import qt_mode_settings
from qt_preferences import load_preferences, save_preferences
from qt_theme import BUILTIN_THEME_NAMES, HOME_THEME_CAPTIONS, THEME_CREDITS, build_theme_qss
from qt_update_service import UpdateService
from qt_widgets import PaintedButton, SmoothFrame, SmoothGroupBox, SmoothRadioButton, SmoothTabBar


class ThemeLoadSignals(QObject):
    loaded = Signal(str, QImage)


class ThemeLoadTask(QRunnable):
    def __init__(self, theme_name: str, theme_path: Path) -> None:
        super().__init__()
        self.theme_name = theme_name
        self.theme_path = theme_path
        self.signals = ThemeLoadSignals()

    def run(self) -> None:
        self.signals.loaded.emit(self.theme_name, load_qimage(self.theme_path))


class SoundMakerQtApp(QMainWindow):
    """Qt version of the prank console. Logic stays in the shared helper modules."""

    def __init__(self) -> None:
        super().__init__()
        self.base_dir = Path(__file__).resolve().parent
        self.library = AssetLibrary(self.base_dir)
        self.audio = AudioManager()

        self.language = DEFAULT_LANGUAGE
        self.active_mode = DEFAULT_MODE
        self.selected_theme = ""
        self.selected_chat_notification = "discord"
        self.camouflage_enabled = False
        self.current_image_index = 0
        self.current_pixmap: QPixmap | None = None
        self.preview_movie: QMovie | None = None
        self.preview_movie_source_size = QSize()
        self.meme_duration = 1.5
        self.meme_text_color = "#FFFFFF"
        self.meme_sound_enabled = False
        self.meme_sound_mode = "single"
        self.selected_meme_sound = ""
        self.selected_meme_sound_path = ""
        self.meme_image_mode = "single"
        self.selected_meme_image = ""
        self.ambient_effects_enabled = True
        self.min_minutes = 1
        self.max_minutes = 8
        self.chaos_start_minutes = 4
        self.chaos_floor_seconds = 8
        self.chaos_factor = 1.0
        self.chaos_enabled_modes = {
            MODE_RANDOM_SOUND,
            MODE_SINGLE_SOUND,
            MODE_MEME_POPUP,
            MODE_FAKE_ERROR,
            MODE_WINDOWS_ERROR,
            MODE_CHAT_NOTIFICATION,
        }
        self.volume = 0.7
        self.is_running = True
        self.next_event_time = datetime.now()
        self._mode_switch_quiet_until = datetime.min
        self.paused_remaining_seconds: int | None = None

        self.selected_meme_template = {"top": "", "bottom": ""}
        self.meme_top_text = ""
        self.meme_bottom_text = ""
        self.alert_text = self._t("default_alert")
        self.selected_single_sound = ""
        self.selected_single_sound_path = ""
        self.preferences_path = self.library.data_dir / "preferences.json"
        self._load_preferences()
        self.audio.set_volume(self.volume)

        self.mode_buttons: dict[str, QRadioButton] = {}
        self.mode_summary_labels: dict[str, QLabel] = {}
        self.mode_cards: dict[str, QFrame] = {}
        self.tray_icon: QSystemTrayIcon | None = None
        self.meme_dialogs: list[QDialog] = []
        self._update_check_is_manual = False
        self.update_service = UpdateService(self)
        self.update_service.completed.connect(self._handle_update_result)
        self.current_animation: QPropertyAnimation | None = None
        self.dock_animation: QParallelAnimationGroup | None = None
        self.depth_effects: list[QGraphicsDropShadowEffect] = []
        self.left_dock_collapsed = False
        self.right_dock_collapsed = False
        self.left_expanded_width = 740
        self.right_expanded_width = 500
        self.narrow_window_breakpoint = 1320
        self._last_settings_compact = False
        self._responsive_dock_adjusting = False
        self._last_preview_target = QSize()
        self.theme_loading = False
        self.theme_spinner_angle = 0
        self.theme_spinner_timer = QTimer(self)
        self.theme_spinner_timer.timeout.connect(self._advance_theme_spinner)
        self.theme_load_pool = QThreadPool(self)
        self.pending_theme_name = ""
        self.theme_load_tasks: list[ThemeLoadTask] = []

        self._configure_window()
        self._build_ui()
        self._apply_panel_depth()
        self._build_tray_icon()
        self._apply_window_identity()
        self._refresh_library_controls()
        self._select_first_sound_if_needed()
        self._select_first_meme_sound_if_needed()
        self._render_mode_settings(animated=False)
        self._update_image_preview()
        self.schedule_next_event(reset_chaos=True)

        self.loop_timer = QTimer(self)
        self.loop_timer.timeout.connect(self._director_loop)
        self.loop_timer.start(1000)
        QTimer.singleShot(3500, lambda: self.check_for_updates(manual=False))

    def _load_preferences(self) -> None:
        load_preferences(self)

    def _save_preferences(self) -> None:
        save_preferences(self)

    def _t(self, key: str, **kwargs: object) -> str:
        text = TRANSLATIONS[self.language][key]
        return text.format(**kwargs) if kwargs else text

    def _configure_window(self) -> None:
        self.setWindowTitle(APP_TITLE)
        self.resize(1380, 740)
        self.setMinimumSize(860, 560)

    def _build_ui(self) -> None:
        self.backdrop = PrankBackdrop(self.base_dir / "assets" / "themes", self.selected_theme)
        self.backdrop.set_ambient_enabled(self.ambient_effects_enabled)
        self.selected_theme = self.backdrop.current_theme
        self.theme_palette = self.backdrop.palette
        self.setCentralWidget(self.backdrop)
        root_layout = QVBoxLayout(self.backdrop)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._build_header(root_layout)

        body = QWidget()
        body.setObjectName("body")
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(20, 18, 20, 20)
        body_layout.setSpacing(18)
        root_layout.addWidget(body, 1)

        self.left_dock_toggle = self._dock_toggle_button("left")
        body_layout.addWidget(self.left_dock_toggle)
        self._build_left_panel(body_layout)
        body_layout.addStretch(1)
        self._build_right_panel(body_layout)
        self.right_dock_toggle = self._dock_toggle_button("right")
        body_layout.addWidget(self.right_dock_toggle)
        self._sync_dock_toggles()
        self._apply_responsive_docks()

        credit_bar = QFrame()
        credit_bar.setObjectName("photoCreditBar")
        credit_bar.setFixedHeight(28)
        credit_layout = QHBoxLayout(credit_bar)
        credit_layout.setContentsMargins(20, 2, 20, 4)
        self.photo_credit_label = QLabel()
        self.photo_credit_label.setObjectName("photoCredit")
        self.photo_credit_label.setTextFormat(Qt.RichText)
        self.photo_credit_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.photo_credit_label.setOpenExternalLinks(True)
        self.photo_credit_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        credit_layout.addWidget(self.photo_credit_label, 1)
        root_layout.addWidget(credit_bar)
        self._apply_theme_palette()

    def _apply_theme_palette(self) -> None:
        self.theme_palette = self.backdrop.palette
        self.setStyleSheet(build_theme_qss(self.theme_palette))
        self._update_theme_credit()
        if hasattr(self, "brand_mark"):
            self.brand_mark.setPixmap(self._prank_app_icon().pixmap(46, 46))
        if hasattr(self, "kofi_button"):
            self.kofi_button.setIcon(self._coffee_sakura_icon())
        if hasattr(self, "mode_cards"):
            self._sync_mode_visuals()

    def _update_theme_credit(self) -> None:
        """Show the current background's source without competing with the scene."""
        if not hasattr(self, "photo_credit_label"):
            return

        theme_name = self.backdrop.current_theme
        credit = THEME_CREDITS.get(theme_name)
        if credit:
            artist, url = credit
            prefix = "Photo by" if self.language == "en" else "Photo par"
            self.photo_credit_label.setText(
                f'{prefix} <a href="{html.escape(url, quote=True)}">'
                f"{html.escape(artist)}</a> · Pexels"
            )
            self.photo_credit_label.show()
            return

        home_caption = HOME_THEME_CAPTIONS.get(theme_name)
        if home_caption:
            self.photo_credit_label.setText(home_caption[self.language])
            self.photo_credit_label.show()
            return

        self.photo_credit_label.clear()
        self.photo_credit_label.hide()

    def _apply_panel_depth(self) -> None:
        for widget in (self.left_panel, self.right_panel):
            self._apply_panel_shadow(widget)

    def _apply_panel_shadow(self, widget: QWidget) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        shadow.setBlurRadius(36)
        shadow.setOffset(0, 16)
        shadow.setColor(QColor(0, 0, 0, 92))
        widget.setGraphicsEffect(shadow)
        self.depth_effects.append(shadow)

    def _dock_toggle_button(self, side: str) -> QPushButton:
        button = PaintedButton()
        button.setObjectName("dockToggle")
        button.setFixedWidth(64)
        button.setMinimumHeight(148)
        button.setMaximumHeight(188)
        button.setIcon(self._dock_icon(side))
        button.setIconSize(QSize(20, 20))
        button.setToolTip("Fold or reveal panel" if self.language == "en" else "Replier ou ouvrir le panneau")
        button.clicked.connect(lambda _checked=False, dock_side=side: self.toggle_dock(dock_side))
        return button

    def _dock_icon(self, side: str) -> QIcon:
        palette = self.theme_palette
        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(palette.text, 1.5))
        painter.setBrush(Qt.NoBrush)
        if side == "left":
            for y, x in ((6, 8), (12, 14), (18, 10)):
                painter.drawLine(3, y, 21, y)
                painter.setBrush(palette.accent)
                painter.drawEllipse(QPointF(x, y), 2.2, 2.2)
                painter.setBrush(Qt.NoBrush)
        else:
            for y in (4, 10, 16):
                painter.drawRoundedRect(QRectF(4, y, 16, 4), 1.4, 1.4)
        painter.end()
        return QIcon(pixmap)

    def _sync_dock_toggles(self) -> None:
        if hasattr(self, "left_dock_toggle"):
            self.left_dock_toggle.setText("<" if not self.left_dock_collapsed else ">")
            self.left_dock_toggle.setIcon(self._dock_icon("left"))
            self.left_dock_toggle.setToolTip(
                "Hide app panel" if self.language == "en" and not self.left_dock_collapsed
                else "Show app panel" if self.language == "en"
                else "Cacher le panneau app" if not self.left_dock_collapsed
                else "Afficher le panneau app"
            )
        if hasattr(self, "right_dock_toggle"):
            self.right_dock_toggle.setText(">" if not self.right_dock_collapsed else "<")
            self.right_dock_toggle.setIcon(self._dock_icon("right"))
            self.right_dock_toggle.setToolTip(
                "Hide options panel" if self.language == "en" and not self.right_dock_collapsed
                else "Show options panel" if self.language == "en"
                else "Cacher le panneau options" if not self.right_dock_collapsed
                else "Afficher le panneau options"
            )

    def _is_narrow_window(self) -> bool:
        return self.width() < self.narrow_window_breakpoint

    def _set_dock_collapsed_immediate(self, side: str, collapsed: bool) -> None:
        panel = self.left_panel if side == "left" else self.right_panel
        collapsed_attr = "left_dock_collapsed" if side == "left" else "right_dock_collapsed"
        width_attr = "left_expanded_width" if side == "left" else "right_expanded_width"
        setattr(self, collapsed_attr, collapsed)
        panel.setMinimumWidth(0)
        if collapsed:
            panel.setMaximumWidth(0)
            panel.setVisible(False)
        else:
            panel.setVisible(True)
            panel.setMaximumWidth(getattr(self, width_attr))
        self._sync_dock_toggles()

    def _apply_responsive_docks(self) -> None:
        if self._responsive_dock_adjusting or not hasattr(self, "right_panel"):
            return
        if not self._is_narrow_window():
            return
        if self.left_dock_collapsed or self.right_dock_collapsed:
            return
        self._responsive_dock_adjusting = True
        self._set_dock_collapsed_immediate("right", True)
        self._responsive_dock_adjusting = False

    def toggle_dock(self, side: str) -> None:
        panel = self.left_panel if side == "left" else self.right_panel
        if self.dock_animation and self.dock_animation.state() == QAbstractAnimation.State.Running:
            self.dock_animation.stop()
        collapsed_attr = "left_dock_collapsed" if side == "left" else "right_dock_collapsed"
        width_attr = "left_expanded_width" if side == "left" else "right_expanded_width"
        collapse = not getattr(self, collapsed_attr)
        if self._is_narrow_window() and not collapse:
            self._set_dock_collapsed_immediate("right" if side == "left" else "left", True)
        setattr(self, collapsed_attr, collapse)
        self._sync_dock_toggles()

        if collapse:
            setattr(self, width_attr, max(panel.width(), getattr(self, width_attr)))
            start_width = panel.width()
            end_width = 0
            start_opacity = 1.0
            end_opacity = 0.0
        else:
            panel.setVisible(True)
            start_width = 0
            end_width = getattr(self, width_attr)
            start_opacity = 0.0
            end_opacity = 1.0

        panel.setMinimumWidth(0)
        panel.setMaximumWidth(max(1, start_width))
        opacity = QGraphicsOpacityEffect(panel)
        opacity.setOpacity(start_opacity)
        panel.setGraphicsEffect(opacity)

        width_animation = QPropertyAnimation(panel, b"maximumWidth", panel)
        width_animation.setDuration(210)
        width_animation.setStartValue(start_width)
        width_animation.setEndValue(end_width)
        width_animation.setEasingCurve(QEasingCurve.InOutCubic)

        opacity_animation = QPropertyAnimation(opacity, b"opacity", panel)
        opacity_animation.setDuration(180)
        opacity_animation.setStartValue(start_opacity)
        opacity_animation.setEndValue(end_opacity)
        opacity_animation.setEasingCurve(QEasingCurve.InOutCubic)

        group = QParallelAnimationGroup(panel)
        group.addAnimation(width_animation)
        group.addAnimation(opacity_animation)

        def finish() -> None:
            setattr(self, collapsed_attr, collapse)
            panel.setVisible(not collapse)
            panel.setGraphicsEffect(None)
            if collapse:
                panel.setMaximumWidth(0)
            else:
                panel.setMaximumWidth(getattr(self, width_attr))
                self._apply_panel_shadow(panel)
                self._update_image_preview()
            self._sync_dock_toggles()

        group.finished.connect(finish)
        self.dock_animation = group
        self.backdrop.set_ambient_running(False)
        group.finished.connect(lambda: self._set_visual_animations_running(not self.isMinimized() and self.isVisible()))
        group.start()

    def _build_header(self, root_layout: QVBoxLayout) -> None:
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 10, 20, 10)
        layout.setSpacing(14)

        self.menu_button = PaintedButton(self._t("menu"))
        self.menu_button.setObjectName("ghostButton")
        self.menu_button.clicked.connect(self._show_app_menu)
        layout.addWidget(self.menu_button)

        self.brand_mark = QLabel()
        self.brand_mark.setObjectName("brandMark")
        self.brand_mark.setAlignment(Qt.AlignCenter)
        self.brand_mark.setPixmap(self._prank_app_icon().pixmap(46, 46))
        layout.addWidget(self.brand_mark)

        title_box = QVBoxLayout()
        title_box.setSpacing(3)
        self.title_label = QLabel(APP_TITLE)
        self.title_label.setObjectName("appTitle")
        self.subtitle_label = QLabel(self._t("header_status"))
        self.subtitle_label.setObjectName("muted")
        self.author_label = QLabel(self._t("author"))
        self.author_label.setObjectName("tinyMuted")
        title_row = QHBoxLayout()
        title_row.setSpacing(10)
        title_row.addWidget(self.title_label)
        title_row.addStretch(1)
        title_box.addLayout(title_row)
        title_box.addWidget(self.subtitle_label)
        title_box.addWidget(self.author_label)
        layout.addLayout(title_box, 1)

        self.pause_button = PaintedButton(self._t("pause"))
        self.pause_button.setObjectName("warningButton")
        self.pause_button.clicked.connect(self.toggle_running)
        layout.addWidget(self.pause_button)

        self.theme_button = PaintedButton(self._t("theme"))
        self.theme_button.setObjectName("secondaryButton")
        self.theme_button.clicked.connect(self.cycle_theme)
        layout.addWidget(self.theme_button)

        self.language_button = PaintedButton(self._t("language"))
        self.language_button.setObjectName("secondaryButton")
        self.language_button.clicked.connect(self.toggle_language)
        layout.addWidget(self.language_button)

        root_layout.addWidget(header)

    def _build_left_panel(self, body_layout: QHBoxLayout) -> None:
        self.left_panel = SmoothFrame()
        self.left_panel.setObjectName("panel")
        self.left_panel.setMaximumWidth(self.left_expanded_width)
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(14)
        body_layout.addWidget(self.left_panel, 6)

        timer_card = SmoothFrame()
        timer_card.setObjectName("timerCard")
        timer_layout = QVBoxLayout(timer_card)
        timer_layout.setContentsMargins(16, 14, 16, 14)
        timer_layout.setSpacing(8)
        self.accent_bar = QFrame()
        self.accent_bar.setObjectName("accentBar")
        self.accent_bar.setFixedHeight(5)
        timer_layout.addWidget(self.accent_bar)
        self.timer_label = QLabel(self._t("next_event", minutes=0, seconds=0))
        self.timer_label.setObjectName("timerText")
        self.mode_status_label = QLabel(self._t("mode_prefix", mode=MODE_BY_KEY[self.active_mode].name(self.language)))
        self.mode_status_label.setObjectName("modeChip")
        timer_layout.addWidget(self.timer_label)
        timer_layout.addWidget(self.mode_status_label)
        left_layout.addWidget(timer_card)

        settings_shell = SmoothFrame()
        settings_shell.setObjectName("settingsShell")
        settings_shell_layout = QVBoxLayout(settings_shell)
        settings_shell_layout.setContentsMargins(10, 10, 10, 10)
        self.settings_widget = QWidget()
        self.settings_layout = QVBoxLayout(self.settings_widget)
        self.settings_layout.setContentsMargins(12, 10, 12, 10)
        self.settings_layout.setSpacing(7)
        settings_shell_layout.addWidget(self.settings_widget)
        left_layout.addWidget(settings_shell, 1)

    def _build_right_panel(self, body_layout: QHBoxLayout) -> None:
        self.right_panel = SmoothFrame()
        self.right_panel.setObjectName("panel")
        self.right_panel.setMaximumWidth(self.right_expanded_width)
        right_layout = QVBoxLayout(self.right_panel)
        right_layout.setContentsMargins(14, 14, 14, 14)
        right_layout.setSpacing(12)
        body_layout.addWidget(self.right_panel, 4)

        self.modes_group = self._section(self._t("available_modes"))
        modes_scroll = QScrollArea()
        modes_scroll.setObjectName("modesScroll")
        modes_scroll.setWidgetResizable(True)
        modes_scroll.setFrameShape(QFrame.NoFrame)
        modes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        modes_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        modes_widget = QWidget()
        modes_layout = QVBoxLayout(modes_widget)
        modes_layout.setContentsMargins(0, 0, 12, 0)
        modes_layout.setSpacing(10)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        for mode in MODES:
            modes_layout.addWidget(self._mode_card(mode.key))
        modes_layout.addStretch(1)
        modes_scroll.setWidget(modes_widget)
        self.modes_group.layout().addWidget(modes_scroll)
        right_layout.addWidget(self.modes_group, 1)

        self.help_group = self._section(self._t("help"))
        help_layout = self.help_group.layout()
        help_buttons = QHBoxLayout()
        self.quick_guide_button = PaintedButton(self._t("quick_guide"))
        self.quick_guide_button.setObjectName("helpButton")
        self.kofi_button = PaintedButton(self._t("kofi_label"))
        self.kofi_button.setObjectName("coffeeButton")
        self.kofi_button.setIcon(self._coffee_sakura_icon())
        self.kofi_button.setIconSize(QSize(26, 26))
        self.quick_guide_button.clicked.connect(self.show_help_window)
        self.kofi_button.clicked.connect(self.open_kofi)
        help_buttons.addWidget(self.quick_guide_button, 1)
        help_buttons.addWidget(self.kofi_button, 1)
        help_layout.addLayout(help_buttons)
        right_layout.addWidget(self.help_group)

    def _section(self, title: str) -> QGroupBox:
        group = SmoothGroupBox(title)
        group.setObjectName("section")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(14, 20, 14, 14)
        layout.setSpacing(12)
        return group

    def _prank_app_icon(self) -> QIcon:
        return prank_app_icon(self.theme_palette)

    def _coffee_sakura_icon(self) -> QIcon:
        return coffee_sakura_icon(self.theme_palette)

    def _mode_card(self, mode_key: str) -> QFrame:
        mode = MODE_BY_KEY[mode_key]
        card = SmoothFrame()
        card.setObjectName("modeCard")
        card_layout = QHBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        content = QVBoxLayout()
        content.setContentsMargins(13, 10, 13, 10)
        content.setSpacing(4)

        radio = SmoothRadioButton(mode.name(self.language))
        radio.setProperty("accent", self._mode_accent(mode.key))
        radio.setChecked(mode.key == self.active_mode)
        radio.toggled.connect(lambda checked, key=mode.key: self.on_mode_selected(key) if checked else None)
        self.mode_group.addButton(radio)
        self.mode_buttons[mode.key] = radio

        summary = QLabel(mode.summary(self.language))
        summary.setObjectName("muted")
        summary.setWordWrap(True)
        self.mode_summary_labels[mode.key] = summary

        content.addWidget(radio)
        content.addWidget(summary)
        card_layout.addLayout(content, 1)
        self.mode_cards[mode.key] = card
        return card

    def _mode_accent(self, mode_key: str) -> str:
        return self.theme_palette.hex(self.theme_palette.mode_accents.get(mode_key, self.theme_palette.accent))

    def _clear_settings(self) -> None:
        self.settings_title = None
        if self.preview_movie:
            self.preview_movie.stop()
            self.preview_movie.deleteLater()
            self.preview_movie = None
        self.preview_movie_source_size = QSize()
        self.current_pixmap = None
        self.image_label = None
        self.image_name_label = None
        self.image_category_combo = None
        self.sound_category_combo = None
        self.meme_sound_combo = None
        while self.settings_layout.count():
            item = self.settings_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
                continue
            layout = item.layout()
            if layout:
                self._delete_layout(layout)

    def _delete_layout(self, layout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            child_layout = item.layout()
            if child_layout:
                self._delete_layout(child_layout)

    def _render_mode_settings(self, animated: bool = True, preserve_tab: bool = False) -> None:
        previous_tab = self._active_settings_tab() if preserve_tab else ""
        self._clear_settings()
        self._last_settings_compact = self._settings_are_compact()
        mode = MODE_BY_KEY[self.active_mode]
        self.mode_status_label.setText(self._t("mode_prefix", mode=mode.name(self.language)))
        self._sync_mode_visuals()

        self.settings_title = QLabel(mode.name(self.language))
        self.settings_title.setObjectName("settingsTitle")
        self.settings_title.setStyleSheet(f"color: {self._mode_accent(mode.key)};")
        summary = QLabel(mode.summary(self.language))
        summary.setObjectName("muted")
        summary.setWordWrap(True)
        self.settings_layout.addWidget(self.settings_title)
        self.settings_layout.addWidget(summary)

        tab_surface = SmoothFrame()
        tab_surface.setObjectName("tabSurface")
        tab_surface_layout = QVBoxLayout(tab_surface)
        tab_surface_layout.setContentsMargins(8, 8, 8, 8)
        tab_surface_layout.setSpacing(0)
        tabs = QTabWidget()
        tabs.setObjectName("modeTabs")
        tabs.setTabBar(SmoothTabBar(tabs))
        tabs.setDocumentMode(True)
        self.mode_tabs = tabs
        self.sound_tab_index: int | None = None
        tab_surface_layout.addWidget(tabs)
        self.settings_layout.addWidget(tab_surface, 1)

        if self.active_mode == MODE_CHAOS:
            self._add_settings_tab(tabs, self._t("tab_timing"), self._t("tab_chaos_desc"), self._add_chaos_controls)
        else:
            self._add_settings_tab(tabs, self._t("tab_timing"), self._t("tab_timing_desc"), self._add_timer_controls)

        sound_modes = {
            MODE_RANDOM_SOUND,
            MODE_SINGLE_SOUND,
            MODE_CHAOS,
            MODE_CHAT_NOTIFICATION,
            MODE_MEME_POPUP,
        }
        if self.active_mode in sound_modes:
            self.sound_tab_index = tabs.count()
            self._add_settings_tab(tabs, self._t("tab_sound"), self._t("tab_sound_desc"), self._add_sound_settings)
        if self.active_mode in {MODE_MEME_POPUP, MODE_CHAOS}:
            self._add_settings_tab(tabs, self._t("tab_meme"), self._t("tab_meme_desc"), self._add_meme_controls)
            self._add_settings_tab(tabs, self._t("tab_image"), self._t("tab_image_desc"), self._add_image_settings)
        if self.active_mode in {MODE_FAKE_ERROR, MODE_CHAOS}:
            self._add_settings_tab(tabs, self._t("tab_alert"), self._t("tab_alert_desc"), self._add_alert_controls)

        if previous_tab:
            for index in range(tabs.count()):
                if tabs.tabText(index) == previous_tab:
                    tabs.setCurrentIndex(index)
                    break

        test_button = PaintedButton(self._t("test_now"))
        test_button.setObjectName("successButton")
        recalc_button = PaintedButton(self._t("recalculate"))
        recalc_button.setObjectName("timerButton")
        test_button.clicked.connect(self.run_current_mode)
        recalc_button.clicked.connect(lambda: self.schedule_next_event(reset_chaos=True))
        self._add_button_row([test_button, recalc_button])

        if self.active_mode in {MODE_MEME_POPUP, MODE_CHAOS}:
            QTimer.singleShot(0, self._update_image_preview)

    def _settings_are_compact(self) -> bool:
        panel_width = self.left_panel.width() if hasattr(self, "left_panel") else self.width()
        return panel_width < 720

    def _add_button_row(self, buttons: list[QPushButton]) -> None:
        add_button_row(self.settings_layout, buttons, self._settings_are_compact())

    def _active_settings_tab(self) -> str:
        tabs = getattr(self, "mode_tabs", None)
        if not tabs:
            return ""
        try:
            return tabs.tabText(tabs.currentIndex())
        except RuntimeError:
            return ""

    def _add_settings_tab(self, tabs: QTabWidget, label: str, description: str, builder: Callable[[], None]) -> None:
        """Give every tab its own clear scroll area without wheel-changing controls."""
        def build(page_layout: QVBoxLayout) -> None:
            settings_layout = self.settings_layout
            self.settings_layout = page_layout
            try:
                builder()
            finally:
                self.settings_layout = settings_layout

        add_tab(tabs, TabSpec(label, description, build))

    def _sync_mode_visuals(self) -> None:
        mode = MODE_BY_KEY[self.active_mode]
        accent = self._mode_accent(mode.key)
        self.accent_bar.setStyleSheet(
            f"background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {accent}, stop:0.55 {self.theme_palette.hex(self.theme_palette.accent_alt)}, stop:1 {self.theme_palette.hex(self.theme_palette.text)});"
            "border-radius: 3px;"
        )
        self.mode_status_label.setStyleSheet(
            f"color: {self.theme_palette.hex(self.theme_palette.text)}; background: {self.theme_palette.rgba(self.theme_palette.base, 184)}; border: 2px solid {accent};"
            "border-radius: 12px; padding: 5px 10px;"
        )
        self.brand_mark.setPixmap(self._prank_app_icon().pixmap(46, 46))
        if getattr(self, "settings_title", None):
            self.settings_title.setStyleSheet(f"color: {accent};")
        for key, card in self.mode_cards.items():
            card.setProperty("active", key == self.active_mode)
            card.style().unpolish(card)
            card.style().polish(card)
            card.update()

    def _apply_shadow(self, widget: QWidget, color: QColor, strength: float = 0.18) -> None:
        shadow = QGraphicsDropShadowEffect(widget)
        color.setAlphaF(strength)
        shadow.setColor(color)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 8)
        widget.setGraphicsEffect(shadow)

    def _add_timer_controls(self) -> None:
        qt_mode_settings.add_timer_controls(self)

    def _add_chaos_controls(self) -> None:
        qt_mode_settings.add_chaos_controls(self)

    def _add_sound_settings(self) -> None:
        qt_mode_settings.add_sound_settings(self)

    def _add_meme_sound_settings(self) -> None:
        qt_mode_settings.add_meme_sound_settings(self)

    def _add_sound_library_controls(self) -> None:
        qt_mode_settings.add_sound_library_controls(self)

    def _add_single_sound_controls(self) -> None:
        qt_mode_settings.add_single_sound_controls(self)

    def _add_meme_single_sound_controls(self) -> None:
        qt_mode_settings.add_meme_single_sound_controls(self)

    def _add_selected_sound_controls(
        self,
        choose_text: str,
        empty_text: str,
        sound_path: Path | None,
        choose_callback: Callable[[], None],
        import_callback: Callable[[], None],
    ) -> QLabel:
        return qt_mode_settings.add_selected_sound_controls(self, choose_text, empty_text, sound_path, choose_callback, import_callback)

    def _add_meme_random_sound_controls(self) -> None:
        qt_mode_settings.add_meme_random_sound_controls(self)

    def _add_random_sound_status(self) -> None:
        qt_mode_settings.add_random_sound_status(self)

    def _add_chat_notification_controls(self) -> None:
        qt_mode_settings.add_chat_notification_controls(self)

    def _add_meme_controls(self) -> None:
        qt_mode_settings.add_meme_controls(self)

    def _add_image_settings(self) -> None:
        qt_mode_settings.add_image_settings(self)

    def _add_alert_controls(self) -> None:
        qt_mode_settings.add_alert_controls(self)

    def _add_volume_controls(self) -> None:
        qt_mode_settings.add_volume_controls(self)

    def _label(self, text: str, object_name: str = "") -> QLabel:
        return component_label(text, object_name)

    def _fade_in(self, widget: QWidget) -> None:
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        animation = QPropertyAnimation(effect, b"opacity", widget)
        animation.setDuration(115)
        animation.setStartValue(0.0)
        animation.setEndValue(1.0)
        animation.setEasingCurve(QEasingCurve.InOutCubic)
        animation.finished.connect(effect.deleteLater)
        self.current_animation = animation
        animation.start()

    def on_mode_selected(self, mode_key: str) -> None:
        self._mode_switch_quiet_until = datetime.now() + timedelta(seconds=2)
        self.active_mode = mode_key
        self.chaos_factor = 1.0
        self._render_mode_settings()
        self.schedule_next_event(reset_chaos=True)
        self._save_preferences()

    def on_chat_notification_selected(self, choice: str) -> None:
        self.selected_chat_notification = choice
        self._save_preferences()

    def on_single_sound_selected(self, text: str) -> None:
        self.selected_single_sound = text
        self._save_preferences()

    def on_min_slider(self, value: int) -> None:
        self.min_minutes = value
        if self.min_minutes > self.max_minutes:
            self.max_minutes = self.min_minutes
            if hasattr(self, "max_time_slider"):
                self.max_time_slider.blockSignals(True)
                self.max_time_slider.setValue(self.max_minutes)
                self.max_time_slider.blockSignals(False)
        if hasattr(self, "min_label"):
            self.min_label.setText(self._t("minimum", value=self.min_minutes))
        if hasattr(self, "max_label"):
            self.max_label.setText(self._t("maximum", value=self.max_minutes))
        self._save_preferences()

    def on_max_slider(self, value: int) -> None:
        self.max_minutes = value
        if self.max_minutes < self.min_minutes:
            self.min_minutes = self.max_minutes
            if hasattr(self, "min_time_slider"):
                self.min_time_slider.blockSignals(True)
                self.min_time_slider.setValue(self.min_minutes)
                self.min_time_slider.blockSignals(False)
        if hasattr(self, "min_label"):
            self.min_label.setText(self._t("minimum", value=self.min_minutes))
        if hasattr(self, "max_label"):
            self.max_label.setText(self._t("maximum", value=self.max_minutes))
        self._save_preferences()

    def on_chaos_start_slider(self, value: int) -> None:
        self.chaos_start_minutes = value
        self.chaos_start_label.setText(self._t("chaos_start", value=value))
        self._save_preferences()

    def on_chaos_floor_slider(self, value: int) -> None:
        self.chaos_floor_seconds = value
        self.chaos_floor_label.setText(self._t("chaos_floor", value=value))
        self._save_preferences()

    def on_chaos_mode_toggled(self, mode_key: str, enabled: bool) -> None:
        if enabled:
            self.chaos_enabled_modes.add(mode_key)
        elif len(self.chaos_enabled_modes) > 1:
            self.chaos_enabled_modes.discard(mode_key)
        else:
            checkbox = getattr(self, "chaos_mode_checkboxes", {}).get(mode_key)
            if checkbox:
                checkbox.blockSignals(True)
                checkbox.setChecked(True)
                checkbox.blockSignals(False)
            return
        self._save_preferences()

    def on_meme_duration_slider(self, value: int) -> None:
        self.meme_duration = value / 10
        self.meme_duration_label.setText(self._t("meme_duration", value=self.meme_duration))
        self._save_preferences()

    def on_meme_text_color_selected(self, index: int) -> None:
        if hasattr(self, "meme_color_combo"):
            self.meme_text_color = str(self.meme_color_combo.itemData(index) or "#FFFFFF")
        self._save_preferences()

    def on_meme_sound_enabled_changed(self, enabled: bool) -> None:
        self.meme_sound_enabled = enabled
        self._save_preferences()

    def on_meme_sound_mode_changed(self, mode: str) -> None:
        self.meme_sound_mode = mode
        self._save_preferences()
        if self.active_mode == MODE_MEME_POPUP:
            self._render_mode_settings(animated=False, preserve_tab=True)

    def on_meme_sound_selected(self, filename: str) -> None:
        if filename in self.library.sounds:
            self.selected_meme_sound = filename
        self._save_preferences()

    def on_meme_image_mode_changed(self, mode: str) -> None:
        self.meme_image_mode = mode
        self._save_preferences()
        if self.active_mode in {MODE_MEME_POPUP, MODE_CHAOS}:
            self._render_mode_settings(animated=False, preserve_tab=True)

    def on_volume_slider(self, value: int) -> None:
        self.volume = value / 100
        self.audio.set_volume(self.volume)
        self.volume_label.setText(self._t("volume", value=value))
        self._save_preferences()

    def on_meme_template_selected(self, index: int) -> None:
        if not hasattr(self, "meme_combo"):
            return
        try:
            template = json.loads(str(self.meme_combo.itemData(index)))
        except (TypeError, ValueError, json.JSONDecodeError):
            template = None
        if not isinstance(template, dict):
            return
        self.selected_meme_template = {"top": str(template.get("top", "")), "bottom": str(template.get("bottom", ""))}
        self.meme_top_text = self.selected_meme_template["top"]
        self.meme_bottom_text = self.selected_meme_template["bottom"]
        for widget, value in ((getattr(self, "meme_top_input", None), self.meme_top_text), (getattr(self, "meme_bottom_input", None), self.meme_bottom_text)):
            if widget:
                widget.blockSignals(True)
                widget.setText(value)
                widget.blockSignals(False)
        self._save_preferences()

    def on_meme_top_text_changed(self, text: str) -> None:
        self.meme_top_text = text

    def on_meme_bottom_text_changed(self, text: str) -> None:
        self.meme_bottom_text = text

    def on_alert_text_changed(self, text: str) -> None:
        self.alert_text = text
        self._save_preferences()

    def toggle_running(self) -> None:
        if self.is_running:
            self.paused_remaining_seconds = max(0, int((self.next_event_time - datetime.now()).total_seconds()))
            self.is_running = False
        else:
            self.is_running = True
            if self.paused_remaining_seconds is not None:
                self.next_event_time = datetime.now() + timedelta(seconds=self.paused_remaining_seconds)
            self.paused_remaining_seconds = None
        self.pause_button.setText(self._t("pause") if self.is_running else self._t("resume"))
        self._update_timer_label()
        self._save_preferences()

    def toggle_language(self) -> None:
        self.language = "fr" if self.language == "en" else "en"
        self._apply_language()
        self._save_preferences()

    def cycle_theme(self) -> None:
        if self.theme_loading:
            return
        next_theme = self.backdrop.next_theme_name()
        next_theme_path = self.backdrop.theme_path(next_theme) if next_theme else None
        if not next_theme_path:
            return
        self.theme_loading = True
        self.pending_theme_name = next_theme
        self.theme_spinner_angle = 0
        self.theme_button.setEnabled(False)
        self.theme_button.setText("")
        self._advance_theme_spinner()
        self.theme_spinner_timer.start(45)
        task = ThemeLoadTask(next_theme, next_theme_path)
        task.signals.loaded.connect(self._finish_theme_cycle)
        self.theme_load_tasks.append(task)
        self.theme_load_pool.start(task)

    def _finish_theme_cycle(self, theme_name: str, image: QImage) -> None:
        try:
            if theme_name == self.pending_theme_name and not image.isNull():
                self.selected_theme = self.backdrop.apply_theme_image(theme_name, image)
                self._apply_theme_palette()
                self._apply_window_identity()
                self._save_preferences()
        finally:
            self.theme_load_tasks = [task for task in self.theme_load_tasks if task.theme_name != theme_name]
            self.theme_spinner_timer.stop()
            self.theme_loading = False
            self.pending_theme_name = ""
            self.theme_button.setIcon(QIcon())
            self.theme_button.setText(self._t("theme"))
            self.theme_button.setEnabled(True)

    def _advance_theme_spinner(self) -> None:
        if not self.theme_loading or not hasattr(self, "theme_button"):
            return
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(QPen(self.theme_palette.text, 2.4))
        painter.drawArc(QRectF(3, 3, 14, 14), self.theme_spinner_angle * 16, 235 * 16)
        painter.end()
        self.theme_button.setIcon(QIcon(pixmap))
        self.theme_spinner_angle = (self.theme_spinner_angle - 42) % 360

    def _apply_language(self) -> None:
        self.menu_button.setText(self._t("menu"))
        self.subtitle_label.setText(self._t("header_status"))
        self.author_label.setText(self._t("author"))
        self.pause_button.setText(self._t("pause") if self.is_running else self._t("resume"))
        self.theme_button.setText(self._t("theme"))
        self.language_button.setText(self._t("language"))
        self.modes_group.setTitle(self._t("available_modes"))
        self.help_group.setTitle(self._t("help"))
        self.quick_guide_button.setText(self._t("quick_guide"))
        self.kofi_button.setText(self._t("kofi_label"))
        self._sync_dock_toggles()
        self._refresh_tray_menu()
        for mode in MODES:
            self.mode_buttons[mode.key].setText(mode.name(self.language))
            self.mode_summary_labels[mode.key].setText(mode.summary(self.language))
        self._render_mode_settings(animated=False, preserve_tab=True)
        self._update_theme_credit()
        self._update_timer_label()

    def _show_app_menu(self) -> None:
        menu = QMenu(self)
        menu.addAction(self._t("menu_pause"), self.toggle_running)
        menu.addAction(self._t("recalculate"), lambda: self.schedule_next_event(reset_chaos=True))
        stealth_action = QAction(self._t("menu_stealth"), self)
        stealth_action.setCheckable(True)
        stealth_action.setChecked(self.camouflage_enabled)
        stealth_action.triggered.connect(self.toggle_camouflage)
        menu.addAction(stealth_action)
        menu.addAction(self._t("check_updates"), self.check_for_updates)
        menu.addSeparator()
        theme_menu = menu.addMenu(self._t("theme"))
        theme_menu.addAction(self._t("theme_add"), self.add_custom_theme)
        remove_theme_action = theme_menu.addAction(self._t("theme_remove"), self.remove_current_custom_theme)
        remove_theme_action.setEnabled(self.backdrop.current_theme not in BUILTIN_THEME_NAMES)
        ambient_action = menu.addAction(self._t("animations"))
        ambient_action.setCheckable(True)
        ambient_action.setChecked(self.ambient_effects_enabled)
        ambient_action.setToolTip(self._t("animations_hint"))
        ambient_action.toggled.connect(self.toggle_ambient_effects)
        menu.addSeparator()
        menu.addAction(self._t("refresh"), self.refresh_library)
        menu.addAction(self._t("import_image"), self.add_image_file)
        menu.addAction(self._t("import_sound"), self.add_sound_file)
        menu.addSeparator()
        menu.addAction(self._t("open_images"), lambda: self.open_system_path(self.library.images_dir))
        menu.addAction(self._t("open_sounds"), lambda: self.open_system_path(self.library.sounds_dir))
        menu.addSeparator()
        menu.addAction(self._t("help"), self.show_help_window)
        menu.addAction(self._t("language"), self.toggle_language)
        menu.addAction(self._t("kofi_label"), self.open_kofi)
        menu.addSeparator()
        menu.addAction(self._t("quit"), self.quit_application)
        self.backdrop.set_ambient_running(False)
        try:
            menu.exec(self.menu_button.mapToGlobal(self.menu_button.rect().bottomLeft()))
        finally:
            self.backdrop.set_ambient_running(True)

    def add_custom_theme(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self._t("theme_add"),
            str(self.base_dir),
            "Images (*.png *.jpg *.jpeg *.bmp *.webp *.avif)",
        )
        if not files:
            return
        self.backdrop.themes_dir.mkdir(parents=True, exist_ok=True)
        newest_theme = ""
        for file_name in files:
            source = Path(file_name)
            if not source.is_file():
                continue
            target = self.backdrop.themes_dir / source.name
            suffix = 2
            while target.exists():
                target = self.backdrop.themes_dir / f"{source.stem}-{suffix}{source.suffix.lower()}"
                suffix += 1
            shutil.copy2(source, target)
            newest_theme = target.name
        if not newest_theme:
            return
        self.backdrop.refresh_themes()
        self.selected_theme = self.backdrop.set_theme(newest_theme)
        self._apply_theme_palette()
        self._save_preferences()

    def remove_current_custom_theme(self) -> None:
        theme_name = self.backdrop.current_theme
        if not theme_name or theme_name in BUILTIN_THEME_NAMES:
            QMessageBox.information(self, APP_TITLE, self._t("theme_remove_protected"))
            return
        choice = QMessageBox.question(
            self,
            APP_TITLE,
            self._t("theme_remove_confirm", name=theme_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if choice != QMessageBox.StandardButton.Yes:
            return
        path = self.backdrop.themes_dir / theme_name
        try:
            path.unlink()
        except OSError as error:
            QMessageBox.warning(self, APP_TITLE, str(error))
            return
        self.backdrop.refresh_themes()
        self.selected_theme = self.backdrop.set_theme("")
        self._apply_theme_palette()
        self._save_preferences()

    def toggle_ambient_effects(self, enabled: bool) -> None:
        self.ambient_effects_enabled = enabled
        self.backdrop.set_ambient_enabled(enabled)
        self._save_preferences()

    def _set_visual_animations_running(self, running: bool) -> None:
        self.backdrop.set_ambient_running(running)
        if self.preview_movie:
            self.preview_movie.setPaused(not running)

    def changeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().changeEvent(event)
        if event.type() == QEvent.WindowStateChange:
            self._set_visual_animations_running(not self.isMinimized() and self.isVisible())
            if self.isMinimized() and self.tray_icon:
                QTimer.singleShot(0, self.hide)

    def hideEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().hideEvent(event)
        self._set_visual_animations_running(False)

    def showEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().showEvent(event)
        if not self.isMinimized():
            self._set_visual_animations_running(True)

    def _refresh_library_controls(self) -> None:
        for attribute, values, selected in (
            ("image_category_combo", self.library.image_categories, self.library.selected_image_category),
            ("sound_category_combo", self.library.sound_categories, self.library.selected_sound_category),
        ):
            combo = getattr(self, attribute, None)
            if not combo:
                continue
            try:
                self._replace_combo_items(combo, values, selected)
            except RuntimeError:
                # The tab was replaced while the library was refreshing.
                setattr(self, attribute, None)

    def _replace_combo_items(self, combo: QComboBox, values: list[str], selected: str) -> None:
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(values)
        combo.setCurrentText(selected)
        combo.blockSignals(False)

    def on_image_category_change(self, choice: str) -> None:
        if not choice:
            return
        self.library.set_image_category(choice)
        self.current_image_index = 0
        self._refresh_library_controls()
        self._update_image_preview()
        self._save_preferences()

    def on_sound_category_change(self, choice: str) -> None:
        if not choice:
            return
        self.library.set_sound_category(choice)
        self._select_first_sound_if_needed(force=True)
        self._select_first_meme_sound_if_needed(force=True)
        self._refresh_library_controls()
        self._render_mode_settings(animated=False, preserve_tab=True)
        self._save_preferences()

    def refresh_library(self) -> None:
        self.library.refresh()
        self._select_first_sound_if_needed(force=True)
        self._select_first_meme_sound_if_needed(force=True)
        self._refresh_library_controls()
        self._update_image_preview()
        self._render_mode_settings(animated=False, preserve_tab=True)
        self._save_preferences()

    def add_image_file(self) -> None:
        if import_images(self):
            self.refresh_library()

    def choose_meme_image(self) -> None:
        selected_image = choose_meme_image(self)
        if not selected_image:
            return
        self.selected_meme_image = selected_image
        self.library.refresh()
        self._save_preferences()
        self._render_mode_settings(animated=False, preserve_tab=True)

    def add_sound_file(self) -> None:
        self._add_sound_file_to(self._active_sound_folder())

    def add_sound_file_to_root(self) -> None:
        self._add_sound_file_to(self.library.sounds_dir)

    def _add_sound_file_to(self, target_dir: Path) -> None:
        if import_sound_files(self, target_dir):
            self.refresh_library()

    def choose_single_sound(self) -> None:
        relative_path = choose_sound_in_library(self, self._t("choose_sound"))
        if not relative_path:
            return
        self.selected_single_sound_path = relative_path.as_posix()
        self.selected_single_sound = relative_path.name
        self.library.refresh()
        self._save_preferences()
        self._render_mode_settings(animated=False, preserve_tab=True)

    def choose_meme_sound(self) -> None:
        relative_path = choose_sound_in_library(self, self._t("choose_meme_sound"))
        if not relative_path:
            return
        self.selected_meme_sound_path = relative_path.as_posix()
        self.selected_meme_sound = relative_path.name
        self.library.refresh()
        self._save_preferences()
        self._render_mode_settings(animated=False, preserve_tab=True)

    def _active_sound_folder(self) -> Path:
        return active_sound_folder(self)

    def save_meme_template(self) -> None:
        templates = self.library.save_meme_template(self.meme_top_text, self.meme_bottom_text)
        self._sync_meme_template_combo(templates, {"top": self.meme_top_text, "bottom": self.meme_bottom_text})

    def update_meme_template(self) -> None:
        templates = self.library.update_meme_template(
            self.selected_meme_template,
            self.meme_top_text,
            self.meme_bottom_text,
        )
        self._sync_meme_template_combo(templates, {"top": self.meme_top_text, "bottom": self.meme_bottom_text})

    def delete_meme_template(self) -> None:
        templates = self.library.delete_meme_template(self.selected_meme_template)
        self._sync_meme_template_combo(templates, templates[0])

    def _sync_meme_template_combo(self, templates: list[dict[str, str]], selected: dict[str, str]) -> None:
        selected_key = self._template_key(selected)
        available_keys = {self._template_key(template) for template in templates}
        if selected_key not in available_keys:
            selected = templates[0]
            selected_key = self._template_key(selected)
        self.selected_meme_template = {"top": selected["top"], "bottom": selected["bottom"]}
        self.meme_top_text = selected["top"]
        self.meme_bottom_text = selected["bottom"]
        if hasattr(self, "meme_combo"):
            self.meme_combo.blockSignals(True)
            self.meme_combo.clear()
            for template in templates:
                self.meme_combo.addItem(self._template_label(template), self._template_key(template))
            self.meme_combo.setCurrentIndex(self.meme_combo.findData(selected_key))
            self.meme_combo.blockSignals(False)
        for widget, value in ((getattr(self, "meme_top_input", None), self.meme_top_text), (getattr(self, "meme_bottom_input", None), self.meme_bottom_text)):
            if widget:
                widget.blockSignals(True)
                widget.setText(value)
                widget.blockSignals(False)
        self._save_preferences()

    def _template_key(self, template: dict[str, str]) -> str:
        return json.dumps({"top": template.get("top", ""), "bottom": template.get("bottom", "")}, ensure_ascii=False, sort_keys=True)

    def _template_label(self, template: dict[str, str]) -> str:
        top = template.get("top", "").strip() or "..."
        bottom = template.get("bottom", "").strip() or "..."
        return f"{top[:28]} / {bottom[:28]}"

    def _select_first_sound_if_needed(self, force: bool = False) -> None:
        if self._single_sound_path():
            return
        if force or self.selected_single_sound not in self.library.sounds:
            self.selected_single_sound = self.library.sounds[0] if self.library.sounds else ""
            self.selected_single_sound_path = ""

    def _select_first_meme_sound_if_needed(self, force: bool = False) -> None:
        if force or self.selected_meme_sound not in self.library.sounds:
            self.selected_meme_sound = self.library.sounds[0] if self.library.sounds else ""

    def _update_image_preview(self) -> None:
        image_label = getattr(self, "image_label", None)
        image_name_label = getattr(self, "image_name_label", None)
        if not image_label:
            return
        if self.preview_movie:
            self.preview_movie.stop()
            self.preview_movie.deleteLater()
            self.preview_movie = None
        self.preview_movie_source_size = QSize()
        self.current_pixmap = None
        self._last_preview_target = QSize()

        image_path = self._preview_meme_image_path()
        if not image_path:
            empty_text = self._t("choose_meme_image_hint") if self.meme_image_mode == "single" else self._t("empty_image_preview")
            image_label.setText(empty_text)
            image_label.setPixmap(QPixmap())
            if image_name_label:
                image_name_label.setText(empty_text)
            return

        if image_path.suffix.lower() == ".gif":
            movie = QMovie(str(image_path))
            movie.setCacheMode(QMovie.CacheAll)
            if movie.isValid():
                movie.jumpToFrame(0)
                self.preview_movie_source_size = movie.currentImage().size()
                if self.preview_movie_source_size.isEmpty():
                    self.preview_movie_source_size = movie.frameRect().size()
                self._last_preview_target = self._preview_target_size()
                movie.setScaledSize(self._scaled_movie_size(movie, self._last_preview_target))
                self.preview_movie = movie
                image_label.setMovie(movie)
                movie.start()
            else:
                image_label.setText(self._t("image_error"))
        else:
            pixmap = load_pixmap(image_path)
            if pixmap.isNull():
                image_label.setText(self._t("image_error"))
            else:
                self.current_pixmap = pixmap
                image_label.setPixmap(
                    pixmap.scaled(self._preview_target_size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        if image_name_label:
            if self.meme_image_mode == "random" and len(self.library.images) > 1:
                image_name_label.setText(self._t("next_image_hint"))
            else:
                image_name_label.setText(image_path.name)

    def _preview_target_size(self) -> QSize:
        width = max(1, self.image_label.width() - 22)
        height = max(1, self.image_label.height() - 22)
        return QSize(width, height)

    def _scaled_movie_size(self, movie: QMovie, target: QSize) -> QSize:
        source = self.preview_movie_source_size
        if source.isEmpty():
            source = movie.currentImage().size()
        if source.isEmpty():
            source = movie.frameRect().size()
        if source.isEmpty():
            return target
        source.scale(target, Qt.KeepAspectRatio)
        return source

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API name
        super().resizeEvent(event)
        self._apply_responsive_docks()
        compact_now = self._settings_are_compact()
        if compact_now != getattr(self, "_last_settings_compact", compact_now):
            self._render_mode_settings(animated=False, preserve_tab=True)
        if self.current_pixmap and getattr(self, "image_label", None):
            self.image_label.setPixmap(
                self.current_pixmap.scaled(self._preview_target_size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        if self.preview_movie and getattr(self, "image_label", None):
            target = self._preview_target_size()
            if target != self._last_preview_target:
                self._last_preview_target = target
                self.preview_movie.setScaledSize(self._scaled_movie_size(self.preview_movie, target))

    def next_image(self) -> None:
        if self.meme_image_mode != "random" or not self.library.images:
            return
        self.current_image_index = (self.current_image_index + 1) % len(self.library.images)
        self._update_image_preview()

    def schedule_next_event(self, reset_chaos: bool = False) -> None:
        if reset_chaos:
            self.chaos_factor = 1.0
        self.next_event_time = datetime.now() + timedelta(seconds=self._next_delay_seconds())
        self._update_timer_label()

    def _next_delay_seconds(self) -> int:
        if self.active_mode == MODE_CHAOS:
            delay = int(self.chaos_start_minutes * 60 * self.chaos_factor)
            self.chaos_factor = max(0.05, self.chaos_factor * 0.75)
            return max(self.chaos_floor_seconds, delay)
        min_seconds = self.min_minutes * 60
        max_seconds = max(self.max_minutes * 60, min_seconds)
        return max(5, random.randint(min_seconds, max_seconds))

    def _director_loop(self) -> None:
        if datetime.now() < self._mode_switch_quiet_until:
            self._update_timer_label()
            return
        if self.is_running and datetime.now() >= self.next_event_time:
            self.run_current_mode()
            self.schedule_next_event()
        self._update_timer_label()

    def _update_timer_label(self) -> None:
        if not self.is_running:
            self.timer_label.setText(self._t("timer_paused"))
            return
        remaining = self.next_event_time - datetime.now()
        seconds = max(0, int(remaining.total_seconds()))
        self.timer_label.setText(self._t("next_event", minutes=seconds // 60, seconds=seconds % 60))

    def run_current_mode(self) -> None:
        if self.active_mode == MODE_RANDOM_SOUND:
            self.play_random_sound()
        elif self.active_mode == MODE_SINGLE_SOUND:
            self.play_selected_sound()
        elif self.active_mode == MODE_MEME_POPUP:
            self.preview_meme()
        elif self.active_mode == MODE_FAKE_ERROR:
            self.preview_message()
        elif self.active_mode == MODE_CHAOS:
            self.run_chaos_event()
        elif self.active_mode == MODE_WINDOWS_ERROR:
            self.audio.play_windows_error()
        elif self.active_mode == MODE_CHAT_NOTIFICATION:
            self.play_chat_notification()

    def run_chaos_event(self) -> None:
        actions = []
        enabled = self.chaos_enabled_modes
        if MODE_FAKE_ERROR in enabled:
            actions.append(self.preview_message)
        if MODE_WINDOWS_ERROR in enabled:
            actions.append(self.audio.play_windows_error)
        if MODE_CHAT_NOTIFICATION in enabled:
            actions.append(self.play_chat_notification)
        if MODE_RANDOM_SOUND in enabled and self.library.sounds:
            actions.append(self.play_random_sound)
        if MODE_SINGLE_SOUND in enabled and self._single_sound_path():
            actions.append(self.play_selected_sound)
        if MODE_MEME_POPUP in enabled and self._selected_meme_image_path():
            actions.append(self.preview_meme)
        if not actions:
            actions = [self.preview_message]
        random.choice(actions)()

    def play_random_sound(self) -> None:
        if self.library.sounds:
            self.audio.play_file(self.library.sound_path(random.choice(self.library.sounds)))

    def play_selected_sound(self) -> None:
        sound_path = self._single_sound_path()
        if sound_path:
            self.audio.play_file(sound_path)

    def preview_random_sound(self) -> None:
        self.play_random_sound()

    def preview_meme_selected_sound(self) -> None:
        sound_path = self._single_meme_sound_path()
        if sound_path:
            self.audio.play_file(sound_path)

    def preview_meme_random_sound(self) -> None:
        if self.library.sounds:
            self.audio.play_file(self.library.sound_path(random.choice(self.library.sounds)))

    def play_chat_notification(self) -> None:
        self.audio.play_chat_notification(self._chat_notification_path())

    def _chat_notification_path(self) -> Path | None:
        filename = CHAT_NOTIFICATION_FILES.get(self.selected_chat_notification)
        if not filename:
            return None
        path = self.base_dir / "assets" / CHAT_NOTIFICATION_DIR / filename
        return path if path.is_file() else None

    def preview_message(self) -> None:
        if os.name == "nt":
            ctypes.windll.user32.MessageBoxW(None, self.alert_text, self._t("system_error_title"), 0x00000010 | 0x00001000)
        else:
            QMessageBox.critical(self, self._t("system_error_title"), self.alert_text)

    def preview_meme(self) -> None:
        image_path = self._selected_meme_image_path()
        if not image_path:
            return
        sound_path = self._selected_meme_sound_path()
        if self.meme_sound_enabled and sound_path:
            self.audio.play_file(sound_path)
        dialog = MemeDialog(
            None,
            image_path,
            self.meme_top_text,
            self.meme_bottom_text,
            self.meme_duration,
            self.meme_text_color,
            self.audio.stop_current if self.meme_sound_enabled else None,
        )
        self.meme_dialogs.append(dialog)
        dialog.destroyed.connect(lambda _unused=None, current=dialog: self._discard_meme_dialog(current))
        dialog.showNormal()
        dialog.raise_()
        dialog.activateWindow()

    def _selected_meme_image_path(self) -> Path | None:
        if self.meme_image_mode == "single":
            return self._single_meme_image_path()
        if not self.library.images:
            return None
        return self.library.image_path(random.randrange(len(self.library.images)))

    def _preview_meme_image_path(self) -> Path | None:
        if self.meme_image_mode == "single":
            return self._single_meme_image_path()
        return self.library.image_path(self.current_image_index)

    def _single_meme_image_path(self) -> Path | None:
        if not self.selected_meme_image:
            return None
        path = Path(self.selected_meme_image)
        if not path.is_absolute():
            path = self.base_dir / path
        return path if path.is_file() else None

    def _selected_meme_sound_path(self) -> Path | None:
        if self.meme_sound_mode == "random":
            if not self.library.sounds:
                return None
            return self.library.sound_path(random.choice(self.library.sounds))
        return self._single_meme_sound_path()

    def _single_meme_sound_path(self) -> Path | None:
        if self.selected_meme_sound_path:
            path = self.library.sounds_dir / self.selected_meme_sound_path
            if path.is_file():
                return path
        if self.selected_meme_sound in self.library.sounds:
            return self.library.sound_path(self.selected_meme_sound)
        return None

    def _single_sound_path(self) -> Path | None:
        if self.selected_single_sound_path:
            path = self.library.sounds_dir / self.selected_single_sound_path
            if path.is_file():
                return path
        if self.selected_single_sound in self.library.sounds:
            return self.library.sound_path(self.selected_single_sound)
        return None

    def _discard_meme_dialog(self, dialog: QDialog) -> None:
        if dialog in self.meme_dialogs:
            self.meme_dialogs.remove(dialog)

    def show_help_window(self) -> None:
        HelpDialog(self, self.language).exec()

    def open_kofi(self) -> None:
        webbrowser.open(KO_FI_URL)

    def open_system_path(self, path: Path) -> None:
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                webbrowser.open(path.as_uri())
        except Exception as exc:
            QMessageBox.warning(self, APP_TITLE, str(exc))

    def toggle_camouflage(self, checked: bool = True) -> None:
        self.camouflage_enabled = checked
        self._apply_window_identity()
        self._save_preferences()

    def _apply_window_identity(self) -> None:
        title = STEALTH_TITLE if self.camouflage_enabled else APP_TITLE
        icon = self._windows_program_icon() if self.camouflage_enabled else self._prank_app_icon()
        self.setWindowTitle(title)
        self.setWindowIcon(icon)
        if self.tray_icon:
            self.tray_icon.setToolTip(title)
            self.tray_icon.setIcon(icon)
            self._refresh_tray_menu()

    def _windows_program_icon(self) -> QIcon:
        return self.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

    def check_for_updates(self, manual: bool = True) -> None:
        self._update_check_is_manual = manual
        self.update_service.check()

    def _handle_update_result(self, result: UpdateResult) -> None:
        if result.status == "available":
            choice = QMessageBox.question(
                self,
                APP_TITLE,
                self._t("update_available", version=result.version),
                QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Open,
            )
            if choice == QMessageBox.StandardButton.Open:
                webbrowser.open(result.download_url or result.release_url)
        elif result.status == "current":
            if self._update_check_is_manual:
                QMessageBox.information(self, APP_TITLE, self._t("update_current", version=result.version or APP_VERSION))
        elif result.status == "no_release":
            if self._update_check_is_manual:
                QMessageBox.information(self, APP_TITLE, self._t("update_missing_release", version=APP_VERSION))
        else:
            if self._update_check_is_manual:
                QMessageBox.warning(self, APP_TITLE, self._t("update_error", error=result.error))

    def _build_tray_icon(self) -> None:
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setToolTip(APP_TITLE)
        self.tray_icon.setIcon(self._prank_app_icon())
        self.tray_menu = QMenu()
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self._refresh_tray_menu()
        self.tray_icon.show()

    def _on_tray_activated(self, reason) -> None:
        if reason in {QSystemTrayIcon.ActivationReason.Trigger, QSystemTrayIcon.ActivationReason.DoubleClick}:
            self._restore_window()

    def _refresh_tray_menu(self) -> None:
        if not hasattr(self, "tray_menu"):
            return
        self.tray_menu.clear()
        show_label = STEALTH_TITLE if self.camouflage_enabled else self._t("show_app")
        self.tray_menu.addAction(show_label, self._restore_window)
        self.tray_menu.addAction(self._t("quit"), self.quit_application)

    def _restore_window(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def keyPressEvent(self, event) -> None:  # noqa: N802 - Qt API name
        if event.key() == Qt.Key_Escape:
            self.hide()
            return
        super().keyPressEvent(event)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt API name
        self.quit_application()
        event.accept()

    def quit_application(self) -> None:
        """Close the app completely; hiding/minimizing remains the stealth path."""
        self._save_preferences()
        self._set_visual_animations_running(False)
        if hasattr(self, "loop_timer"):
            self.loop_timer.stop()
        for dialog in tuple(self.meme_dialogs):
            dialog.close()
        self.audio.shutdown()
        if self.tray_icon:
            self.tray_icon.hide()
        QApplication.quit()


def run_qt_app() -> int:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = SoundMakerQtApp()
    window.show()
    return app.exec()
