import sys
import os
import hashlib
import re
import subprocess
import random
import shutil
import zipfile
import json

from datetime import datetime
import arrow

from io import BytesIO

import html5lib
from urllib.parse import urljoin

from PyQt5.QtCore import Qt, QTimer, QUrl, QFileInfo
from PyQt5.QtGui import QIcon, QPalette
from PyQt5.QtWidgets import (
    QApplication, QWidget, QStatusBar, QGridLayout, QGroupBox, QMainWindow,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QToolButton,
    QProgressBar, QButtonGroup, QRadioButton, QComboBox, QAction, QDialog,
    QTextBrowser, QTabWidget, QCheckBox)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

from cddagl.config import (
    get_config_value, set_config_value, new_version, get_build_from_sha256,
    new_build)

from .__version__ import version

READ_BUFFER_SIZE = 16384

BASE_URLS = {
    'Tiles': {
        'Windows x64': ('http://dev.narc.ro/cataclysm/jenkins-latest/'
            'Windows_x64/Tiles/'),
        'Windows x86': ('http://dev.narc.ro/cataclysm/jenkins-latest/'
            'Windows/Tiles/')
    },
    'Console': {
        'Windows x64': ('http://dev.narc.ro/cataclysm/jenkins-latest/'
            'Windows_x64/Curses/'),
        'Windows x86': ('http://dev.narc.ro/cataclysm/jenkins-latest/'
            'Windows/Curses/')
    }
}

def clean_qt_path(path):
    return path.replace('/', '\\')

def is_64_windows():
    return 'PROGRAMFILES(X86)' in os.environ

def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


class MainWindow(QMainWindow):
    def __init__(self, title):
        super(MainWindow, self).__init__()

        self.setMinimumSize(400, 0)
        width = int(get_config_value('window.width', -1))
        height = int(get_config_value('window.height', -1))
        if width != -1 and height != -1:
            self.resize(width, height)
        
        self.create_status_bar()
        self.create_central_widget()
        self.create_menu()

        self.about_dialog = None

        self.setWindowTitle(title)

    def create_status_bar(self):
        status_bar = self.statusBar()
        status_bar.busy = 0

        status_bar.showMessage('Ready')

    def create_central_widget(self):
        central_widget = CentralWidget()
        self.setCentralWidget(central_widget)
        self.central_widget = central_widget

    def create_menu(self):
        about_action = QAction('&About', self, triggered=self.show_about_dialog)
        self.about_action = about_action
        self.menuBar().addAction(about_action)

    def show_about_dialog(self):
        if self.about_dialog is None:
            about_dialog = AboutDialog(self, Qt.WindowTitleHint |
                Qt.WindowCloseButtonHint)
            self.about_dialog = about_dialog
        
        self.about_dialog.exec()

    def resizeEvent(self, event):
        set_config_value('window.width', event.size().width())
        set_config_value('window.height', event.size().height())

    def closeEvent(self, event):
        update_group_box = self.central_widget.main_tab.update_group_box

        if update_group_box.updating:
            update_group_box.close_after_update = True
            update_group_box.update_game()

            if not update_group_box.updating:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


class CentralWidget(QTabWidget):
    def __init__(self):
        super(CentralWidget, self).__init__()

        self.create_main_tab()
        self.create_settings_tab()

    def create_main_tab(self):
        main_tab = MainTab()
        self.addTab(main_tab, 'Main')
        self.main_tab = main_tab

    def create_settings_tab(self):
        settings_tab = SettingsTab()
        self.addTab(settings_tab, 'Settings')
        self.settings_tab = settings_tab


class MainTab(QWidget):
    def __init__(self):
        super(MainTab, self).__init__()

        game_dir_group_box = GameDirGroupBox()
        self.game_dir_group_box = game_dir_group_box

        update_group_box = UpdateGroupBox()
        self.update_group_box = update_group_box

        layout = QVBoxLayout()
        layout.addWidget(game_dir_group_box)
        layout.addWidget(update_group_box)
        self.setLayout(layout)

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()


class SettingsTab(QWidget):
    def __init__(self):
        super(SettingsTab, self).__init__()

        launcher_settings_group_box = LauncherSettingsGroupBox()
        self.launcher_settings_group_box = launcher_settings_group_box

        update_settings_group_box = UpdateSettingsGroupBox()
        self.update_settings_group_box = update_settings_group_box

        layout = QVBoxLayout()
        layout.addWidget(launcher_settings_group_box)
        layout.addWidget(update_settings_group_box)
        self.setLayout(layout)

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

class GameDirGroupBox(QGroupBox):
    def __init__(self):
        super(GameDirGroupBox, self).__init__()

        self.shown = False
        self.restored_previous = False
        self.exe_path = None

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

        version_value_label = QLineEdit()
        version_value_label.setReadOnly(True)
        layout.addWidget(version_value_label, 1, 1)
        self.version_value_label = version_value_label

        build_label = QLabel()
        build_label.setText('Build:')
        layout.addWidget(build_label, 2, 0, Qt.AlignRight)
        self.build_label = build_label

        build_value_label = QLineEdit()
        build_value_label.setReadOnly(True)
        build_value_label.setText('Unknown')
        layout.addWidget(build_value_label, 2, 1)
        self.build_value_label = build_value_label

        launch_game_button = QPushButton()
        launch_game_button.setText('Launch game')
        launch_game_button.setEnabled(False)
        launch_game_button.setStyleSheet("font-size: 20px;")
        launch_game_button.clicked.connect(self.launch_game)
        layout.addWidget(launch_game_button, 3, 0, 1, 3)
        self.launch_game_button = launch_game_button

        restore_button = QPushButton()
        restore_button.setText('Restore previous version')
        restore_button.setEnabled(False)
        restore_button.clicked.connect(self.restore_previous)
        layout.addWidget(restore_button, 4, 0, 1, 3)
        self.restore_button = restore_button

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

    def disable_controls(self):
        self.dir_edit.setEnabled(False)
        self.dir_change_button.setEnabled(False)

        self.previous_lgb_enabled = self.launch_game_button.isEnabled()
        self.launch_game_button.setEnabled(False)
        self.previous_rb_enabled = self.restore_button.isEnabled()
        self.restore_button.setEnabled(False)

    def enable_controls(self):
        self.dir_edit.setEnabled(True)
        self.dir_change_button.setEnabled(True)
        self.launch_game_button.setEnabled(self.previous_lgb_enabled)
        self.restore_button.setEnabled(self.previous_rb_enabled)

    def restore_previous(self):
        self.disable_controls()

        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box
        update_group_box.disable_controls(True)

        try:
            game_dir = self.dir_edit.text()
            previous_version_dir = os.path.join(game_dir, 'previous_version')

            if os.path.isdir(previous_version_dir) and os.path.isdir(game_dir):

                temp_dir = os.path.join(os.environ['TEMP'],
                    'CDDA Game Launcher')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)

                temp_move_dir = os.path.join(temp_dir, 'moved')
                while os.path.exists(temp_move_dir):
                    temp_move_dir = os.path.join(temp_dir, 'moved-{0}'.format(
                        '%08x' % random.randrange(16**8)))
                os.makedirs(temp_move_dir)

                excluded_dirs = set(['previous_version'])
                if get_config_value('prevent_save_move', False):
                    excluded_dirs.add('save')
                for entry in os.listdir(game_dir):
                    if entry not in excluded_dirs:
                        entry_path = os.path.join(game_dir, entry)
                        shutil.move(entry_path, temp_move_dir)

                excluded_dirs = set()
                if get_config_value('prevent_save_move', False):
                    excluded_dirs.add('save')
                for entry in os.listdir(previous_version_dir):
                    if entry not in excluded_dirs:
                        entry_path = os.path.join(previous_version_dir, entry)
                        shutil.move(entry_path, game_dir)

                for entry in os.listdir(temp_move_dir):
                    entry_path = os.path.join(temp_move_dir, entry)
                    shutil.move(entry_path, previous_version_dir)

                shutil.rmtree(temp_move_dir)
        except OSError as e:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(str(e))

        self.last_game_directory = None
        self.restored_previous = True
        self.enable_controls()
        update_group_box.enable_controls()
        self.game_directory_changed()

    def launch_game(self):
        self.get_main_window().setWindowState(Qt.WindowMinimized)
        exe_dir = os.path.dirname(self.exe_path)

        params = get_config_value('command.params', '').strip()
        if params != '':
            params = ' ' + params

        command = 'start /D "{app_path}" "" "{exe_path}"{params}'.format(
            app_path=exe_dir, exe_path=self.exe_path, params=params)
        subprocess.call(command, shell=True)

        self.get_main_window().close()

    def get_main_tab(self):
        return self.parentWidget()

    def get_main_window(self):
        return self.get_main_tab().get_main_window()

    def set_game_directory(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self,
                'Game directory', self.dir_edit.text(), options=options)
        if directory:
            self.dir_edit.setText(clean_qt_path(directory))
            self.game_directory_changed()

    def game_directory_changed(self):
        directory = self.dir_edit.text()
        self.exe_path = None
        
        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box

        if not os.path.isdir(directory):
            self.version_value_label.setText('Not a valid directory')
            self.build_value_label.setText('Unknown')
        else:
            # Check for previous version
            previous_version_dir = os.path.join(directory, 'previous_version')
            self.restore_button.setEnabled(os.path.isdir(previous_version_dir))

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
                self.build_value_label.setText('Unknown')
            else:
                self.exe_path = exe_path
                self.version_type = version_type
                if self.last_game_directory != directory:
                    self.update_version()

        if self.exe_path is None:
            self.launch_game_button.setEnabled(False)
            update_group_box.update_button.setText('Install game')
            self.restored_previous = False
        else:
            self.launch_game_button.setEnabled(True)
            update_group_box.update_button.setText('Update game')

        self.last_game_directory = directory
        set_config_value('game_directory', directory)

    def update_version(self):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        status_bar.busy += 1

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
        self.game_version = ''
        self.opened_exe = open(self.exe_path, 'rb')

        def timeout():
            bytes = self.opened_exe.read(READ_BUFFER_SIZE)
            if len(bytes) == 0:
                self.opened_exe.close()
                self.exe_reading_timer.stop()
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                if self.game_version == '':
                    self.game_version = 'Unknown'

                self.version_value_label.setText(
                    '{version} ({type})'.format(version=self.game_version,
                    type=self.version_type))

                status_bar.removeWidget(self.reading_label)
                status_bar.removeWidget(self.reading_progress_bar)

                status_bar.busy -= 1
                if status_bar.busy == 0:
                    if self.restored_previous:
                        self.restored_previous = False
                        status_bar.showMessage('Previous version restored')
                    else:
                        status_bar.showMessage('Ready')

                sha256 = self.exe_sha256.hexdigest()

                new_version(self.game_version, sha256)

                build = get_build_from_sha256(sha256)

                if build is not None:
                    build_date = arrow.get(build['released_on'], 'UTC')
                    human_delta = build_date.humanize(arrow.utcnow())
                    self.build_value_label.setText('{0} ({1})'.format(
                        build['build'], human_delta))
                else:
                    self.build_value_label.setText('Unknown')

            else:
                last_frame = bytes
                if self.last_bytes is not None:
                    last_frame = self.last_bytes + last_frame

                match = re.search(
                    b'(?P<version>[01]\\.[A-F](-\\d+-g[0-9a-f]+)?)\\x00',
                    last_frame)
                if match is not None:
                    game_version = match.group('version').decode('ascii')
                    if len(game_version) > len(self.game_version):
                        self.game_version = game_version

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

    def analyse_new_build(self, build):
        game_dir = self.dir_edit.text()

        self.previous_exe_path = self.exe_path
        self.exe_path = None

        # Check for previous version
        previous_version_dir = os.path.join(game_dir, 'previous_version')
        self.previous_rb_enabled = os.path.isdir(previous_version_dir)

        console_exe = os.path.join(game_dir, 'cataclysm.exe')
        tiles_exe = os.path.join(game_dir, 'cataclysm-tiles.exe')

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
            self.build_value_label.setText('Unknown')
        else:
            self.exe_path = exe_path
            self.version_type = version_type
            self.build_number = build['number']
            self.build_date = build['date']

            main_window = self.get_main_window()

            status_bar = main_window.statusBar()
            status_bar.clearMessage()

            status_bar.busy += 1

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
            self.game_version = ''
            self.opened_exe = open(self.exe_path, 'rb')

            def timeout():
                bytes = self.opened_exe.read(READ_BUFFER_SIZE)
                if len(bytes) == 0:
                    self.opened_exe.close()
                    self.exe_reading_timer.stop()
                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    if self.game_version == '':
                        self.game_version = 'Unknown'
                    self.version_value_label.setText(
                        '{version} ({type})'.format(version=self.game_version,
                        type=self.version_type))

                    build_date = arrow.get(self.build_date, 'UTC')
                    human_delta = build_date.humanize(arrow.utcnow())
                    self.build_value_label.setText('{0} ({1})'.format(
                        self.build_number, human_delta))

                    status_bar.removeWidget(self.reading_label)
                    status_bar.removeWidget(self.reading_progress_bar)

                    status_bar.busy -= 1

                    sha256 = self.exe_sha256.hexdigest()

                    new_build(self.game_version, sha256, self.build_number,
                        self.build_date)

                    main_tab = self.get_main_tab()
                    update_group_box = main_tab.update_group_box

                    update_group_box.post_extraction()

                else:
                    last_frame = bytes
                    if self.last_bytes is not None:
                        last_frame = self.last_bytes + last_frame

                    match = re.search(
                        b'(?P<version>[01]\\.[A-F](-\\d+-g[0-9a-f]+)?)\\x00',
                        last_frame)
                    if match is not None:
                        game_version = match.group('version').decode('ascii')
                        if len(game_version) > len(self.game_version):
                            self.game_version = game_version

                    self.exe_total_read += len(bytes)
                    self.reading_progress_bar.setValue(self.exe_total_read)
                    self.exe_sha256.update(bytes)
                    self.last_bytes = bytes

            timer.timeout.connect(timeout)
            timer.start(0)

        if self.exe_path is None:
            self.previous_lgb_enabled = False
        else:
            self.previous_lgb_enabled = True


class UpdateGroupBox(QGroupBox):
    def __init__(self):
        super(UpdateGroupBox, self).__init__()

        self.shown = False
        self.updating = False
        self.close_after_update = False

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

        available_builds_label = QLabel()
        available_builds_label.setText('Available builds:')
        layout.addWidget(available_builds_label, 2, 0, Qt.AlignRight)
        self.available_builds_label = available_builds_label

        builds_combo = QComboBox()
        builds_combo.setEnabled(False)
        builds_combo.addItem('Unknown')
        layout.addWidget(builds_combo, 2, 1, 1, 2)
        self.builds_combo = builds_combo

        refresh_builds_button = QToolButton()
        refresh_builds_button.setText('Refresh')
        refresh_builds_button.clicked.connect(self.refresh_builds)
        layout.addWidget(refresh_builds_button, 2, 3)
        self.refresh_builds_button = refresh_builds_button

        update_button = QPushButton()
        update_button.setText('Update game')
        update_button.setEnabled(False)
        update_button.setStyleSheet('font-size: 20px;')
        update_button.clicked.connect(self.update_game)
        layout.addWidget(update_button, 3, 0, 1, 4)
        self.update_button = update_button

        layout.setColumnStretch(1, 100)
        layout.setColumnStretch(2, 100)

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

            self.lb_html = BytesIO()
            self.start_lb_request(BASE_URLS[graphics][platform])

        self.shown = True

    def update_game(self):
        if not self.updating:
            self.updating = True
            self.download_aborted = False
            self.backing_up_game = False
            self.extracting_new_build = False
            self.analysing_new_build = False
            self.in_post_extraction = False

            self.selected_build = self.builds[self.builds_combo.currentIndex()]

            main_tab = self.get_main_tab()
            game_dir_group_box = main_tab.game_dir_group_box

            game_dir_group_box.disable_controls()
            self.disable_controls()

            game_dir = game_dir_group_box.dir_edit.text()

            try:
                if not os.path.exists(game_dir):
                    os.makedirs(game_dir)
                elif os.path.isfile(game_dir):
                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    status_bar.showMessage('Cannot install game on a file')

                    self.finish_updating()
                    return

                temp_dir = os.path.join(os.environ['TEMP'],
                    'CDDA Game Launcher')
                if not os.path.exists(temp_dir):
                    os.makedirs(temp_dir)
                
                download_dir = os.path.join(temp_dir, 'newbuild')
                while os.path.exists(download_dir):
                    download_dir = os.path.join(temp_dir, 'newbuild-{0}'.format(
                        '%08x' % random.randrange(16**8)))
                os.makedirs(download_dir)

                download_url = self.selected_build['url']
                
                url = QUrl(download_url)
                file_info = QFileInfo(url.path())
                file_name = file_info.fileName()

                self.downloaded_file = os.path.join(download_dir, file_name)
                self.downloading_file = open(self.downloaded_file, 'wb')

                self.download_game_update(download_url)

            except OSError as e:
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(str(e))

                self.finish_updating()
        else:
            main_tab = self.get_main_tab()
            game_dir_group_box = main_tab.game_dir_group_box

            # Are we downloading the file?
            if self.download_http_reply.isRunning():
                self.download_aborted = True
                self.download_http_reply.abort()

                main_window = self.get_main_window()

                status_bar = main_window.statusBar()

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Update cancelled')
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Installation cancelled')
            elif self.backing_up_game:
                self.backup_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.removeWidget(self.backup_label)
                status_bar.removeWidget(self.backup_progress_bar)

                status_bar.busy -= 1

                self.restore_backup()

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Update cancelled')
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Installation cancelled')

            elif self.extracting_new_build:
                self.extracting_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.removeWidget(self.extracting_label)
                status_bar.removeWidget(self.extracting_progress_bar)

                status_bar.busy -= 1

                self.extracting_zipfile.close()

                download_dir = os.path.dirname(self.downloaded_file)
                shutil.rmtree(download_dir)

                path = self.clean_game_dir()
                self.restore_backup()
                self.restore_previous_content(path)

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Update cancelled')
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Installation cancelled')
            elif self.analysing_new_build:
                game_dir_group_box.opened_exe.close()
                game_dir_group_box.exe_reading_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.removeWidget(game_dir_group_box.reading_label)
                status_bar.removeWidget(game_dir_group_box.reading_progress_bar)

                status_bar.busy -= 1

                path = self.clean_game_dir()
                self.restore_backup()
                self.restore_previous_content(path)

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Update cancelled')
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Installation cancelled')
            elif self.in_post_extraction:
                self.in_post_extraction = False

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()
                status_bar.clearMessage()

                path = self.clean_game_dir()
                self.restore_backup()
                self.restore_previous_content(path)

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Update cancelled')
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage('Installation cancelled')

            self.finish_updating()

    def clean_game_dir(self):
        game_dir = self.game_dir
        dir_list = os.listdir(game_dir)
        if len(dir_list) == 0 or (
            len(dir_list) == 1 and dir_list[0] == 'previous_version'):
            return None

        temp_dir = os.path.join(os.environ['TEMP'], 'CDDA Game Launcher')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        temp_move_dir = os.path.join(temp_dir, 'moved')
        while os.path.exists(temp_move_dir):
            temp_move_dir = os.path.join(temp_dir, 'moved-{0}'.format(
                '%08x' % random.randrange(16**8)))
        os.makedirs(temp_move_dir)

        excluded_dirs = set(['previous_version'])
        if get_config_value('prevent_save_move', False):
            excluded_dirs.add('save')
        for entry in dir_list:
            if entry not in excluded_dirs:
                entry_path = os.path.join(game_dir, entry)
                shutil.move(entry_path, temp_move_dir)

        return temp_move_dir

    def restore_previous_content(self, path):
        if path is None:
            return

        game_dir = self.game_dir
        previous_version_dir = os.path.join(game_dir, 'previous_version')
        if not os.path.exists(previous_version_dir):
            os.makedirs(previous_version_dir)

        for entry in os.listdir(path):
            entry_path = os.path.join(path, entry)
            shutil.move(entry_path, previous_version_dir)

    def restore_backup(self):
        game_dir = self.game_dir
        previous_version_dir = os.path.join(game_dir, 'previous_version')

        if os.path.isdir(previous_version_dir) and os.path.isdir(game_dir):

            for entry in os.listdir(previous_version_dir):
                if (entry == 'save' and
                    get_config_value('prevent_save_move', False)):
                    continue
                entry_path = os.path.join(previous_version_dir, entry)
                shutil.move(entry_path, game_dir)

            shutil.rmtree(previous_version_dir)

    def get_main_tab(self):
        return self.parentWidget()

    def get_main_window(self):
        return self.get_main_tab().get_main_window()

    def disable_controls(self, update_button=False):
        self.tiles_radio_button.setEnabled(False)
        self.console_radio_button.setEnabled(False)
        self.x64_radio_button.setEnabled(False)
        self.x86_radio_button.setEnabled(False)

        self.previous_bc_enabled = self.builds_combo.isEnabled()
        self.builds_combo.setEnabled(False)
        self.refresh_builds_button.setEnabled(False)

        self.previous_ub_enabled = self.update_button.isEnabled()
        if update_button:
            self.update_button.setEnabled(False)

    def enable_controls(self, builds_combo=False):
        self.tiles_radio_button.setEnabled(True)
        self.console_radio_button.setEnabled(True)
        if is_64_windows():
            self.x64_radio_button.setEnabled(True)
        self.x86_radio_button.setEnabled(True)

        self.refresh_builds_button.setEnabled(True)

        if builds_combo:
            self.builds_combo.setEnabled(True)
        else:
            self.builds_combo.setEnabled(self.previous_bc_enabled)

        self.update_button.setEnabled(self.previous_ub_enabled)

    def download_game_update(self, url):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        status_bar.busy += 1

        downloading_label = QLabel()
        downloading_label.setText('Downloading: {0}'.format(url))
        status_bar.addWidget(downloading_label, 100)
        self.downloading_label = downloading_label

        dowloading_speed_label = QLabel()
        status_bar.addWidget(dowloading_speed_label)
        self.dowloading_speed_label = dowloading_speed_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.downloading_progress_bar = progress_bar
        progress_bar.setMinimum(0)

        self.download_last_read = datetime.utcnow()
        self.download_last_bytes_read = 0
        self.download_speed_count = 0

        self.download_http_reply = self.qnam.get(QNetworkRequest(QUrl(url)))
        self.download_http_reply.finished.connect(self.download_http_finished)
        self.download_http_reply.readyRead.connect(
            self.download_http_ready_read)
        self.download_http_reply.downloadProgress.connect(
            self.download_dl_progress)

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        if game_dir_group_box.exe_path is not None:
            self.update_button.setText('Cancel update')
        else:
            self.update_button.setText('Cancel installation')

    def download_http_finished(self):
        self.downloading_file.close()

        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.removeWidget(self.downloading_label)
        status_bar.removeWidget(self.dowloading_speed_label)
        status_bar.removeWidget(self.downloading_progress_bar)

        status_bar.busy -= 1

        if self.download_aborted:
            download_dir = os.path.dirname(self.downloaded_file)
            shutil.rmtree(download_dir)
        else:
            # Test downloaded file
            status_bar.showMessage('Testing downloaded file archive')

            try:
                with zipfile.ZipFile(self.downloaded_file) as z:
                    if z.testzip() is not None:
                        status_bar.clearMessage()
                        status_bar.showMessage('Downloaded archive is invalid')

                        download_dir = os.path.dirname(self.downloaded_file)
                        shutil.rmtree(download_dir)
                        self.finish_updating()

                        return
            except zipfile.BadZipFile:
                status_bar.clearMessage()
                status_bar.showMessage('Could not download game')

                download_dir = os.path.dirname(self.downloaded_file)
                shutil.rmtree(download_dir)
                self.finish_updating()

                return

            status_bar.clearMessage()
            self.backup_current_game()

    def backup_current_game(self):
        self.backing_up_game = True

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        game_dir = game_dir_group_box.dir_edit.text()
        self.game_dir = game_dir

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        backup_dir = os.path.join(game_dir, 'previous_version')
        if os.path.isdir(backup_dir):
            shutil.rmtree(backup_dir)

        dir_list = os.listdir(game_dir)
        self.backup_dir_list = dir_list

        if get_config_value('prevent_save_move', False) and 'save' in dir_list:
            dir_list.remove('save')

        if len(dir_list) > 0:
            status_bar.busy += 1

            backup_label = QLabel()
            status_bar.addWidget(backup_label, 100)
            self.backup_label = backup_label

            progress_bar = QProgressBar()
            status_bar.addWidget(progress_bar)
            self.backup_progress_bar = progress_bar

            timer = QTimer(self)
            self.backup_timer = timer

            progress_bar.setRange(0, len(dir_list))

            os.makedirs(backup_dir)
            self.backup_dir = backup_dir
            self.backup_index = 0

            def timeout():
                self.backup_progress_bar.setValue(self.backup_index)

                if self.backup_index == len(self.backup_dir_list):
                    self.backup_timer.stop()

                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    status_bar.removeWidget(self.backup_label)
                    status_bar.removeWidget(self.backup_progress_bar)

                    status_bar.busy -= 1

                    self.backing_up_game = False
                    self.extract_new_build()

                else:
                    backup_element = self.backup_dir_list[self.backup_index]
                    self.backup_label.setText('Backing up {0}'.format(
                        backup_element))
                    
                    shutil.move(os.path.join(self.game_dir, backup_element),
                        self.backup_dir)

                    self.backup_index += 1

            timer.timeout.connect(timeout)
            timer.start(0)
        else:
            self.backing_up_game = False
            self.extract_new_build()

    def extract_new_build(self):
        self.extracting_new_build = True
        
        z = zipfile.ZipFile(self.downloaded_file)
        self.extracting_zipfile = z

        self.extracting_infolist = z.infolist()
        self.extracting_index = 0

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_bar.busy += 1

        extracting_label = QLabel()
        status_bar.addWidget(extracting_label, 100)
        self.extracting_label = extracting_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.extracting_progress_bar = progress_bar

        timer = QTimer(self)
        self.extracting_timer = timer

        progress_bar.setRange(0, len(self.extracting_infolist))

        def timeout():
            self.extracting_progress_bar.setValue(self.extracting_index)

            if self.extracting_index == len(self.extracting_infolist):
                self.extracting_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.removeWidget(self.extracting_label)
                status_bar.removeWidget(self.extracting_progress_bar)

                status_bar.busy -= 1

                self.extracting_new_build = False

                self.extracting_zipfile.close()

                download_dir = os.path.dirname(self.downloaded_file)
                shutil.rmtree(download_dir)

                main_tab = self.get_main_tab()
                game_dir_group_box = main_tab.game_dir_group_box

                self.analysing_new_build = True
                game_dir_group_box.analyse_new_build(self.selected_build)

            else:
                extracting_element = self.extracting_infolist[
                    self.extracting_index]
                self.extracting_label.setText('Extracting {0}'.format(
                    extracting_element.filename))
                
                self.extracting_zipfile.extract(extracting_element,
                    self.game_dir)

                self.extracting_index += 1

        timer.timeout.connect(timeout)
        timer.start(0)

    def asset_name(self, path, filename):
        asset_file = os.path.join(path, filename)
        if os.path.isfile(asset_file):
            with open(asset_file, 'r') as f:
                for line in f:
                    if line.startswith('NAME'):
                        space_index = line.find(' ')
                        name = line[space_index:].strip().replace(
                            ',', '')
                        return name
        return None

    def mod_ident(self, path):
        json_file = os.path.join(path, 'modinfo.json')
        if os.path.isfile(json_file):
            with open(json_file, 'r') as f:
                values = {}
                try:
                    values = json.load(f)
                except json.JSONDecodeError:
                    pass
                if 'ident' in values:
                    return values['ident']

        return None

    def post_extraction(self):
        self.analysing_new_build = False
        self.in_post_extraction = True

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        # Copy config, save, templates and memorial directory from previous
        # version
        previous_version_dir = os.path.join(self.game_dir, 'previous_version')
        if os.path.isdir(previous_version_dir) and self.in_post_extraction:

            previous_dirs = ['config', 'save', 'templates', 'memorial']
            if (get_config_value('prevent_save_move', False) and
                'save' in previous_dirs):
                previous_dirs.remove('save')

            for previous_dir in previous_dirs:
                previous_dir_path = os.path.join(previous_version_dir,
                    previous_dir)

                if os.path.isdir(previous_dir_path):
                    status_bar.showMessage(
                        'Restoring {0} directory from previous version'.format(
                            previous_dir))
                    dst_dir = os.path.join(self.game_dir, previous_dir)
                    shutil.copytree(previous_dir_path, dst_dir)

                if not self.in_post_extraction:
                    break

        status_bar.clearMessage()

        # Copy custom tilesets, mods and soundpack from previous version
        # tilesets
        tilesets_dir = os.path.join(self.game_dir, 'gfx')
        previous_tilesets_dir = os.path.join(self.game_dir, 'previous_version',
            'gfx')

        if (os.path.isdir(tilesets_dir) and os.path.isdir(previous_tilesets_dir)
            and self.in_post_extraction):
            status_bar.showMessage('Restoring custom tilesets')

            official_set = {}
            for entry in os.listdir(tilesets_dir):
                if not self.in_post_extraction:
                    break

                entry_path = os.path.join(tilesets_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.asset_name(entry_path, 'tileset.txt')
                    if name is not None and name not in official_set:
                        official_set[name] = entry_path

            previous_set = {}
            for entry in os.listdir(previous_tilesets_dir):
                if not self.in_post_extraction:
                    break

                entry_path = os.path.join(previous_tilesets_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.asset_name(entry_path, 'tileset.txt')
                    if name is not None and name not in previous_set:
                        previous_set[name] = entry_path

            custom_set = set(previous_set.keys()) - set(official_set.keys())
            for item in custom_set:
                if not self.in_post_extraction:
                    break

                target_dir = os.path.join(tilesets_dir, os.path.basename(
                    previous_set[item]))
                if not os.path.exists(target_dir):
                    shutil.copytree(previous_set[item], target_dir)

            status_bar.clearMessage()

        # soundpacks
        soundpack_dir = os.path.join(self.game_dir, 'data', 'sound')
        previous_soundpack_dir = os.path.join(self.game_dir, 'previous_version',
            'data', 'sound')

        if (os.path.isdir(soundpack_dir) and os.path.isdir(
            previous_soundpack_dir) and self.in_post_extraction):
            status_bar.showMessage('Restoring custom soundpacks')

            official_set = {}
            for entry in os.listdir(soundpack_dir):
                if not self.in_post_extraction:
                    break

                entry_path = os.path.join(soundpack_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.asset_name(entry_path, 'soundpack.txt')
                    if name is not None and name not in official_set:
                        official_set[name] = entry_path

            previous_set = {}
            for entry in os.listdir(previous_soundpack_dir):
                if not self.in_post_extraction:
                    break

                entry_path = os.path.join(previous_soundpack_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.asset_name(entry_path, 'soundpack.txt')
                    if name is not None and name not in previous_set:
                        previous_set[name] = entry_path

            custom_set = set(previous_set.keys()) - set(official_set.keys())
            for item in custom_set:
                if not self.in_post_extraction:
                    break

                target_dir = os.path.join(soundpack_dir, os.path.basename(
                    previous_set[item]))
                if not os.path.exists(target_dir):
                    shutil.copytree(previous_set[item], target_dir)

            status_bar.clearMessage()
        
        # mods
        mods_dir = os.path.join(self.game_dir, 'data', 'mods')
        previous_mods_dir = os.path.join(self.game_dir, 'previous_version',
            'data', 'mods')

        if (os.path.isdir(mods_dir) and os.path.isdir(previous_mods_dir) and
            self.in_post_extraction):
            status_bar.showMessage('Restoring custom mods')

            official_set = {}
            for entry in os.listdir(mods_dir):
                entry_path = os.path.join(mods_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.mod_ident(entry_path)
                    if name is not None and name not in official_set:
                        official_set[name] = entry_path
            previous_set = {}
            for entry in os.listdir(previous_mods_dir):
                entry_path = os.path.join(previous_mods_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.mod_ident(entry_path)
                    if name is not None and name not in previous_set:
                        previous_set[name] = entry_path

            custom_set = set(previous_set.keys()) - set(official_set.keys())
            for item in custom_set:
                target_dir = os.path.join(mods_dir, os.path.basename(
                    previous_set[item]))
                if not os.path.exists(target_dir):
                    shutil.copytree(previous_set[item], target_dir)

            status_bar.clearMessage()

        if not self.in_post_extraction:
            return

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        if game_dir_group_box.previous_exe_path is not None:
            status_bar.showMessage('Update completed')
        else:
            status_bar.showMessage('Installation completed')

        self.in_post_extraction = False

        self.finish_updating()

    def finish_updating(self):
        self.updating = False
        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        game_dir_group_box.enable_controls()
        self.enable_controls(True)

        if game_dir_group_box.exe_path is not None:
            self.update_button.setText('Update game')
        else:
            self.update_button.setText('Install game')

        if self.close_after_update:
            self.get_main_window().close()

    def download_http_ready_read(self):
        self.downloading_file.write(self.download_http_reply.readAll())

    def download_dl_progress(self, bytes_read, total_bytes):
        self.downloading_progress_bar.setMaximum(total_bytes)
        self.downloading_progress_bar.setValue(bytes_read)

        self.download_speed_count += 1

        if self.download_speed_count % 5 == 0:
            delta_bytes = bytes_read - self.download_last_bytes_read
            delta_time = datetime.utcnow() - self.download_last_read

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.dowloading_speed_label.setText('{0}/s'.format(
                sizeof_fmt(bytes_secs)))

            self.download_last_bytes_read = bytes_read
            self.download_last_read = datetime.utcnow()

    def start_lb_request(self, url):
        self.disable_controls(True)

        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        status_bar.busy += 1

        self.builds_combo.clear()
        self.builds_combo.addItem('Fetching remote builds')

        fetching_label = QLabel()
        fetching_label.setText('Fetching: {0}'.format(url))
        self.base_url = url
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

        status_bar.busy -= 1
        if status_bar.busy == 0:
            status_bar.showMessage('Ready')

        self.enable_controls()

        self.lb_html.seek(0)
        document = html5lib.parse(self.lb_html, treebuilder='lxml',
            encoding='utf8', namespaceHTMLElements=False)

        builds = []
        for row in document.getroot().cssselect('tr'):
            build = {}
            for index, cell in enumerate(row.cssselect('td')):
                if index == 1:
                    if len(cell) > 0 and cell[0].text.startswith(
                        'cataclysmdda'):
                        anchor = cell[0]
                        url = urljoin(self.base_url, anchor.get('href'))
                        name = anchor.text

                        build_number = None
                        match = re.search(
                            'cataclysmdda-[01]\\.[A-F]-(?P<build>\d+)', name)
                        if match is not None:
                            build_number = match.group('build')

                        build['url'] = url
                        build['name'] = name
                        build['number'] = build_number
                elif index == 2:
                    # build date
                    str_date = cell.text.strip()
                    if str_date != '':
                        build_date = datetime.strptime(str_date,
                            '%Y-%m-%d %H:%M')
                        build['date'] = build_date

            if 'url' in build:
                builds.append(build)

        self.lb_html = BytesIO()

        if len(builds) > 0:
            builds.reverse()
            self.builds = builds

            self.builds_combo.clear()
            for index, build in enumerate(builds):
                build_date = arrow.get(build['date'], 'UTC')
                human_delta = build_date.humanize(arrow.utcnow())

                if index == 0:
                    self.builds_combo.addItem(
                        '{number} ({delta}) - latest'.format(
                        number=build['number'], delta=human_delta))
                else:
                    self.builds_combo.addItem('{number} ({delta})'.format(
                        number=build['number'], delta=human_delta))

            self.builds_combo.setEnabled(True)

            main_tab = self.get_main_tab()
            game_dir_group_box = main_tab.game_dir_group_box

            if game_dir_group_box.exe_path is not None:
                self.update_button.setText('Update game')
            else:
                self.update_button.setText('Install game')

            self.update_button.setEnabled(True)

        else:
            self.builds = None

            self.builds_combo.clear()
            self.builds_combo.addItem('Could not find remote builds')
            self.builds_combo.setEnabled(False)

    def lb_http_ready_read(self):
        self.lb_html.write(self.http_reply.readAll())

    def lb_dl_progress(self, bytes_read, total_bytes):
        self.fetching_progress_bar.setMaximum(total_bytes)
        self.fetching_progress_bar.setValue(bytes_read)

    def refresh_builds(self):
        selected_graphics = self.graphics_button_group.checkedButton().text()
        selected_platform = self.platform_button_group.checkedButton().text()
        url = BASE_URLS[selected_graphics][selected_platform]

        self.start_lb_request(url)

    def graphics_clicked(self, button):
        set_config_value('graphics', button.text())

        self.refresh_builds()

    def platform_clicked(self, button):
        set_config_value('platform', button.text())

        self.refresh_builds()


class AboutDialog(QDialog):
    def __init__(self, parent=0, f=0):
        super(AboutDialog, self).__init__(parent, f)

        layout = QGridLayout()

        text_content = QTextBrowser()
        text_content.setReadOnly(True)
        text_content.setOpenExternalLinks(True)
        text_content.setHtml('''
<p>CDDA Game Launcher version {version}</p>

<p>Get the latest release <a href="https://github.com/remyroy/CDDA-Game-Launcher/releases">on Github</a>.</p>

<p>Please report any issue <a href="https://github.com/remyroy/CDDA-Game-Launcher/issues/new">on Github</a>.</p>

<p>Copyright (c) 2015 Rémy Roy</p>

<p>Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:</p>

<p>The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.</p>

<p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</p>

'''.format(version=version))
        layout.addWidget(text_content, 0, 0)
        self.text_content = text_content

        ok_button = QPushButton()
        ok_button.setText('OK')
        ok_button.clicked.connect(self.done)
        layout.addWidget(ok_button, 1, 0, Qt.AlignRight)
        self.ok_button = ok_button

        layout.setRowStretch(0, 100)

        self.setMinimumSize(400, 250)

        self.setLayout(layout)
        self.setWindowTitle('About CDDA Game Launcher')


class LauncherSettingsGroupBox(QGroupBox):
    def __init__(self):
        super(LauncherSettingsGroupBox, self).__init__()

        layout = QGridLayout()

        command_line_parameters_label = QLabel()
        command_line_parameters_label.setText('Command line parameters:')
        layout.addWidget(command_line_parameters_label, 0, 0, Qt.AlignRight)
        self.command_line_parameters_label = command_line_parameters_label

        command_line_parameters_edit = QLineEdit()
        command_line_parameters_edit.setText(get_config_value('command.params',
            ''))
        command_line_parameters_edit.editingFinished.connect(
            self.clp_changed)
        layout.addWidget(command_line_parameters_edit, 0, 1)
        self.command_line_parameters_edit = command_line_parameters_edit

        self.setTitle('Launcher')
        self.setLayout(layout)

    def clp_changed(self):
        set_config_value('command.params',
            self.command_line_parameters_edit.text())


class UpdateSettingsGroupBox(QGroupBox):
    def __init__(self):
        super(UpdateSettingsGroupBox, self).__init__()

        layout = QGridLayout()

        prevent_save_move_checkbox = QCheckBox()
        prevent_save_move_checkbox.setText(
            'Do not copy or move the save directory')
        prevent_save_move_checkbox.setToolTip('If your save directory size is '
            'large, it might take a long time to copy it during the update '
            'process. This option might help you speed the whole thing but '
            'your previous version will lack the save directory.')
        check_state = (Qt.Checked if get_config_value(
            'prevent_save_move', False) else Qt.Unchecked)
        prevent_save_move_checkbox.setCheckState(check_state)
        prevent_save_move_checkbox.stateChanged.connect(self.psmc_changed)
        layout.addWidget(prevent_save_move_checkbox, 0, 0)
        self.prevent_save_move_checkbox = prevent_save_move_checkbox

        self.setTitle('Update/Installation')
        self.setLayout(layout)

    def psmc_changed(self, state):
        set_config_value('prevent_save_move', state != Qt.Unchecked)

def start_ui():
    app = QApplication(sys.argv)
    mainWin = MainWindow('CDDA Game Launcher')
    mainWin.show()
    sys.exit(app.exec_())