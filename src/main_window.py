import datetime
from src.utils import *
import src.constants as constants
from PySide6.QtCore import (QDateTime, QDir, QLibraryInfo, QSysInfo, Qt,
                            QTimer, Slot, qVersion, QProcess)
from PySide6.QtGui import (QCursor, QDesktopServices, QGuiApplication, QIcon,
                           QKeySequence, QShortcut, QStandardItem,
                           QStandardItemModel, QIntValidator, QDoubleValidator)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox,
                               QCommandLinkButton, QDateTimeEdit, QDial,
                               QDialog, QDialogButtonBox, QFileSystemModel,
                               QGridLayout, QGroupBox, QHBoxLayout, QLabel,
                               QLineEdit, QListView, QMenu, QPlainTextEdit,
                               QProgressBar, QPushButton, QRadioButton,
                               QScrollBar, QSizePolicy, QSlider, QSpinBox,
                               QStyleFactory, QTableWidget, QTabWidget,
                               QTextBrowser, QTextEdit, QToolBox, QToolButton,
                               QTreeView, QVBoxLayout, QWidget, QFileDialog, QFrame)


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
        print(self.processes[self.completed_jobs])
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
        file_filter = "Video Files (*.mp4 *.avi *.mkv *.mov *.flv *.wmv)"
        file_paths, _ = QFileDialog.getOpenFileNames(self, 'Select file', '', file_filter)

        # Create set for exists files
        item_set = set()
        for row in range(self.file_model.rowCount()):
            item_text = self.file_model.item(row, 0).text()
            item_set.add(item_text)

        for file_path in file_paths:
            if file_path not in item_set:
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

        # create enable encode format button
        self.enable_encode_format = QCheckBox("Specifying Encoding Format")
        self.enable_encode_format.clicked.connect(self.enable_change_encode)

        # create encode format choose box
        self.encode_format = QComboBox()
        self.encode_format.addItems(constants.SUPPORT_VIDEO_ENCODE_FORMAT.keys())
        self.encode_format.currentIndexChanged.connect(self.change_encode_format)
        self.encode_format.setEnabled(False)
        encode_format_label = QLabel("Encode Format:")
        encode_format_label.setBuddy(self.encode_format)

        # encode format layout
        encode_format_layout = QHBoxLayout()
        encode_format_layout.addWidget(self.enable_encode_format)
        encode_format_layout.addStretch(1)
        encode_format_layout.addWidget(encode_format_label)
        encode_format_layout.addWidget(self.encode_format)

        # encode speed
        self.encode_speed = QComboBox()
        self.encode_speed.addItems(constants.ENCODE_SPEED)
        self.encode_speed.setCurrentIndex(5)
        self.encode_speed.currentIndexChanged.connect(self.change_encode_speed)
        encode_speed_label = QLabel("Encode Speed:")
        encode_speed_label.setBuddy(self.encode_speed)

        # encode speed layout
        encode_speed_layout = QHBoxLayout()
        encode_speed_layout.addStretch(1)
        encode_speed_layout.addWidget(encode_speed_label)
        encode_speed_layout.addWidget(self.encode_speed)

        # enable video framerate
        self.enable_video_framerate = QCheckBox("Specifying Video Framerate")
        self.enable_video_framerate.clicked.connect(self.enable_change_framerate)

        # video framerate
        self.video_framerate = QLineEdit()
        self.video_framerate.setEnabled(False)
        self.video_framerate.setValidator(QDoubleValidator(0.0, 1000.0, 2, self))
        self.video_framerate.setText("24")
        self.video_framerate.textChanged.connect(self.update_command_line)
        video_framerate_label = QLabel("Video Framerate:")
        video_framerate_label.setBuddy(self.video_framerate)

        # video framerate layout
        video_framerate_layout = QHBoxLayout()
        video_framerate_layout.addWidget(self.enable_video_framerate)
        video_framerate_layout.addStretch(1)
        video_framerate_layout.addWidget(video_framerate_label)
        video_framerate_layout.addWidget(self.video_framerate)

        # enable video scale
        self.enable_video_scale = QCheckBox("Specifying Video Scale")
        self.enable_video_scale.clicked.connect(self.enable_change_scale)

        # video scale
        self.video_scale = QLineEdit()
        self.video_scale.setEnabled(False)
        self.video_scale.setText("1920:1080")
        self.video_scale.textChanged.connect(self.update_command_line)
        video_scale_label = QLabel("Video Scale:")
        video_scale_label.setBuddy(self.video_scale)

        # video scale layout
        video_scale_layout = QHBoxLayout()
        video_scale_layout.addWidget(self.enable_video_scale)
        video_scale_layout.addStretch(1)
        video_scale_layout.addWidget(video_scale_label)
        video_scale_layout.addWidget(self.video_scale)

        # video quality
        self.video_quality = QLineEdit()
        self.video_quality.setEnabled(False)
        self.video_quality.setValidator(QIntValidator(0, 51))
        self.video_quality.setText("28")
        self.video_quality.textChanged.connect(self.update_command_line)
        video_quality_label = QLabel("Constant Rate Factor(Video Quality):")
        video_quality_label.setBuddy(self.video_quality)

        # video quality layout
        video_quality_layout = QHBoxLayout()
        video_quality_layout.addStretch(1)
        video_quality_layout.addWidget(video_quality_label)
        video_quality_layout.addWidget(self.video_quality)

        # main layout
        main_layout = QVBoxLayout(result)
        main_layout.addLayout(encode_format_layout)
        main_layout.addLayout(encode_speed_layout)
        main_layout.addLayout(video_framerate_layout)
        main_layout.addLayout(video_scale_layout)
        main_layout.addLayout(video_quality_layout)

        return result

    @Slot()
    def enable_change_encode(self):
        if self.enable_encode_format.isChecked():
            self.encode_format.setEnabled(True)
            self.video_quality.setEnabled(support_crf(self.encode_format.currentText()))
        else:
            self.encode_format.setEnabled(False)
            self.video_quality.setEnabled(False)

        self.update_command_line()

    @Slot()
    def change_encode_format(self):
        self.video_quality.setEnabled(support_crf(self.encode_format.currentText()))
        self.update_command_line()

    @Slot()
    def change_encode_speed(self):
        self.update_command_line()

    @Slot()
    def enable_change_framerate(self):
        if self.enable_video_framerate.isChecked():
            self.video_framerate.setEnabled(True)
        else:
            self.video_framerate.setEnabled(False)

        self.update_command_line()

    @Slot()
    def enable_change_scale(self):
        if self.enable_video_scale.isChecked():
            self.video_scale.setEnabled(True)
        else:
            self.video_scale.setEnabled(False)

        self.update_command_line()

    def create_audio_config_groupbox(self):
        result = QGroupBox()

        # create audio copy button
        self.audio_copy_button = QCheckBox("Copy All Audio")
        self.audio_copy_button.setChecked(True)
        self.audio_copy_button.clicked.connect(self.handle_audio_copy)

        # audio copy button layout
        audio_copy_layout = QHBoxLayout()
        audio_copy_layout.addWidget(self.audio_copy_button)
        audio_copy_layout.addStretch(1)

        # enable audio format
        self.enable_audio_format = QCheckBox("Specifying Audio Format")
        self.enable_audio_format.setEnabled(False)
        self.enable_audio_format.clicked.connect(self.enable_change_audio_format)

        # audio format
        self.audio_format = QComboBox()
        self.audio_format.addItems(constants.SUPPORT_AUDIO_ENCODE_FORMAT.keys())
        self.audio_format.currentIndexChanged.connect(self.change_audio_format)
        self.audio_format.setEnabled(False)
        audio_format_label = QLabel("Audio Format:")
        audio_format_label.setBuddy(self.audio_format)

        # audio format layout
        audio_format_layout = QHBoxLayout()
        audio_format_layout.addWidget(self.enable_audio_format)
        audio_format_layout.addStretch(1)
        audio_format_layout.addWidget(audio_format_label)
        audio_format_layout.addWidget(self.audio_format)

        # enable audio compress
        self.enable_audio_compress = QCheckBox("Specifying Audio Bit Rate")
        self.enable_audio_compress.setEnabled(False)
        self.enable_audio_compress.clicked.connect(self.enable_change_audio_compress)

        # audio compress
        self.audio_compress = QLineEdit()
        self.audio_compress.setEnabled(False)
        self.audio_compress.setText("192")
        self.audio_compress.setValidator(QIntValidator(0, 500))
        self.audio_compress.textChanged.connect(self.update_command_line)
        audio_k_label = QLabel("k")
        audio_compress_label = QLabel("Audio Bit Rate:")
        audio_compress_label.setBuddy(self.audio_compress)

        # audio layout
        audio_compress_layout = QHBoxLayout()
        audio_compress_layout.addWidget(self.enable_audio_compress)
        audio_compress_layout.addStretch(6)
        audio_compress_layout.addWidget(audio_compress_label)
        audio_compress_layout.addWidget(self.audio_compress, 1)
        audio_compress_layout.addWidget(audio_k_label)

        # line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        # main layout
        main_layout = QVBoxLayout(result)
        main_layout.addLayout(audio_copy_layout)
        main_layout.addWidget(line)
        main_layout.addLayout(audio_format_layout)
        main_layout.addLayout(audio_compress_layout)
        main_layout.addStretch(1)

        return result

    @Slot()
    def handle_audio_copy(self):
        if self.audio_copy_button.isChecked():
            self.enable_audio_format.setEnabled(False)
            self.audio_format.setEnabled(False)
            self.enable_audio_compress.setEnabled(False)
            self.audio_compress.setEnabled(False)
        else:
            self.enable_audio_format.setEnabled(True)
            self.audio_format.setEnabled(True)
            self.enable_audio_compress.setEnabled(True)
            self.audio_compress.setEnabled(True)

        self.update_command_line()

    @Slot()
    def enable_change_audio_format(self):
        if self.enable_audio_format.isChecked():
            self.audio_format.setEnabled(True)
        else:
            self.audio_format.setEnabled(False)

        self.update_command_line()

    @Slot()
    def change_audio_format(self):
        if self.audio_format.currentText() == "FLAC":
            self.enable_audio_compress.setEnabled(False)
            self.audio_compress.setEnabled(False)
        else:
            self.enable_audio_compress.setEnabled(True)
            self.audio_compress.setEnabled(True)

        self.update_command_line()

    @Slot()
    def enable_change_audio_compress(self):
        if self.enable_audio_compress.isChecked():
            self.audio_compress.setEnabled(True)
        else:
            self.audio_compress.setEnabled(False)

        self.update_command_line()

    def create_file_format_config_groupbox(self):
        result = QGroupBox()

        self.file_format = QComboBox()
        self.file_format.addItems(constants.SUPPORT_FILE_FORMAT)
        self.file_format.currentIndexChanged.connect(self.change_output_format)
        file_format_label = QLabel("File Format:")
        file_format_label.setBuddy(self.file_format)

        format_selector_layout = QHBoxLayout()
        format_selector_layout.addWidget(file_format_label)
        format_selector_layout.addWidget(self.file_format)

        self.movflag = QCheckBox("Enable Fast Start (Only for mp4 format)")
        self.movflag.setEnabled(False)
        self.movflag.clicked.connect(self.enable_mov_flag)

        file_format_layout = QHBoxLayout()
        file_format_layout.addLayout(format_selector_layout)
        file_format_layout.addStretch(1)
        file_format_layout.addWidget(self.movflag)

        main_layout = QVBoxLayout(result)
        main_layout.addLayout(file_format_layout)
        main_layout.addStretch(1)

        return result

    @Slot()
    def change_output_format(self):
        if self.file_format.currentText() == "mp4":
            self.movflag.setEnabled(True)
        else:
            self.movflag.setEnabled(False)

        self.update_command_line()
        self.output_label.setText(f"$OUTPUT$.{self.file_format.currentText()}")

    @Slot()
    def enable_mov_flag(self):
        self.update_command_line()

    def create_output_config_groupbox(self):
        result = QGroupBox()

        # output directory
        output_directory_label = QLabel("Output Directory:")
        self.output_directory = QLineEdit()
        self.output_directory.setReadOnly(True)
        output_directory_button = QPushButton("Choose Directory")
        output_directory_button.clicked.connect(self.choose_output_directory)

        # output directory layout
        output_directory_layout = QHBoxLayout()
        output_directory_layout.addWidget(output_directory_label)
        output_directory_layout.addWidget(self.output_directory)
        output_directory_layout.addWidget(output_directory_button)

        # enable rename
        self.enable_rename = QCheckBox("Rename Output File")
        self.enable_rename.clicked.connect(self.enable_rename_file)

        # rename mode
        self.rename_mode = QComboBox()
        self.rename_mode.addItem("Add Prefix")
        self.rename_mode.addItem("Add Suffix")
        self.rename_mode.addItem("Rename with Indexed Number")
        self.rename_mode.setEnabled(False)
        self.rename_mode.currentIndexChanged.connect(self.change_rename_mode)
        rename_mode_label = QLabel("Rename Mode:")
        rename_mode_label.setBuddy(self.rename_mode)

        # rename
        self.rename = QLineEdit()
        self.rename.setEnabled(False)
        self.rename_prefix_label = QLabel("-$NAME$")
        self.rename_suffix_label = QLabel("$NAME$-")
        self.rename_suffix_label.setVisible(False)
        self.rename_index_label = QLabel("-XX")
        self.rename_index_label.setVisible(False)
        rename_file_format_label = QLabel(f".{self.file_format.currentText()}")

        # rename layout
        rename_layout = QHBoxLayout()
        rename_layout.addWidget(rename_mode_label)
        rename_layout.addWidget(self.rename_mode)
        rename_layout.addStretch(1)
        rename_layout.addWidget(self.rename_suffix_label)
        rename_layout.addWidget(self.rename)
        rename_layout.addWidget(self.rename_prefix_label)
        rename_layout.addWidget(self.rename_index_label)
        rename_layout.addWidget(rename_file_format_label)

        # line
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)

        # main layout
        main_layout = QVBoxLayout(result)
        main_layout.addLayout(output_directory_layout)
        main_layout.addWidget(line)
        main_layout.addWidget(self.enable_rename)
        main_layout.addLayout(rename_layout)
        main_layout.addStretch(1)

        return result

    @Slot()
    def choose_output_directory(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Select Output Directory")

        if folder_path:
            self.output_directory.setText(folder_path)

    @Slot()
    def enable_rename_file(self):
        if self.enable_rename.isChecked():
            self.rename_mode.setEnabled(True)
            self.rename.setEnabled(True)
        else:
            self.rename_mode.setEnabled(False)
            self.rename.setEnabled(False)

    @Slot()
    def change_rename_mode(self):
        if self.rename_mode.currentText() == "Add Prefix":
            self.rename_prefix_label.setVisible(True)
            self.rename_suffix_label.setVisible(False)
            self.rename_index_label.setVisible(False)
        elif self.rename_mode.currentText() == "Add Suffix":
            self.rename_prefix_label.setVisible(False)
            self.rename_suffix_label.setVisible(True)
            self.rename_index_label.setVisible(False)
        else:
            self.rename_prefix_label.setVisible(False)
            self.rename_suffix_label.setVisible(False)
            self.rename_index_label.setVisible(True)

    def create_command_line_groupbox(self):
        """Create command line Groupbox"""
        result = QGroupBox("Command")

        # create labels
        prefix = QLabel("ffmpeg -i $INPUT$")
        self.output_label = QLabel(f"$OUTPUT$.{self.file_format.currentText()}")

        # create a command text editor
        self.command_editor = QLineEdit()

        # create reset button
        reset_button = QPushButton("Reset")
        reset_button.clicked.connect(self.reset_command_line)
        reset_button.setDefault(True)

        main_layout = QHBoxLayout(result)
        main_layout.addWidget(prefix)
        main_layout.addWidget(self.command_editor, 8)
        main_layout.addWidget(self.output_label)
        main_layout.addStretch(1)
        main_layout.addWidget(reset_button)

        return result

    @Slot()
    def update_command_line(self):
        cmd = ""
        if self.enable_encode_format.isChecked():
            cmd += f" -c:v {constants.SUPPORT_VIDEO_ENCODE_FORMAT[self.encode_format.currentText()]}"

        if self.video_quality.isEnabled():
            cmd += f" -crf {self.video_quality.text()}"

        cmd += f" -preset {self.encode_speed.currentText()}"

        if self.enable_video_framerate.isChecked():
            cmd += f" -r {self.video_framerate.text()}"

        if self.enable_video_scale.isChecked():
            cmd += f" -vf scale=\"{self.video_scale.text()}\""

        if self.movflag.isEnabled() and self.movflag.isChecked():
            cmd += " -movflags faststart"

        if self.audio_copy_button.isChecked():
            cmd += " -c:a copy"
        else:
            if self.enable_audio_format.isChecked():
                cmd += f" -c:a {constants.SUPPORT_AUDIO_ENCODE_FORMAT[self.audio_format.currentText()]}"
            if self.audio_compress.isEnabled() and self.enable_audio_compress.isChecked():
                cmd += f" -b:a {self.audio_compress.text()}k"

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

        # create job list
        self.processes = []
        for i in range(self.jobs):
            input_file = self.file_model.item(i, 0).text()
            output_file = get_output_file_path(enable_rename=self.enable_rename.isChecked(),
                                                    rename_mode=self.rename_mode.currentText(),
                                                    rename_content=self.rename.text(),
                                                    index= i,
                                                    format=self.file_format.currentText(),
                                                    original_file_path=input_file,
                                                    output_directory=self.output_directory.text())
            cmd = f"-i {input_file} {self.command_editor.text()} {output_file}"
            self.processes.append(cmd)

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