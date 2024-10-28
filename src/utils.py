from enum import Enum

from PySide6.QtCore import Signal, QObject


class LOG_LEVEL(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4

class MySignal(QObject):
    update_signal = Signal(int)