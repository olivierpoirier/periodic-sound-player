from __future__ import annotations

import math
import os
import shutil
import struct
import subprocess
import threading
import time
from pathlib import Path

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "hide")

import pygame

from platform_utils import IS_LINUX, IS_MACOS, IS_WINDOWS

try:
    import winsound
except ImportError:  # pragma: no cover - Windows-only module
    winsound = None


class AudioManager:
    """Small wrapper around pygame and OS sounds so the UI does not own audio details."""

    def __init__(self) -> None:
        self.available = False
        self.can_generate_tones = False
        self.volume = 0.7
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            self.available = True
            self.can_generate_tones = True
        except pygame.error as exc:
            try:
                pygame.mixer.init()
                self.available = True
                init = pygame.mixer.get_init()
                self.can_generate_tones = bool(init and init[1] == -16)
            except pygame.error:
                print(f"Audio unavailable: {exc}")

    def set_volume(self, value: float) -> None:
        self.volume = max(0.0, min(1.0, float(value)))
        if self.available:
            pygame.mixer.music.set_volume(self.volume)

    def play_file(self, file_path: Path | None) -> None:
        if not file_path or not file_path.is_file() or not self.available:
            return
        threading.Thread(target=self._play_file, args=(file_path,), daemon=True).start()

    def play_system_error(self) -> None:
        threading.Thread(target=self._play_system_error, daemon=True).start()

    def play_windows_error(self) -> None:
        self.play_system_error()

    def play_chat_notification(self, file_path: Path | None = None) -> None:
        if file_path and self.available:
            self.play_file(file_path)
            return
        threading.Thread(target=self._play_chat_notification, daemon=True).start()

    def stop_current(self) -> None:
        if self.available:
            pygame.mixer.music.stop()
            pygame.mixer.stop()

    def shutdown(self) -> None:
        if self.available:
            pygame.mixer.quit()

    def _play_file(self, file_path: Path) -> None:
        try:
            pygame.mixer.music.load(str(file_path))
            pygame.mixer.music.play()
        except pygame.error as exc:
            print(f"Audio playback error: {exc}")

    def _play_system_error(self) -> None:
        if IS_WINDOWS and winsound:
            winsound.MessageBeep(winsound.MB_ICONHAND)
            return
        if self._play_desktop_error_sound():
            return
        self._play_tone_sequence([(330, 0.18), (220, 0.22)])

    def _play_chat_notification(self) -> None:
        if IS_WINDOWS and winsound:
            winsound.Beep(1200, 140)
            winsound.Beep(1800, 140)
            return
        self._play_tone_sequence([(980, 0.08), (1480, 0.1)])

    def _play_desktop_error_sound(self) -> bool:
        if IS_MACOS:
            afplay = shutil.which("afplay")
            sound = Path("/System/Library/Sounds/Basso.aiff")
            if afplay and sound.is_file():
                return self._run_audio_command([afplay, str(sound)])

        if IS_LINUX:
            canberra = shutil.which("canberra-gtk-play")
            if canberra and self._run_audio_command([canberra, "-i", "dialog-error"]):
                return True

            paplay = shutil.which("paplay")
            for sound in (
                Path("/usr/share/sounds/freedesktop/stereo/dialog-error.oga"),
                Path("/usr/share/sounds/ubuntu/stereo/dialog-error.ogg"),
            ):
                if paplay and sound.is_file() and self._run_audio_command([paplay, str(sound)]):
                    return True

        return False

    def _run_audio_command(self, args: list[str]) -> bool:
        try:
            result = subprocess.run(
                args,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=3,
                check=False,
            )
            return result.returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            return False

    def _play_tone_sequence(self, tones: list[tuple[int, float]]) -> None:
        if not self.available or not self.can_generate_tones:
            if IS_WINDOWS and winsound:
                for frequency, duration in tones:
                    winsound.Beep(int(frequency), max(1, int(duration * 1000)))
            return

        for frequency, duration in tones:
            try:
                sound = self._make_tone(frequency, duration)
                sound.set_volume(self.volume)
                channel = sound.play()
                if channel:
                    time.sleep(duration + 0.03)
            except pygame.error as exc:
                print(f"Generated audio playback error: {exc}")
                return

    def _make_tone(self, frequency: int, duration: float) -> pygame.mixer.Sound:
        init = pygame.mixer.get_init()
        sample_rate = init[0] if init else 44100
        channels = max(1, init[2] if init else 2)
        frame_count = max(1, int(sample_rate * duration))
        attack = max(1, int(sample_rate * 0.01))
        release = max(1, int(sample_rate * 0.02))
        amplitude = int(32767 * 0.28)
        frames = bytearray()

        for index in range(frame_count):
            fade_in = min(1.0, index / attack)
            fade_out = min(1.0, (frame_count - index) / release)
            envelope = min(fade_in, fade_out)
            sample = int(math.sin(2 * math.pi * frequency * index / sample_rate) * amplitude * envelope)
            packed = struct.pack("<h", sample)
            frames.extend(packed * channels)

        return pygame.mixer.Sound(buffer=bytes(frames))
