from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout

from app_config import (
    MODE_CHAOS,
    MODE_CHAT_NOTIFICATION,
    MODE_FAKE_ERROR,
    MODE_MEME_POPUP,
    MODE_RANDOM_SOUND,
    MODE_SINGLE_SOUND,
    MODE_WINDOWS_ERROR,
    MODES,
)
from qt_components import (
    add_folder_picker,
    add_image_preview,
    add_radio_row,
    add_selected_file_controls,
    add_slider_grid,
    add_text_input_row,
    add_toggle_row,
    add_volume_controls as add_volume_controls_component,
    make_radio_group,
    make_slider,
)
from qt_widgets import GardenComboBox, PaintedButton, SafeSlider, SmoothCheckBox


def add_timer_controls(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("delay"), "fieldTitle"))
    app.min_label = app._label(app._t("minimum", value=app.min_minutes), "muted")
    app.min_time_slider = make_slider(0, 60, app.min_minutes, app.on_min_slider)
    app.max_label = app._label(app._t("maximum", value=app.max_minutes), "muted")
    app.max_time_slider = make_slider(0, 60, app.max_minutes, app.on_max_slider)
    add_slider_grid(app.settings_layout, [(app.min_label, app.min_time_slider), (app.max_label, app.max_time_slider)])


def add_chaos_controls(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("chaos_delay_disabled"), "fieldTitle"))
    app.settings_layout.addWidget(app._label(app._t("chaos_help"), "muted"))
    app.chaos_start_label = app._label(app._t("chaos_start", value=app.chaos_start_minutes), "muted")
    start_slider = make_slider(1, 30, app.chaos_start_minutes, app.on_chaos_start_slider)
    app.chaos_floor_label = app._label(app._t("chaos_floor", value=app.chaos_floor_seconds), "muted")
    floor_slider = make_slider(5, 60, app.chaos_floor_seconds, app.on_chaos_floor_slider)
    add_slider_grid(app.settings_layout, [(app.chaos_start_label, start_slider), (app.chaos_floor_label, floor_slider)])
    app.settings_layout.addWidget(app._label(app._t("chaos_choices"), "fieldTitle"))
    hint = app._label(app._t("chaos_choices_hint"), "muted")
    hint.setWordWrap(True)
    app.settings_layout.addWidget(hint)
    app.chaos_mode_checkboxes = {}
    for mode in MODES:
        if mode.key == MODE_CHAOS:
            continue
        checkbox = SmoothCheckBox(mode.name(app.language))
        checkbox.setChecked(mode.key in app.chaos_enabled_modes)
        checkbox.toggled.connect(lambda checked, key=mode.key: app.on_chaos_mode_toggled(key, checked))
        app.chaos_mode_checkboxes[mode.key] = checkbox
        app.settings_layout.addWidget(checkbox)


def add_sound_settings(app: Any) -> None:
    if app.active_mode == MODE_MEME_POPUP:
        app._add_meme_sound_settings()
        return
    if app.active_mode in {MODE_RANDOM_SOUND, MODE_CHAOS}:
        app._add_sound_library_controls()
        app._add_random_sound_status()
    if app.active_mode == MODE_SINGLE_SOUND:
        app._add_single_sound_controls()
    if app.active_mode == MODE_CHAT_NOTIFICATION:
        app._add_chat_notification_controls()
    app._add_volume_controls()


def add_meme_sound_settings(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("meme_sound_choice"), "fieldTitle"))
    controls_shell = QFrame()
    controls_layout = QVBoxLayout(controls_shell)
    controls_layout.setContentsMargins(0, 0, 0, 0)
    controls_layout.setSpacing(7)

    def handle_sound_enabled(enabled: bool) -> None:
        app.on_meme_sound_enabled_changed(enabled)
        hint.setVisible(not enabled)
        controls_shell.setVisible(enabled)

    app.meme_sound_toggle = add_toggle_row(
        app.settings_layout,
        app._t("meme_sound_toggle_label"),
        app.meme_sound_enabled,
        handle_sound_enabled,
        app._t("toggle_no"),
        app._t("toggle_yes"),
    )

    hint = app._label(app._t("meme_sound_disabled"), "muted")
    hint.setWordWrap(True)
    hint.setVisible(not app.meme_sound_enabled)
    app.settings_layout.addWidget(hint)

    parent_layout = app.settings_layout
    app.settings_layout = controls_layout

    app.meme_sound_single_radio, app.meme_sound_random_radio = make_radio_group(
        [
            (app._t("meme_sound_single"), app.meme_sound_mode == "single", lambda checked: app.on_meme_sound_mode_changed("single") if checked else None),
            (app._t("meme_sound_random"), app.meme_sound_mode == "random", lambda checked: app.on_meme_sound_mode_changed("random") if checked else None),
        ]
    )
    add_radio_row(app.settings_layout, [app.meme_sound_single_radio, app.meme_sound_random_radio], app._settings_are_compact())

    if app.meme_sound_mode == "single":
        app._add_meme_single_sound_controls()
    else:
        app._add_sound_library_controls()
        app._add_meme_random_sound_controls()
    app._add_volume_controls()
    app.settings_layout = parent_layout
    controls_shell.setVisible(app.meme_sound_enabled)
    app.settings_layout.addWidget(controls_shell)


def add_sound_library_controls(app: Any) -> None:
    app.sound_category_combo = add_folder_picker(
        app.settings_layout,
        app._t("sound_folder"),
        app.library.sound_categories,
        app.library.selected_sound_category,
        app.on_sound_category_change,
        app._t("import_sound"),
        app.add_sound_file,
        app._settings_are_compact(),
    )


def add_single_sound_controls(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("chosen_sound"), "fieldTitle"))
    app.single_sound_name_label = app._add_selected_sound_controls(
        choose_text=app._t("choose_sound"),
        empty_text=app._t("choose_sound_hint"),
        sound_path=app._single_sound_path(),
        choose_callback=app.choose_single_sound,
        import_callback=app.add_sound_file_to_root,
    )


def add_meme_single_sound_controls(app: Any) -> None:
    app.meme_sound_name_label = app._add_selected_sound_controls(
        choose_text=app._t("choose_meme_sound"),
        empty_text=app._t("choose_meme_sound_hint"),
        sound_path=app._single_meme_sound_path(),
        choose_callback=app.choose_meme_sound,
        import_callback=app.add_sound_file_to_root,
    )


def add_selected_sound_controls(
    app: Any,
    choose_text: str,
    empty_text: str,
    sound_path: Path | None,
    choose_callback: Callable[[], None],
    import_callback: Callable[[], None],
) -> QLabel:
    return add_selected_file_controls(
        app.settings_layout,
        choose_text,
        empty_text,
        sound_path,
        app._t("import_sound"),
        choose_callback,
        import_callback,
        app._settings_are_compact(),
    )


def add_meme_random_sound_controls(app: Any) -> None:
    app._add_random_sound_status()


def add_random_sound_status(app: Any) -> None:
    hint = app._label(app._t("random_sound_hint"), "muted")
    hint.setWordWrap(True)
    app.settings_layout.addWidget(hint)
    app.settings_layout.addWidget(app._label(app._t("sound_count", count=len(app.library.sounds)), "muted"))


def add_chat_notification_controls(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("chat_sound"), "fieldTitle"))
    radios = make_radio_group(
        [
            (app._t("discord_choice"), app.selected_chat_notification == "discord", lambda checked: app.on_chat_notification_selected("discord") if checked else None),
            (app._t("teams_choice"), app.selected_chat_notification == "teams", lambda checked: app.on_chat_notification_selected("teams") if checked else None),
        ]
    )
    add_radio_row(app.settings_layout, radios, app._settings_are_compact())


def add_meme_controls(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("meme_settings"), "fieldTitle"))
    grid = QGridLayout()
    grid.setHorizontalSpacing(10)
    grid.setVerticalSpacing(6)

    app.meme_top_input = QLineEdit(app.meme_top_text)
    app.meme_top_input.setObjectName("gardenInput")
    app.meme_top_input.setMaxLength(120)
    app.meme_top_input.textChanged.connect(app.on_meme_top_text_changed)

    app.meme_bottom_input = QLineEdit(app.meme_bottom_text)
    app.meme_bottom_input.setObjectName("gardenInput")
    app.meme_bottom_input.setMaxLength(120)
    app.meme_bottom_input.textChanged.connect(app.on_meme_bottom_text_changed)

    app.meme_color_combo = GardenComboBox()
    colors = [
        (app._t("meme_color_white"), "#FFFFFF"),
        (app._t("meme_color_cream"), "#FFF0D8"),
        (app._t("meme_color_sakura"), "#F7B6C8"),
        (app._t("meme_color_lantern"), "#F0C66E"),
        (app._t("meme_color_sage"), "#B7D6B0"),
    ]
    for label, color in colors:
        app.meme_color_combo.addItem(label, color)
    color_index = app.meme_color_combo.findData(app.meme_text_color)
    app.meme_color_combo.setCurrentIndex(max(0, color_index))
    app.meme_color_combo.currentIndexChanged.connect(app.on_meme_text_color_selected)

    app.meme_duration_label = app._label(app._t("meme_duration", value=app.meme_duration), "muted")
    duration_slider = SafeSlider(Qt.Horizontal)
    duration_slider.setRange(2, 60)
    duration_slider.setValue(int(app.meme_duration * 10))
    duration_slider.valueChanged.connect(app.on_meme_duration_slider)

    grid.addWidget(app._label(app._t("meme_text_top"), "muted"), 0, 0)
    grid.addWidget(app.meme_top_input, 0, 1)
    grid.addWidget(app._label(app._t("meme_text_bottom"), "muted"), 1, 0)
    grid.addWidget(app.meme_bottom_input, 1, 1)
    grid.addWidget(app._label(app._t("meme_text_color"), "muted"), 2, 0)
    grid.addWidget(app.meme_color_combo, 2, 1)
    grid.addWidget(app.meme_duration_label, 3, 0)
    grid.addWidget(duration_slider, 3, 1)
    grid.setColumnStretch(1, 1)
    app.settings_layout.addLayout(grid)


def add_image_settings(app: Any) -> None:
    app.settings_layout.addWidget(app._label(app._t("meme_image"), "fieldTitle"))
    app.meme_image_single_radio, app.meme_image_random_radio = make_radio_group(
        [
            (app._t("meme_image_single"), app.meme_image_mode == "single", lambda checked: app.on_meme_image_mode_changed("single") if checked else None),
            (app._t("meme_image_random"), app.meme_image_mode == "random", lambda checked: app.on_meme_image_mode_changed("random") if checked else None),
        ]
    )
    add_radio_row(app.settings_layout, [app.meme_image_single_radio, app.meme_image_random_radio], app._settings_are_compact())

    if app.meme_image_mode == "single":
        app.settings_layout.addWidget(app._label(app._t("single_image_hint"), "muted"))
        choose_button = PaintedButton(app._t("choose_meme_image"))
        choose_button.setObjectName("secondaryButton")
        choose_button.clicked.connect(app.choose_meme_image)
        app.settings_layout.addWidget(choose_button)
    else:
        app.settings_layout.addWidget(app._label(app._t("image_folder_hint"), "muted"))
        app.image_category_combo = add_folder_picker(
            app.settings_layout,
            app._t("image_folder"),
            app.library.image_categories,
            app.library.selected_image_category,
            app.on_image_category_change,
            app._t("import_image"),
            app.add_image_file,
            app._settings_are_compact(),
        )

    app.image_label, app.image_name_label = add_image_preview(
        app.settings_layout,
        app._t("choose_meme_image_hint"),
        app._t("next_image_hint"),
        app.next_image if app.meme_image_mode == "random" else None,
        show_name=False,
    )


def add_alert_controls(app: Any) -> None:
    alert_input = QLineEdit(app.alert_text)
    alert_input.setObjectName("gardenInput")
    alert_input.setMaxLength(180)
    alert_input.textChanged.connect(app.on_alert_text_changed)
    add_text_input_row(app.settings_layout, app._t("alert_message"), alert_input, app._settings_are_compact())


def add_volume_controls(app: Any) -> None:
    app.volume_label = add_volume_controls_component(
        app.settings_layout,
        app._t("volume", value=int(app.volume * 100)),
        int(app.volume * 100),
        app.on_volume_slider,
    )
