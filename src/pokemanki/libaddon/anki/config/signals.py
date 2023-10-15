from typing import TYPE_CHECKING

from aqt.qt import qtmajor

if TYPE_CHECKING or qtmajor >= 6:
    from PyQt6.QtCore import QObject, pyqtSignal
else:
    from PyQt5.QtCore import QObject, pyqtSignal


class ConfigSignals(QObject):
    initialized = pyqtSignal()
    saved = pyqtSignal()
    loaded = pyqtSignal()
    reset = pyqtSignal()
    deleted = pyqtSignal()
    unloaded = pyqtSignal()
