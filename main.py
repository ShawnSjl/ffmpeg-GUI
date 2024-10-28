# Copyright © 2024 Jiale Song. All rights reserved.

import sys
from PySide6.QtWidgets import QApplication
from src.main_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(800, 900)
    window.show()
    sys.exit(app.exec())