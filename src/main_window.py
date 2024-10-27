import sys
import datetime
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
from src.widget_utils import *
from src.utils import *

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # set window title
        self.setWindowTitle('FFmpeg GUI')

        input_files_groupbox = self.create_input_files_groupbox()
        log_groupbox = self.create_log_groupbox()   # create log group box

        # Set layout
        main_layout = QGridLayout(self)
        main_layout.addWidget(input_files_groupbox, 0, 0)
        main_layout.addWidget(log_groupbox, 1, 0, 1, 2)

    def create_input_files_groupbox(self):
        """Create input files Groupbox"""
        result = QGroupBox("Input Files")
        init_widget(result, "input_files_groupbox")

        self.file_model = QStandardItemModel()

        # create file list view
        self.file_list_view = QListView()
        init_widget(self.file_list_view, "file_list_view")
        self.file_list_view.setModel(self.file_model)

        # create add button
        add_file_button = QPushButton("Add File")
        init_widget(add_file_button, "add_file_button")
        add_file_button.clicked.connect(self.add_files)

        # create delete button
        delete_file_button = QPushButton("Delete File")
        init_widget(delete_file_button, "delete_file_button")
        delete_file_button.clicked.connect(self.delete_files)

        # create clear All button
        clear_file_button = QPushButton("Clear All Files")
        init_widget(clear_file_button, "clear_file_button")
        clear_file_button.clicked.connect(self.clear_files_list)

        # create bottom button layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(add_file_button)
        bottom_layout.addWidget(delete_file_button)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(clear_file_button)

        # create main layout
        main_layout = QVBoxLayout(result)
        main_layout.addWidget(self.file_list_view)
        main_layout.addLayout(bottom_layout)

        return result

    @Slot()
    def add_files(self):
        """Add new files into file list"""
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select file', '', "All Files (*)")

        for file_path in file_paths:
            item = QStandardItem(file_path)
            self.file_model.appendRow(item)
            self.print_log(LOG_LEVEL.INFO.name, f"Add file {file_path}")

    @Slot()
    def delete_files(self):
        """Delete files from file list"""
        selected_indexes = self.file_list_view.selectedIndexes()
        for index in selected_indexes:
            item = self.file_model.item(index.row(), 0)
            self.print_log(LOG_LEVEL.INFO.name, f"Delete file {item.text()}")
            self.file_model.removeRow(index.row())

    @Slot()
    def clear_files_list(self):
        """Clear all items in file list"""
        self.file_model.clear()
        self.print_log(LOG_LEVEL.INFO.name, "Clear all items in file list")

    # def create_progress_groupbox(self):
    #     """Create progress Groupbox"""
    #     result = QGroupBox("Progress")



    def create_log_groupbox(self):
        """Create Log Browser Groupbox"""
        result = QGroupBox()
        init_widget(result, "log_groupbox")

        # create Log label
        log_label = QLabel("Log")
        init_widget(log_label, "log_label")

        # create clear log button
        clear_pushbutton = QPushButton("Clear")
        init_widget(clear_pushbutton, "clear_pushbutton")
        clear_pushbutton.clicked.connect(self.clear_log)
        clear_pushbutton.setDefault(True)

        # define top layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(log_label)
        top_layout.addStretch(1)
        top_layout.addWidget(clear_pushbutton)

        # create log browser
        self.log_editor = QTextEdit()
        init_widget(self.log_editor, "log_editor")
        self.log_editor.setReadOnly(True)

        # overall layout
        main_layout = QVBoxLayout(result)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.log_editor)

        return result

    @Slot(str, str)
    def print_log(self, log_level, log):
        """Print log message"""
        self.log_editor.append(f"{datetime.datetime.now()}  [{log_level}]  \t{log}")

    @Slot()
    def clear_log(self):
        """Clear log browser"""
        self.log_editor.clear()