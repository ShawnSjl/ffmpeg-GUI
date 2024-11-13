from enum import Enum

from PySide6.QtCore import Signal, QObject


class LOG_LEVEL(Enum):
    DEBUG = 1
    INFO = 2
    WARNING = 3
    ERROR = 4

class MySignal(QObject):
    update_signal = Signal(int)

def support_crf(encode_format: str):
    support_list = [
        "H.264",
        "H.265",
        "VP9",
        "AV1"
    ]
    return encode_format in support_list