from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from PySide6.QtWidgets import QFileDialog, QMessageBox

from app_config import APP_TITLE

IMAGE_FILTER = "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp *.avif)"
SOUND_FILTER = "Audio (*.mp3 *.wav *.ogg)"


def import_images(app: Any) -> bool:
    files, _ = QFileDialog.getOpenFileNames(app, app._t("import_image"), str(app.base_dir), IMAGE_FILTER)
    if not files:
        return False
    app.library.import_images(files)
    app.current_image_index = 0
    return True


def choose_meme_image(app: Any) -> str | None:
    source_name, _ = QFileDialog.getOpenFileName(app, app._t("choose_meme_image"), str(app.base_dir), IMAGE_FILTER)
    if not source_name:
        return None
    source = Path(source_name)
    if not source.is_file():
        return None
    target = _unique_target(app.library.images_dir, source)
    try:
        _copy_if_needed(source, target)
    except OSError as error:
        QMessageBox.warning(app, APP_TITLE, str(error))
        return None
    return target.relative_to(app.base_dir).as_posix()


def import_sound_files(app: Any, target_dir: Path) -> bool:
    files, _ = QFileDialog.getOpenFileNames(app, app._t("import_sound"), str(target_dir), SOUND_FILTER)
    if not files:
        return False
    copy_files(files, target_dir)
    return True


def choose_sound_in_library(app: Any, title: str) -> Path | None:
    source_name, _ = QFileDialog.getOpenFileName(app, title, str(app.library.sounds_dir), SOUND_FILTER)
    if not source_name:
        return None
    source = Path(source_name)
    if not source.is_file():
        return None
    try:
        return source.resolve().relative_to(app.library.sounds_dir.resolve())
    except ValueError:
        target = _unique_target(app.library.sounds_dir, source)
        try:
            _copy_if_needed(source, target)
        except OSError as error:
            QMessageBox.warning(app, APP_TITLE, str(error))
            return None
        return target.relative_to(app.library.sounds_dir)


def copy_files(files: tuple[str, ...] | list[str], target_dir: Path) -> None:
    target_dir.mkdir(exist_ok=True)
    for file_name in files:
        source = Path(file_name)
        if source.is_file():
            shutil.copy2(source, target_dir / source.name)


def active_sound_folder(app: Any) -> Path:
    if app.library.selected_sound_category == "/":
        return app.library.sounds_dir
    return app.library.sounds_dir / app.library.selected_sound_category


def _unique_target(target_dir: Path, source: Path) -> Path:
    target = target_dir / source.name
    suffix = 2
    while target.exists() and target.resolve() != source.resolve():
        target = target_dir / f"{source.stem}-{suffix}{source.suffix.lower()}"
        suffix += 1
    return target


def _copy_if_needed(source: Path, target: Path) -> None:
    if target.resolve() != source.resolve():
        shutil.copy2(source, target)
