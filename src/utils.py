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

def get_output_file_path(enable_rename: bool, rename_mode: str, rename_content: str, index: int, format: str, original_file_path: str, output_directory: str):
    # get original file name without file extension
    file_name = original_file_path.split("/")[-1]
    file_name = file_name.split(".")[0]

    # get output directory
    if output_directory == '':
        output_directory = '/'.join(original_file_path.split("/")[0:-1])
    result = f"{output_directory}/"
    if enable_rename:
        match rename_mode:
            case "Add Prefix":
                result += f"{rename_content}-{file_name}.{format}"
            case "Add Suffix":
                result += f"{file_name}-{rename_content}.{format}"
            case "Rename with Indexed Number":
                result += f"{rename_content}-{index}.{format}"
    else:
        result += f"{file_name}.{format}"
    return result