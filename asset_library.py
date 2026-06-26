from __future__ import annotations

import json
import shutil
from pathlib import Path

from app_config import DEFAULT_MEME_PRESETS, IMAGE_EXTENSIONS, SOUND_EXTENSIONS


ROOT_CATEGORY = "/"


class AssetLibrary:
    """Indexes image, sound, and meme text files only when the user refreshes."""

    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.images_dir = self.base_dir / "Images"
        self.sounds_dir = self.base_dir / "Sounds"
        self.data_dir = self.base_dir / "data"
        self.meme_presets_path = self.data_dir / "meme_presets.txt"
        self.meme_templates_path = self.data_dir / "meme_templates.json"

        self.selected_image_category = ROOT_CATEGORY
        self.selected_sound_category = ROOT_CATEGORY
        self.image_categories: list[str] = []
        self.sound_categories: list[str] = []
        self.images: list[str] = []
        self.sounds: list[str] = []

        self.ensure_structure()
        self.refresh()

    def ensure_structure(self) -> None:
        self.images_dir.mkdir(exist_ok=True)
        self.sounds_dir.mkdir(exist_ok=True)
        self.data_dir.mkdir(exist_ok=True)
        if not self.meme_presets_path.exists():
            self.meme_presets_path.write_text(
                "\n".join(DEFAULT_MEME_PRESETS) + "\n",
                encoding="utf-8",
            )

    def refresh(self) -> None:
        self.image_categories = self._categories_for(self.images_dir)
        self.sound_categories = self._categories_for(self.sounds_dir)

        if self.selected_image_category not in self.image_categories:
            self.selected_image_category = ROOT_CATEGORY
        if self.selected_sound_category not in self.sound_categories:
            self.selected_sound_category = ROOT_CATEGORY

        self.images = self._files_for(
            self._category_path(self.images_dir, self.selected_image_category),
            IMAGE_EXTENSIONS,
        )
        self.sounds = self._files_for(
            self._category_path(self.sounds_dir, self.selected_sound_category),
            SOUND_EXTENSIONS,
        )

    def set_image_category(self, category: str) -> None:
        self.selected_image_category = category
        self.refresh()

    def set_sound_category(self, category: str) -> None:
        self.selected_sound_category = category
        self.refresh()

    def image_path(self, index: int = 0, filename: str | None = None) -> Path | None:
        if filename:
            return self._category_path(self.images_dir, self.selected_image_category) / filename
        if not self.images:
            return None
        return self._category_path(self.images_dir, self.selected_image_category) / self.images[index % len(self.images)]

    def sound_path(self, filename: str | None = None) -> Path | None:
        if filename:
            return self._category_path(self.sounds_dir, self.selected_sound_category) / filename
        if not self.sounds:
            return None
        return self._category_path(self.sounds_dir, self.selected_sound_category) / self.sounds[0]

    def import_images(self, file_paths: tuple[str, ...] | list[str]) -> None:
        self._copy_files(file_paths, self._category_path(self.images_dir, self.selected_image_category))
        self.refresh()

    def import_sounds(self, file_paths: tuple[str, ...] | list[str]) -> None:
        self._copy_files(file_paths, self._category_path(self.sounds_dir, self.selected_sound_category))
        self.refresh()

    def load_meme_presets(self) -> list[str]:
        self.ensure_structure()
        presets = [
            line.strip()
            for line in self.meme_presets_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        return presets or DEFAULT_MEME_PRESETS.copy()

    def save_meme_preset(self, text: str) -> list[str]:
        clean_text = text.strip()
        presets = self.load_meme_presets()
        if clean_text and clean_text not in presets:
            presets.append(clean_text)
            self._write_meme_presets(presets)
        return presets

    def update_meme_preset(self, old_text: str, new_text: str) -> list[str]:
        old_clean = old_text.strip()
        new_clean = new_text.strip()
        presets = self.load_meme_presets()
        if not old_clean or not new_clean:
            return presets

        if old_clean in presets:
            index = presets.index(old_clean)
            presets[index] = new_clean
        elif new_clean not in presets:
            presets.append(new_clean)

        presets = self._dedupe_presets(presets)
        self._write_meme_presets(presets)
        return presets

    def delete_meme_preset(self, text: str) -> list[str]:
        clean_text = text.strip()
        presets = [preset for preset in self.load_meme_presets() if preset != clean_text]
        if not presets:
            presets = DEFAULT_MEME_PRESETS.copy()
        self._write_meme_presets(presets)
        return presets

    def load_meme_templates(self) -> list[dict[str, str]]:
        """Load two-line meme templates, migrating old one-line presets on demand."""
        self.ensure_structure()
        try:
            raw_templates = json.loads(self.meme_templates_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raw_templates = []

        templates = self._clean_templates(raw_templates)
        if templates:
            return templates
        return [{"top": "", "bottom": preset} for preset in self.load_meme_presets()]

    def save_meme_template(self, top: str, bottom: str) -> list[dict[str, str]]:
        templates = self.load_meme_templates()
        template = self._template(top, bottom)
        if template not in templates and (template["top"] or template["bottom"]):
            templates.append(template)
            self._write_meme_templates(templates)
        return templates

    def update_meme_template(self, old: dict[str, str], top: str, bottom: str) -> list[dict[str, str]]:
        templates = self.load_meme_templates()
        old_template = self._template(old.get("top", ""), old.get("bottom", ""))
        new_template = self._template(top, bottom)
        if not (new_template["top"] or new_template["bottom"]):
            return templates
        if old_template in templates:
            templates[templates.index(old_template)] = new_template
        elif new_template not in templates:
            templates.append(new_template)
        templates = self._dedupe_templates(templates)
        self._write_meme_templates(templates)
        return templates

    def delete_meme_template(self, template: dict[str, str]) -> list[dict[str, str]]:
        selected = self._template(template.get("top", ""), template.get("bottom", ""))
        templates = [item for item in self.load_meme_templates() if item != selected]
        if not templates:
            templates = [{"top": "", "bottom": preset} for preset in DEFAULT_MEME_PRESETS]
        self._write_meme_templates(templates)
        return templates

    def _categories_for(self, base_path: Path) -> list[str]:
        subfolders = sorted(
            [path.name for path in base_path.iterdir() if path.is_dir()],
            key=str.casefold,
        )
        return [ROOT_CATEGORY] + subfolders

    def _files_for(self, folder: Path, extensions: tuple[str, ...]) -> list[str]:
        if not folder.exists():
            return []
        return sorted(
            [
                path.name
                for path in folder.iterdir()
                if path.is_file() and path.suffix.lower() in extensions
            ],
            key=str.casefold,
        )

    def _category_path(self, base_path: Path, category: str) -> Path:
        return base_path if category == ROOT_CATEGORY else base_path / category

    def _copy_files(self, file_paths: tuple[str, ...] | list[str], target_dir: Path) -> None:
        target_dir.mkdir(exist_ok=True)
        for file_path in file_paths:
            source = Path(file_path)
            if source.is_file():
                shutil.copy2(source, target_dir / source.name)

    def _write_meme_presets(self, presets: list[str]) -> None:
        clean_presets = self._dedupe_presets([preset.strip() for preset in presets if preset.strip()])
        self.meme_presets_path.write_text("\n".join(clean_presets) + "\n", encoding="utf-8")

    def _write_meme_templates(self, templates: list[dict[str, str]]) -> None:
        self.meme_templates_path.write_text(
            json.dumps(self._dedupe_templates(templates), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _dedupe_presets(self, presets: list[str]) -> list[str]:
        seen = set()
        clean_presets = []
        for preset in presets:
            if preset not in seen:
                clean_presets.append(preset)
                seen.add(preset)
        return clean_presets

    def _clean_templates(self, raw_templates: object) -> list[dict[str, str]]:
        if not isinstance(raw_templates, list):
            return []
        templates = []
        for item in raw_templates:
            if isinstance(item, dict):
                template = self._template(str(item.get("top", "")), str(item.get("bottom", "")))
                if template["top"] or template["bottom"]:
                    templates.append(template)
        return self._dedupe_templates(templates)

    def _template(self, top: str, bottom: str) -> dict[str, str]:
        return {"top": top.strip()[:120], "bottom": bottom.strip()[:120]}

    def _dedupe_templates(self, templates: list[dict[str, str]]) -> list[dict[str, str]]:
        unique = []
        seen = set()
        for item in templates:
            template = self._template(item.get("top", ""), item.get("bottom", ""))
            key = (template["top"], template["bottom"])
            if key not in seen and (template["top"] or template["bottom"]):
                unique.append(template)
                seen.add(key)
        return unique
