from __future__ import annotations

import threading

from PySide6.QtCore import QObject, Signal

from app_config import APP_VERSION, UPDATE_REPOSITORY
from update_manager import check_for_update


class UpdateService(QObject):
    """Runs the GitHub release check away from the Qt event loop."""

    completed = Signal(object)

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._checking = False

    def check(self) -> bool:
        if self._checking:
            return False
        self._checking = True
        threading.Thread(target=self._run_check, daemon=True).start()
        return True

    def _run_check(self) -> None:
        result = check_for_update(UPDATE_REPOSITORY, APP_VERSION)
        self._checking = False
        self.completed.emit(result)
