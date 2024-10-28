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
from src.utils import *

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # set window title
        self.setWindowTitle('FFmpeg GUI')

        # create global variables to track status of jobs
        self.is_started = False
        self.jobs = -1
        self.completed_jobs = -1
        self.signal = MySignal()

        input_files_groupbox = self.create_input_files_groupbox()
        config_groupbox = self.create_config_groupbox()
        progress_groupbox = self.create_progress_groupbox()
        log_groupbox = self.create_log_groupbox()   # create log group box

        # Set layout
        main_layout = QGridLayout(self)
        main_layout.addWidget(input_files_groupbox, 0, 0)
        main_layout.addWidget(config_groupbox, 0, 1)
        main_layout.addWidget(progress_groupbox, 1, 0, 1, 2)
        main_layout.addWidget(log_groupbox, 2, 0, 1, 2)

        # use signal to update ui
        self.signal.update_signal.connect(self.update_ui)

    @Slot()
    def update_ui(self):
        # if work is done, set as finished
        if self.is_started and self.completed_jobs == self.jobs:
            self.is_started = False
            self.start_button.setEnabled(self.file_model.rowCount() > 0)
            self.stop_button.setEnabled(False)
            self.test_button.setEnabled(False)
            self.update_progress_bar()
            self.print_log(LOG_LEVEL.INFO.name, "Work done")
            return

        if self.is_started:
            # if work is start, only update progress bar
            self.update_progress_bar()
        else:
            # if work is not start yet, enable button if there are files as input
            self.start_button.setEnabled(self.file_model.rowCount() > 0)

    def create_input_files_groupbox(self):
        """Create input files Groupbox"""
        result = QGroupBox("Input Files")

        self.file_model = QStandardItemModel()

        # create file list view
        self.file_list_view = QListView()
        self.file_list_view.setModel(self.file_model)

        # create add button
        add_file_button = QPushButton("Add File")
        add_file_button.clicked.connect(self.add_files)

        # create delete button
        delete_file_button = QPushButton("Delete File")
        delete_file_button.clicked.connect(self.delete_files)

        # create clear All button
        clear_file_button = QPushButton("Clear All Files")
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

        # update ui
        self.signal.update_signal.emit(1)

    @Slot()
    def delete_files(self):
        """Delete files from file list"""
        selected_indexes = self.file_list_view.selectedIndexes()
        for index in selected_indexes:
            item = self.file_model.item(index.row(), 0)
            self.print_log(LOG_LEVEL.INFO.name, f"Delete file {item.text()}")
            self.file_model.removeRow(index.row())

        # update ui
        self.signal.update_signal.emit(1)

    @Slot()
    def clear_files_list(self):
        """Clear all items in file list"""
        self.file_model.clear()
        self.print_log(LOG_LEVEL.INFO.name, "Clear all items in file list")

        # update ui
        self.signal.update_signal.emit(1)

    def create_config_groupbox(self):
        """Create config Groupbox"""
        result = QGroupBox("Config")

        # create a test button
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.test)
        self.test_button.setEnabled(False)

        main_layout = QHBoxLayout(result)
        main_layout.addWidget(self.test_button)

        return result

    @Slot()
    def test(self):
        self.completed_jobs += 1
        self.signal.update_signal.emit(self.completed_jobs)

    def create_progress_groupbox(self):
        """Create progress Groupbox"""
        result = QGroupBox("Progress")

        # create start button
        self.start_button = QPushButton("Start")
        self.start_button.clicked.connect(self.start)
        self.start_button.setEnabled(False)

        # create stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self.terminate)
        self.stop_button.setEnabled(False)

        # create progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setEnabled(False)

        # main layout
        main_layout = QHBoxLayout(result)
        main_layout.addWidget(self.start_button)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.stop_button)

        return result

    @Slot()
    def start(self):
        # reset variables
        self.is_started = True
        self.completed_jobs = 0
        self.jobs = self.file_model.rowCount()

        # update ui
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.test_button.setEnabled(True)
        self.progress_bar.setEnabled(True)
        self.update_progress_bar()

        # print log
        self.print_log(LOG_LEVEL.INFO.name, "Start working")

    @Slot()
    def terminate(self):
        # update widgets
        self.is_started = False
        self.completed_jobs = -1
        self.jobs = -1

        # update ui
        self.start_button.setEnabled(self.file_model.rowCount() > 0)
        self.stop_button.setEnabled(False)
        self.test_button.setEnabled(False)
        self.progress_bar.setEnabled(False)

        # print log
        self.print_log(LOG_LEVEL.INFO.name, "Terminate work")

    @Slot()
    def update_progress_bar(self):
        self.progress_bar.setValue(round((self.completed_jobs / self.jobs) * 100))

    def create_log_groupbox(self):
        """Create Log Browser Groupbox"""
        result = QGroupBox()

        # create Log label
        log_label = QLabel("Log")

        # create clear log button
        clear_pushbutton = QPushButton("Clear")
        clear_pushbutton.clicked.connect(self.clear_log)
        clear_pushbutton.setDefault(True)

        # define top layout
        top_layout = QHBoxLayout()
        top_layout.addWidget(log_label)
        top_layout.addStretch(1)
        top_layout.addWidget(clear_pushbutton)

        # create log browser
        self.log_editor = QTextEdit()
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