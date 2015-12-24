import sys
import os
import hashlib
import re

from PyQt5.QtCore import Qt, QTimer, QUrl
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QWidget, QStatusBar, QGridLayout, QGroupBox, QMainWindow,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QToolButton,
    QProgressBar, QButtonGroup, QRadioButton)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

from cddagl.config import (
    get_config_value, set_config_value, new_version, get_build_from_sha256)

READ_BUFFER_SIZE = 16384

BASE_URLS = {
    'Tiles': {
        'Windows x64': 'http://dev.narc.ro/cataclysm/jenkins-latest/Windows_x64/Tiles/',
        'Windows x86': 'http://dev.narc.ro/cataclysm/jenkins-latest/Windows/Tiles/'
    },
    'Console': {
        'Windows x64': 'http://dev.narc.ro/cataclysm/jenkins-latest/Windows_x64/Curses/',
        'Windows x86': 'http://dev.narc.ro/cataclysm/jenkins-latest/Windows/Curses/'
    }
}

def clean_qt_path(path):
    return path.replace('/', '\\')

def is_64_windows():
    return 'PROGRAMFILES(X86)' in os.environ

class MainWindow(QMainWindow):
    def __init__(self, title):
        super(MainWindow, self).__init__()

        self.setMinimumSize(400, 0)
        
        self.create_status_bar()
        self.create_central_widget()

        self.setWindowTitle(title)

    def create_status_bar(self):
        status_bar = self.statusBar()

        status_bar.showMessage('Ready')

    def create_central_widget(self):
        central_widget = CentralWidget()
        self.setCentralWidget(central_widget)


class CentralWidget(QWidget):
    def __init__(self):
        super(CentralWidget, self).__init__()

        game_dir_group_box = GameDirGroupBox()
        self.game_dir_group_box = game_dir_group_box

        update_group_box = UpdateGroupBox()
        self.update_group_box = update_group_box

        layout = QVBoxLayout()
        layout.addWidget(game_dir_group_box)
        layout.addWidget(update_group_box)
        self.setLayout(layout)

    def get_main_window(self):
        return self.parentWidget()


class GameDirGroupBox(QGroupBox):
    def __init__(self):
        super(GameDirGroupBox, self).__init__()

        self.shown = False

        layout = QGridLayout()

        dir_label = QLabel()
        dir_label.setText('Directory:')
        layout.addWidget(dir_label, 0, 0, Qt.AlignRight)
        self.dir_label = dir_label

        dir_edit = QLineEdit()
        dir_edit.editingFinished.connect(self.game_directory_changed)
        layout.addWidget(dir_edit, 0, 1)
        self.dir_edit = dir_edit

        dir_change_button = QToolButton()
        dir_change_button.setText('...')
        dir_change_button.clicked.connect(self.set_game_directory)
        layout.addWidget(dir_change_button, 0, 2)
        self.dir_change_button = dir_change_button

        version_label = QLabel()
        version_label.setText('Version:')
        layout.addWidget(version_label, 1, 0, Qt.AlignRight)
        self.version_label = version_label

        version_value_label = QLabel()
        layout.addWidget(version_value_label, 1, 1)
        self.version_value_label = version_value_label

        build_label = QLabel()
        build_label.setText('Build:')
        layout.addWidget(build_label, 2, 0, Qt.AlignRight)
        self.build_label = build_label

        build_value_label = QLabel()
        build_value_label.setText('Unknown')
        layout.addWidget(build_value_label, 2, 1)
        self.build_value_label = build_value_label

        self.setTitle('Game directory')
        self.setLayout(layout)

    def showEvent(self, event):
        if not self.shown:
            game_directory = get_config_value('game_directory')
            if game_directory is None:
                cddagl_path = os.path.dirname(os.path.realpath(sys.argv[0]))
                default_dir = os.path.join(cddagl_path, 'cdda')
                game_directory = default_dir

            self.last_game_directory = None
            self.dir_edit.setText(game_directory)
            self.game_directory_changed()

        self.shown = True

    def get_main_window(self):
        return self.parentWidget().get_main_window()

    def set_game_directory(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self,
                "QFileDialog.getExistingDirectory()",
                self.dir_edit.text(), options=options)
        if directory:
            self.dir_edit.setText(clean_qt_path(directory))
            self.game_directory_changed()

    def game_directory_changed(self):
        directory = self.dir_edit.text()
        
        if not os.path.isdir(directory):
            self.version_value_label.setText('Not a valid directory')
        else:
            # Find the executable

            console_exe = os.path.join(directory, 'cataclysm.exe')
            tiles_exe = os.path.join(directory, 'cataclysm-tiles.exe')

            exe_path = None
            version_type = None
            if os.path.isfile(console_exe):
                version_type = 'console'
                exe_path = console_exe
            elif os.path.isfile(tiles_exe):
                version_type = 'tiles'
                exe_path = tiles_exe

            if version_type is None:
                self.version_value_label.setText('Not a CDDA directory')
            else:
                self.exe_path = exe_path
                self.version_type = version_type
                if self.last_game_directory != directory:
                    self.update_version()

        self.last_game_directory = directory
        set_config_value('game_directory', directory)

    def update_version(self):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        reading_label = QLabel()
        reading_label.setText('Reading: {0}'.format(self.exe_path))
        status_bar.addWidget(reading_label, 100)
        self.reading_label = reading_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.reading_progress_bar = progress_bar

        timer = QTimer(self)
        self.exe_reading_timer = timer

        exe_size = os.path.getsize(self.exe_path)

        progress_bar.setRange(0, exe_size)
        self.exe_total_read = 0

        self.exe_sha256 = hashlib.sha256()
        self.last_bytes = None
        self.game_version = 'Unknown'
        self.opened_exe = open(self.exe_path, 'rb')

        def timeout():
            bytes = self.opened_exe.read(READ_BUFFER_SIZE)
            if len(bytes) == 0:
                self.opened_exe.close()
                self.exe_reading_timer.stop()
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                self.version_value_label.setText(
                    '{version} ({type})'.format(version=self.game_version,
                    type=self.version_type))

                status_bar.removeWidget(self.reading_label)
                status_bar.removeWidget(self.reading_progress_bar)
                status_bar.showMessage('Ready')

                sha256 = self.exe_sha256.hexdigest()

                new_version(self.game_version, sha256)

                build = get_build_from_sha256(sha256)

                if build is not None:
                    self.build_value_label.setText(build)

            else:
                last_frame = bytes
                if self.last_bytes is not None:
                    last_frame = self.last_bytes + last_frame

                match = re.search(
                    b'(?P<version>[01]\\.[A-F](-\\d+-g[0-9a-f]+)?)\\x00',
                    last_frame)
                if match is not None:
                    game_version = match.group('version').decode('ascii')
                    self.game_version = game_version
                    self.version_value_label.setText(
                        '{version} ({type})'.format(version=self.game_version,
                            type=self.version_type))

                self.exe_total_read += len(bytes)
                self.reading_progress_bar.setValue(self.exe_total_read)
                self.exe_sha256.update(bytes)
                self.last_bytes = bytes

        timer.timeout.connect(timeout)
        timer.start(0)

        '''from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
        pyqtRemoveInputHook()
        import pdb; pdb.set_trace()
        pyqtRestoreInputHook()'''


class UpdateGroupBox(QGroupBox):
    def __init__(self):
        super(UpdateGroupBox, self).__init__()

        self.shown = False

        self.qnam = QNetworkAccessManager()
        self.http_reply = None

        layout = QGridLayout()

        graphics_label = QLabel()
        graphics_label.setText('Graphics:')
        layout.addWidget(graphics_label, 0, 0, Qt.AlignRight)
        self.graphics_label = graphics_label

        graphics_button_group = QButtonGroup()
        self.graphics_button_group = graphics_button_group

        tiles_radio_button = QRadioButton()
        tiles_radio_button.setText('Tiles')
        layout.addWidget(tiles_radio_button, 0, 1)
        self.tiles_radio_button = tiles_radio_button
        graphics_button_group.addButton(tiles_radio_button)

        console_radio_button = QRadioButton()
        console_radio_button.setText('Console')
        layout.addWidget(console_radio_button, 0, 2)
        self.console_radio_button = console_radio_button
        graphics_button_group.addButton(console_radio_button)

        graphics_button_group.buttonClicked.connect(self.graphics_clicked)

        platform_label = QLabel()
        platform_label.setText('Platform:')
        layout.addWidget(platform_label, 1, 0, Qt.AlignRight)
        self.platform_label = platform_label

        platform_button_group = QButtonGroup()
        self.platform_button_group = platform_button_group

        x64_radio_button = QRadioButton()
        x64_radio_button.setText('Windows x64')
        layout.addWidget(x64_radio_button, 1, 1)
        self.x64_radio_button = x64_radio_button
        platform_button_group.addButton(x64_radio_button)

        platform_button_group.buttonClicked.connect(self.platform_clicked)

        if not is_64_windows():
            x64_radio_button.setEnabled(False)

        x86_radio_button = QRadioButton()
        x86_radio_button.setText('Windows x86')
        layout.addWidget(x86_radio_button, 1, 2)
        self.x86_radio_button = x86_radio_button
        platform_button_group.addButton(x86_radio_button)

        latest_build_label = QLabel()
        latest_build_label.setText('Latest build:')
        layout.addWidget(latest_build_label, 2, 0, Qt.AlignRight)
        self.latest_build_label = latest_build_label

        latest_build_value_label = QLabel()
        latest_build_value_label.setText('Unknown')
        layout.addWidget(latest_build_value_label, 2, 1, 1, 2)
        self.latest_build_value_label = latest_build_value_label

        self.setTitle('Update/Installation')
        self.setLayout(layout)

    def showEvent(self, event):
        if not self.shown:
            graphics = get_config_value('graphics')
            if graphics is None:
                graphics = 'Tiles'

            platform = get_config_value('platform')
            if platform is None:
                if is_64_windows():
                    platform = 'Windows x64'
                else:
                    platform = 'Windows x86'

            if graphics == 'Tiles':
                self.tiles_radio_button.setChecked(True)
            elif graphics == 'Console':
                self.console_radio_button.setChecked(True)

            if platform == 'Windows x64':
                self.x64_radio_button.setChecked(True)
            elif platform == 'Windows x86':
                self.x86_radio_button.setChecked(True)

            self.start_lb_request(BASE_URLS[graphics][platform])

        self.shown = True

    def get_main_window(self):
        return self.parentWidget().get_main_window()

    def start_lb_request(self, url):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        fetching_label = QLabel()
        fetching_label.setText('Fetching: {0}'.format(url))
        status_bar.addWidget(fetching_label, 100)
        self.fetching_label = fetching_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.fetching_progress_bar = progress_bar

        progress_bar.setMinimum(0)

        self.http_reply = self.qnam.get(QNetworkRequest(QUrl(url)))
        self.http_reply.finished.connect(self.lb_http_finished)
        self.http_reply.readyRead.connect(self.lb_http_ready_read)
        self.http_reply.downloadProgress.connect(self.lb_dl_progress)

    def lb_http_finished(self):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.removeWidget(self.fetching_label)
        status_bar.removeWidget(self.fetching_progress_bar)

    def lb_http_ready_read(self):
        print('ready read')
        self.http_reply.readAll()
        #print(self.http_reply.readAll())

    def lb_dl_progress(self, bytes_read, total_bytes):
        print(bytes_read, total_bytes)
        self.fetching_progress_bar.setMaximum(total_bytes)
        self.fetching_progress_bar.setValue(bytes_read)

    def graphics_clicked(self, button):
        set_config_value('graphics', button.text())

    def platform_clicked(self, button):
        set_config_value('platform', button.text())

def start_ui():
    app = QApplication(sys.argv)
    mainWin = MainWindow('CDDA Game Launcher')
    mainWin.show()
    sys.exit(app.exec_())