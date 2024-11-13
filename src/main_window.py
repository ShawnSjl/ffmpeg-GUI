import datetime
from src.utils import *
import src.constants as constants
from PySide6.QtCore import (QDateTime, QDir, QLibraryInfo, QSysInfo, Qt,
                            QTimer, Slot, qVersion, QProcess)
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
        # set window title
        self.setWindowTitle('FFmpeg GUI')

        # create global variables to track status of jobs
        self.is_started = False
        self.jobs = -1
        self.completed_jobs = -1
        self.signal = MySignal()

        input_files_groupbox = self.create_input_files_groupbox()
        config_toolbox = self.create_config_toolbox()
        command_line_groupbox = self.create_command_line_groupbox()
        progress_groupbox = self.create_progress_groupbox()
        log_groupbox = self.create_log_groupbox()   # create log group box

        # create a test button
        self.test_button = QPushButton("Test")
        self.test_button.clicked.connect(self.test)
        self.test_button.setEnabled(False)

        # Set layout
        main_layout = QGridLayout(self)
        main_layout.addWidget(input_files_groupbox, 0, 0, 1, 2)
        main_layout.addWidget(config_toolbox, 1, 0, 1, 2)
        main_layout.addWidget(command_line_groupbox, 2, 0, 1, 2)
        main_layout.addWidget(progress_groupbox, 3, 0, 1, 2)
        main_layout.addWidget(log_groupbox, 4, 0, 1, 2)
        main_layout.addWidget(self.test_button, 5, 0, 1, 2)

        # use signal to update ui
        self.signal.update_signal.connect(self.update_ui)

    @Slot()
    def test(self):
        self.completed_jobs += 1
        self.signal.update_signal.emit(self.completed_jobs)

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
        self.file_list_view.selectionModel().selectionChanged.connect(self.handle_selection)

        # create add button
        add_file_button = QPushButton("Add File")
        add_file_button.clicked.connect(self.add_files)

        # create delete button
        delete_file_button = QPushButton("Delete File")
        delete_file_button.clicked.connect(self.delete_files)

        self.file_info_button = QPushButton("File Info")
        self.file_info_button.setEnabled(False)
        self.file_info_button.clicked.connect(self.show_file_info)

        self.file_info_process = QProcess()
        self.file_info_process.readyReadStandardOutput.connect(self.handle_stdout)
        self.file_info_process.readyReadStandardError.connect(self.handle_stderr)
        self.file_info_process.finished.connect(self.handle_finish)

        # create clear All button
        clear_file_button = QPushButton("Clear All Files")
        clear_file_button.clicked.connect(self.clear_files_list)

        # create bottom button layout
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(add_file_button)
        bottom_layout.addWidget(delete_file_button)
        bottom_layout.addWidget(self.file_info_button)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(clear_file_button)

        # create main layout
        main_layout = QVBoxLayout(result)
        main_layout.addWidget(self.file_list_view)
        main_layout.addLayout(bottom_layout)

        return result

    @Slot()
    def handle_selection(self):
        self.file_info_button.setEnabled(True)

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
        self.file_info_button.setEnabled(False)

    @Slot()
    def show_file_info(self):
        self.print_log(LOG_LEVEL.DEBUG.name, f"File Info")
        command = constants.DEFAULT_FFMPEG_PATH
        item = self.file_model.item(self.file_list_view.currentIndex().row(), 0)
        arguments = ["-i", f"{item.text()}"]

        self.file_info_process.start(command, arguments)

    @Slot()
    def handle_stdout(self):
        data = self.file_info_process.readAllStandardOutput().data().decode("utf-8")
        self.log_editor.append(data)

    @Slot()
    def handle_stderr(self):
        data = self.file_info_process.readAllStandardError().data().decode("utf-8")
        self.log_editor.append(data)

    @Slot()
    def handle_finish(self):
        self.print_log(LOG_LEVEL.INFO.name, f"Finish File Info")

    @Slot()
    def clear_files_list(self):
        """Clear all items in file list"""
        self.file_model.clear()
        self.print_log(LOG_LEVEL.INFO.name, "Clear all items in file list")

        # update ui
        self.signal.update_signal.emit(1)
        self.file_info_button.setEnabled(False)

    def create_config_toolbox(self):
        """Create config Groupbox"""
        result = QTabWidget()

        video_config_groupbox = self.create_video_config_groupbox()
        audio_config_groupbox = self.create_audio_config_groupbox()
        file_format_config_groupbox = self.create_file_format_config_groupbox()
        output_config_groupbox = self.create_output_config_groupbox()

        result.addTab(video_config_groupbox, "Video")
        result.addTab(audio_config_groupbox, "Audio")
        result.addTab(file_format_config_groupbox, "Format")
        result.addTab(output_config_groupbox, "Output")

        return result

    def create_video_config_groupbox(self):
        result = QGroupBox()

        # create encoder choose box
        encoder_label = QLabel("Encoder:")

        main_layout = QGridLayout(result)
        main_layout.addWidget(encoder_label, 0, 0)

        return result

    def create_audio_config_groupbox(self):
        result = QGroupBox()

        # create audio copy button
        self.audio_copy_button = QCheckBox("Copy All Audio")

        main_layout = QGridLayout(result)
        main_layout.addWidget(self.audio_copy_button, 0, 0)

        return result

    def create_file_format_config_groupbox(self):
        result = QGroupBox()

        self.format = QComboBox()
        self.format.addItems(constants.SUPPORT_FILE_FORMAT)
        self.format.currentIndexChanged.connect(self.change_output_format)
        format_label = QLabel("Format:")
        format_label.setBuddy(self.format)

        format_selector_layout = QHBoxLayout()
        format_selector_layout.addWidget(format_label)
        format_selector_layout.addWidget(self.format)

        self.movflag = QCheckBox("Enable Fast Start (Only for mp4 format)")
        self.movflag.setEnabled(False)
        self.movflag.clicked.connect(self.enable_mov_flag)

        main_layout = QGridLayout(result)
        main_layout.addLayout(format_selector_layout, 0, 0)
        main_layout.addWidget(self.movflag, 0, 1)

        return result

    @Slot()
    def change_output_format(self):
        if self.format.currentText() == "mp4":
            self.movflag.setEnabled(True)
        else:
            self.movflag.setEnabled(False)

        self.update_command_line()

    @Slot()
    def enable_mov_flag(self):
        self.update_command_line()

    def create_output_config_groupbox(self):
        result = QGroupBox()

        output_directory_label = QLabel("Output Directory:")
        self.output_directory = QLineEdit()
        self.output_directory.setReadOnly(True)
        output_directory_button = QPushButton("Choose Directory")

        output_directory_layout = QHBoxLayout()
        output_directory_layout.addWidget(output_directory_label)
        output_directory_layout.addWidget(self.output_directory)
        output_directory_layout.addWidget(output_directory_button)

        main_layout = QGridLayout(result)
        main_layout.addLayout(output_directory_layout, 0, 0)

        return result

    def create_command_line_groupbox(self):
        """Create command line Groupbox"""
        result = QGroupBox("Command")

        # create labels
        prefix = QLabel("ffmpeg -i $INPUT$")
        postfix = QLabel("$OUTPUT$")

        # create a command text editor
        self.command_editor = QLineEdit()

        # create reset button
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_command_line)
        reset_button.setDefault(True)

        main_layout = QHBoxLayout(result)
        main_layout.addWidget(prefix)
        main_layout.addWidget(self.command_editor, 8)
        main_layout.addWidget(postfix)
        main_layout.addStretch(1)
        main_layout.addWidget(reset_button)

        return result

    @Slot()
    def update_command_line(self):
        cmd = ""
        if self.movflag.isEnabled() and self.movflag.isChecked():
            cmd += " -movflags faststart"
        self.command_editor.setText(cmd)

    @Slot()
    def reset_command_line(self):
        self.command_editor.clear()

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