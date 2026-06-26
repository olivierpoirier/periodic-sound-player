from __future__ import annotations

import json
from typing import Any

from app_config import CHAT_NOTIFICATION_FILES, MODE_BY_KEY, MODE_CHAOS, TRANSLATIONS

MEME_TEXT_COLORS = {"#FFFFFF", "#FFF0D8", "#F7B6C8", "#F0C66E", "#B7D6B0"}


def load_preferences(app: Any) -> None:
    try:
        data = json.loads(app.preferences_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        data = {}
    if not isinstance(data, dict):
        data = {}

    language = data.get("language")
    if language in TRANSLATIONS:
        app.language = language

    mode = data.get("active_mode")
    if mode in MODE_BY_KEY:
        app.active_mode = mode

    app.selected_chat_notification = data.get("selected_chat_notification", app.selected_chat_notification)
    if app.selected_chat_notification not in CHAT_NOTIFICATION_FILES:
        app.selected_chat_notification = "discord"
    app.camouflage_enabled = bool(data.get("camouflage_enabled", app.camouflage_enabled))
    app.selected_theme = str(data.get("selected_theme", app.selected_theme))

    app.min_minutes = _bounded_int(data.get("min_minutes"), app.min_minutes, 0, 60)
    app.max_minutes = _bounded_int(data.get("max_minutes"), app.max_minutes, 0, 60)
    app.chaos_start_minutes = _bounded_int(data.get("chaos_start_minutes"), app.chaos_start_minutes, 1, 30)
    app.chaos_floor_seconds = _bounded_int(data.get("chaos_floor_seconds"), app.chaos_floor_seconds, 5, 60)
    chaos_enabled_modes = data.get("chaos_enabled_modes")
    if isinstance(chaos_enabled_modes, list):
        app.chaos_enabled_modes = {
            mode
            for mode in chaos_enabled_modes
            if isinstance(mode, str) and mode in MODE_BY_KEY and mode != MODE_CHAOS
        } or app.chaos_enabled_modes
    app.volume = min(1.0, max(0.0, float(data.get("volume", app.volume))))
    app.meme_duration = min(6.0, max(0.2, float(data.get("meme_duration", app.meme_duration))))
    app.meme_text_color = str(data.get("meme_text_color", app.meme_text_color))
    if app.meme_text_color not in MEME_TEXT_COLORS:
        app.meme_text_color = "#FFFFFF"
    app.meme_sound_enabled = bool(data.get("meme_sound_enabled", app.meme_sound_enabled))
    app.meme_sound_mode = str(data.get("meme_sound_mode", app.meme_sound_mode))
    if app.meme_sound_mode not in {"single", "random"}:
        app.meme_sound_mode = "single"
    app.selected_meme_sound = str(data.get("selected_meme_sound", app.selected_meme_sound))
    app.selected_meme_sound_path = str(data.get("selected_meme_sound_path", app.selected_meme_sound_path))
    app.meme_image_mode = str(data.get("meme_image_mode", app.meme_image_mode))
    if app.meme_image_mode not in {"single", "random"}:
        app.meme_image_mode = "single"
    app.selected_meme_image = str(data.get("selected_meme_image", app.selected_meme_image))
    app.ambient_effects_enabled = bool(data.get("ambient_effects_enabled", app.ambient_effects_enabled))
    app.selected_single_sound = str(data.get("selected_single_sound", app.selected_single_sound))
    app.selected_single_sound_path = str(data.get("selected_single_sound_path", app.selected_single_sound_path))
    app.alert_text = str(data.get("alert_text", app._t("default_alert")))[:180]

    image_category = data.get("image_category")
    if image_category in app.library.image_categories:
        app.library.set_image_category(image_category)
    sound_category = data.get("sound_category")
    if sound_category in app.library.sound_categories:
        app.library.set_sound_category(sound_category)


def save_preferences(app: Any) -> None:
    data = {
        "language": app.language,
        "active_mode": app.active_mode,
        "selected_theme": app.selected_theme,
        "selected_chat_notification": app.selected_chat_notification,
        "camouflage_enabled": app.camouflage_enabled,
        "min_minutes": app.min_minutes,
        "max_minutes": app.max_minutes,
        "chaos_start_minutes": app.chaos_start_minutes,
        "chaos_floor_seconds": app.chaos_floor_seconds,
        "chaos_enabled_modes": sorted(app.chaos_enabled_modes),
        "volume": app.volume,
        "meme_duration": app.meme_duration,
        "meme_text_color": app.meme_text_color,
        "meme_sound_enabled": app.meme_sound_enabled,
        "meme_sound_mode": app.meme_sound_mode,
        "selected_meme_sound": app.selected_meme_sound,
        "selected_meme_sound_path": app.selected_meme_sound_path,
        "meme_image_mode": app.meme_image_mode,
        "selected_meme_image": app.selected_meme_image,
        "ambient_effects_enabled": app.ambient_effects_enabled,
        "selected_single_sound": app.selected_single_sound,
        "selected_single_sound_path": app.selected_single_sound_path,
        "alert_text": app.alert_text,
        "image_category": app.library.selected_image_category,
        "sound_category": app.library.selected_sound_category,
    }
    app.preferences_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _bounded_int(value: object, fallback: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        return fallback
    return max(low, min(high, number))
