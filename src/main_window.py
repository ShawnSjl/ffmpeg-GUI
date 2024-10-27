import sys
from PySide6.QtCore import (QDateTime, QDir, QLibraryInfo, QSysInfo, Qt,
                            QTimer, Slot, qVersion)
from PySide6.QtGui import (QCursor, QDesktopServices, QGuiApplication, QIcon,
                           QKeySequence, QShortcut, QStandardItem,
                           QStandardItemModel)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                               QCommandLinkButton, QDateTimeEdit, QDial,
                               QDialog, QDialogButtonBox, QFileSystemModel,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListView, QMenu, QPlainTextEdit,
                               QProgressBar, QPushButton, QRadioButton,
                               QScrollBar, QSizePolicy, QSlider, QSpinBox,
                               QStyleFactory, QTableWidget, QTabWidget,
                               QTextBrowser, QTextEdit, QToolBox, QToolButton,
                               QTreeView, QVBoxLayout, QWidget, QFileDialog)

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('FFmpeg GUI')

        # create main layout
        layout = QVBoxLayout()

        # Show result
        self.result_label = QLabel('')
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # file selector
        self.file_path_edit = QLineEdit(self)
        self.file_path_edit.setPlaceholderText('Enter file path')
        select_file_button = QPushButton('Select file')
        select_file_button.clicked.connect(self.open_file_dialog())

        file_layout = QHBoxLayout()
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(select_file_button)

        # text input
        self.text_input = QLineEdit(self)
        self.text_input.setPlaceholderText('Enter text')

        # Button
        submit_button = QPushButton('Submit')
        submit_button.clicked.connect(self.on_submit())

        # Set layout
        layout.addLayout(file_layout)
        layout.addWidget(self.text_input)
        layout.addWidget(submit_button)
        layout.addWidget(self.result_label)

        self.setLayout(layout)


    @Slot()
    def open_file_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Select file', '', "All Files (*)")
        if file_path:
            self.file_path_edit.setText(file_path)

    @Slot()
    def on_submit(self):
        file_path = self.file_path_edit.text()
        input_text = self.text_input.text()

        if file_path and input_text:
            self.result_label.setText(f"File Path: {file_path}\nInput Text: {input_text}")
        else:
            self.result_label.setText('')