from __future__ import annotations

import os
import platform
import shutil
import subprocess
import webbrowser
from pathlib import Path


SYSTEM_NAME = platform.system().lower()
IS_WINDOWS = os.name == "nt"
IS_MACOS = SYSTEM_NAME == "darwin"
IS_LINUX = SYSTEM_NAME == "linux"


def platform_stealth_title() -> str:
    if IS_WINDOWS:
        return "Host Process for Windows Tasks"
    if IS_MACOS:
        return "System Events Helper"
    if IS_LINUX:
        return "System Monitor Helper"
    return "System Helper Process"


def open_path(path: Path) -> None:
    resolved = path.resolve()
    if IS_WINDOWS:
        os.startfile(resolved)  # type: ignore[attr-defined]
        return
    if IS_MACOS:
        subprocess.Popen(["open", str(resolved)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    xdg_open = shutil.which("xdg-open")
    if xdg_open:
        subprocess.Popen([xdg_open, str(resolved)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    gio = shutil.which("gio")
    if gio:
        subprocess.Popen([gio, "open", str(resolved)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return

    webbrowser.open(resolved.as_uri())
