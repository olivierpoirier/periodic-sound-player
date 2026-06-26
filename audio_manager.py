from __future__ import annotations

import threading
from pathlib import Path

import pygame

try:
    import winsound
except ImportError:  # pragma: no cover - Windows-only module
    winsound = None


class AudioManager:
    """Small wrapper around pygame/winsound so the UI does not own audio details."""

    def __init__(self) -> None:
        self.available = False
        try:
            pygame.mixer.init()
            self.available = True
        except pygame.error as exc:
            print(f"Audio unavailable: {exc}")

    def set_volume(self, value: float) -> None:
        if self.available:
            pygame.mixer.music.set_volume(float(value))

    def play_file(self, file_path: Path | None) -> None:
        if not file_path or not self.available:
            return
        threading.Thread(target=self._play_file, args=(file_path,), daemon=True).start()

    def play_windows_error(self) -> None:
        threading.Thread(target=self._play_windows_error, daemon=True).start()

    def play_chat_notification(self, file_path: Path | None = None) -> None:
        if file_path and self.available:
            self.play_file(file_path)
            return
        threading.Thread(target=self._play_chat_notification, daemon=True).start()

    def stop_current(self) -> None:
        if self.available:
            pygame.mixer.music.stop()

    def shutdown(self) -> None:
        if self.available:
            pygame.mixer.quit()

    def _play_file(self, file_path: Path) -> None:
        try:
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
        except pygame.error as exc:
            print(f"Audio playback error: {exc}")

    def _play_windows_error(self) -> None:
        if winsound:
            winsound.MessageBeep(winsound.MB_ICONHAND)

    def _play_chat_notification(self) -> None:
        if winsound:
            winsound.Beep(1200, 140)
            winsound.Beep(1800, 140)
