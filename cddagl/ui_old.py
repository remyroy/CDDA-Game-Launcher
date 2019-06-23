import sys
import os
import hashlib
import re
import subprocess
import random
import shutil
import zipfile
import json
import traceback
import html
import stat
import logging
import platform
import tempfile
import xml.etree.ElementTree
import markdown

from os import scandir

from datetime import datetime, timedelta, timezone
import arrow

from babel.core import Locale
from babel.numbers import format_percent
from babel.dates import format_datetime

from io import BytesIO, StringIO, TextIOWrapper
from collections import deque

from rfc6266 import parse_headers as parse_cd_headers

from urllib.parse import urljoin, urlencode

import rarfile
from py7zlib import Archive7z, NoPasswordGivenError, FormatError

from distutils.version import LooseVersion

from pywintypes import error as PyWinError, com_error

import winutils

from PyQt5.QtCore import (
    Qt, QTimer, QUrl, QFileInfo, pyqtSignal, QByteArray, QStringListModel,
    QSize, QRect, QThread, QItemSelectionModel, QItemSelection)
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QGroupBox, QMainWindow,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QToolButton,
    QProgressBar, QButtonGroup, QRadioButton, QComboBox, QAction, QDialog,
    QTextBrowser, QTabWidget, QCheckBox, QMessageBox, QStyle, QHBoxLayout,
    QSpinBox, QListView, QAbstractItemView, QTextEdit, QSizePolicy,
    QTableWidget, QTableWidgetItem, QMenu)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

from cddagl.i18n import (
    load_gettext_locale, get_available_locales,
    proxy_ngettext as ngettext, proxy_gettext as _
)
from cddagl.sql.functions import (
    get_config_value, set_config_value, new_version, get_build_from_sha256,
    new_build, config_true)
from cddagl.win32 import (
    find_process_with_file_handle, get_downloads_directory, get_ui_locale,
    activate_window, SimpleNamedPipe, process_id_from_path,
    wait_for_pid)
import cddagl.constants as cons
from cddagl.constants import get_locale_path, get_data_path, get_resource_path, get_cddagl_path
from cddagl.functions import (
    tryint, move_path, is_64_windows, sizeof_fmt, safe_filename, alphanum_key,
    delete_path, arstrip, clean_qt_path, unique, log_exception, bitness
)
from cddagl.ui.views.soundpacks import SoundpacksTab
from cddagl.ui.views.mods import ModsTab
from cddagl.ui.views.dialogs import BrowserDownloadDialog
from cddagl.ui.views.settings import SettingsTab

import cddagl
version = cddagl.__version__


logger = logging.getLogger('cddagl')

if getattr(sys, 'frozen', False):
    rarfile.UNRAR_TOOL = get_cddagl_path('UnRAR.exe')


def retry_rename(src, dst):
    while os.path.exists(src):
        try:
            os.rename(src, dst)
        except OSError as e:
            retry_msgbox = QMessageBox()
            retry_msgbox.setWindowTitle(_('Cannot rename file'))

            process = None
            if e.filename is not None:
                process = find_process_with_file_handle(e.filename)

            text = _('''
<p>The launcher failed to rename the following file: {src} to {dst}</p>
<p>When trying to rename or access {filename}, the launcher raised the
following error: {error}</p>
''').format(
    src=html.escape(src),
    dst=html.escape(dst),
    filename=html.escape(e.filename),
    error=html.escape(e.strerror))

            if process is None:
                text = text + _('''
<p>No process seems to be using that file.</p>
''')
            else:
                text = text + _('''
<p>The process <strong>{image_file_name} ({pid})</strong> is currently using
that file. You might need to end it if you want to retry.</p>
''').format(image_file_name=process['image_file_name'], pid=process['pid'])

            retry_msgbox.setText(text)
            retry_msgbox.setInformativeText(_('Do you want to retry renaming '
                'this file?'))
            retry_msgbox.addButton(_('Retry renaming the file'),
                QMessageBox.YesRole)
            retry_msgbox.addButton(_('Cancel the operation'),
                QMessageBox.NoRole)
            retry_msgbox.setIcon(QMessageBox.Critical)

            if retry_msgbox.exec() == 1:
                return False

    return True


class MainWindow(QMainWindow):
    def __init__(self, title):
        super(MainWindow, self).__init__()

        self.setMinimumSize(440, 540)

        self.create_status_bar()
        self.create_central_widget()
        self.create_menu()

        self.shown = False
        self.qnam = QNetworkAccessManager()
        self.http_reply = None
        self.in_manual_update_check = False

        self.about_dialog = None

        geometry = get_config_value('window_geometry')
        if geometry is not None:
            qt_geometry = QByteArray.fromBase64(geometry.encode('utf8'))
            self.restoreGeometry(qt_geometry)

        self.setWindowTitle(title)

        if not config_true(get_config_value('allow_multiple_instances',
            'False')):
            self.init_named_pipe()

    def set_text(self):
        self.file_menu.setTitle(_('&File'))
        self.exit_action.setText(_('E&xit'))
        self.help_menu.setTitle(_('&Help'))
        if getattr(sys, 'frozen', False):
            self.update_action.setText(_('&Check for update'))
        self.about_action.setText(_('&About CDDA Game Launcher'))

        if self.about_dialog is not None:
            self.about_dialog.set_text()
        self.central_widget.set_text()

    def create_status_bar(self):
        status_bar = self.statusBar()
        status_bar.busy = 0

        status_bar.showMessage(_('Ready'))

    def create_central_widget(self):
        central_widget = CentralWidget()
        self.setCentralWidget(central_widget)
        self.central_widget = central_widget

    def create_menu(self):
        file_menu = QMenu(_('&File'))
        self.menuBar().addMenu(file_menu)
        self.file_menu = file_menu

        exit_action = QAction(_('E&xit'), self, triggered=self.close)
        file_menu.addAction(exit_action)
        self.exit_action = exit_action

        help_menu = QMenu(_('&Help'))
        self.menuBar().addMenu(help_menu)
        self.help_menu = help_menu

        if getattr(sys, 'frozen', False):
            update_action = QAction(_('&Check for update'), self,
                triggered=self.manual_update_check)
            self.update_action = update_action
            self.help_menu.addAction(update_action)
            self.help_menu.addSeparator()

        about_action = QAction(_('&About CDDA Game Launcher'), self,
            triggered=self.show_about_dialog)
        self.about_action = about_action
        self.help_menu.addAction(about_action)

    def show_about_dialog(self):
        if self.about_dialog is None:
            about_dialog = AboutDialog(self, Qt.WindowTitleHint |
                Qt.WindowCloseButtonHint)
            self.about_dialog = about_dialog

        self.about_dialog.exec()

    def check_new_launcher_version(self):
        self.lv_html = BytesIO()

        url = cons.GITHUB_REST_API_URL + cons.CDDAGL_LATEST_RELEASE

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent',
            b'CDDA-Game-Launcher/' + version.encode('utf8'))
        request.setRawHeader(b'Accept', cons.GITHUB_API_VERSION)

        self.http_reply = self.qnam.get(request)
        self.http_reply.finished.connect(self.lv_http_finished)
        self.http_reply.readyRead.connect(self.lv_http_ready_read)

    def lv_http_finished(self):
        redirect = self.http_reply.attribute(
            QNetworkRequest.RedirectionTargetAttribute)
        if redirect is not None:
            redirected_url = urljoin(
                self.http_reply.request().url().toString(),
                redirect.toString())

            self.lv_html = BytesIO()

            request = QNetworkRequest(QUrl(redirected_url))
            request.setRawHeader(b'User-Agent',
                b'CDDA-Game-Launcher/' + version.encode('utf8'))
            request.setRawHeader(b'Accept', cons.GITHUB_API_VERSION)

            self.http_reply = self.qnam.get(request)
            self.http_reply.finished.connect(self.lv_http_finished)
            self.http_reply.readyRead.connect(self.lv_http_ready_read)
            return

        status_code = self.http_reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            reason = self.http_reply.attribute(
                QNetworkRequest.HttpReasonPhraseAttribute)
            url = self.http_reply.request().url().toString()
            msg = _('Could not find launcher latest release '
                '[HTTP {status_code}] ({reason}) when requesting {url}'
                ).format(
                    status_code=status_code,
                    reason=reason,
                    url=url
                )
            logger.warning(msg)

            if self.in_manual_update_check:
                self.in_manual_update_check = False

            self.lv_html = None
            return

        self.lv_html.seek(0)

        try:
            latest_release = json.loads(TextIOWrapper(self.lv_html,
                encoding='utf8').read())
        except json.decoder.JSONDecodeError:
            latest_release = {
                'cannot_decode': True
            }

        self.lv_html = None

        if 'name' not in latest_release:
            return
        if 'html_url' not in latest_release:
            return
        if 'tag_name' not in latest_release:
            return
        if 'assets' not in latest_release:
            return
        if 'body' not in latest_release:
            return

        version_text = latest_release['tag_name']
        if version_text.startswith('v'):
            version_text = version_text[1:]
        latest_version = LooseVersion(version_text)

        if latest_version is None:
            return

        executable_url = None
        for file_asset in latest_release['assets']:
            if not 'name' in file_asset:
                continue
            if 'browser_download_url' not in file_asset:
                continue
            if file_asset['name'].endswith('.exe'):
                executable_url = file_asset['browser_download_url']
                break

        if executable_url is None:
            return

        current_version = LooseVersion(version)

        if latest_version > current_version:

            markdown_desc = latest_release['body']

            # Replace number signs with issue links
            number_pattern = ' \\#(?P<id>\\d+)'
            replacement_pattern = (' [#\\g<id>](' + cons.CDDAGL_ISSUE_URL_ROOT +
                '\\g<id>)')
            markdown_desc = re.sub(number_pattern, replacement_pattern,
                markdown_desc)

            html_desc = markdown.markdown(markdown_desc)

            release_html = ('''
<h2><a href="{release_url}">{release_name}</a></h2>{description}
                ''').format(
                release_url=html.escape(latest_release['html_url']),
                release_name=html.escape(latest_release['name']),
                description=html_desc)

            no_launcher_version_check_checkbox = QCheckBox()
            no_launcher_version_check_checkbox.setText(_('Do not check '
                'for new version of the CDDA Game Launcher on launch'))
            check_state = (Qt.Checked if config_true(get_config_value(
                'prevent_version_check_launch', 'False'))
                else Qt.Unchecked)
            no_launcher_version_check_checkbox.stateChanged.connect(
                self.nlvcc_changed)
            no_launcher_version_check_checkbox.setCheckState(
                check_state)

            launcher_update_msgbox = QMessageBox()
            launcher_update_msgbox.setWindowTitle(_('Launcher update'))
            launcher_update_msgbox.setText(_('You are using version '
                '{version} but there is a new update for CDDA Game '
                'Launcher. Would you like to update?').format(
                version=version))
            launcher_update_msgbox.setInformativeText(release_html)
            launcher_update_msgbox.addButton(_('Update the launcher'),
                QMessageBox.YesRole)
            launcher_update_msgbox.addButton(_('Not right now'),
                QMessageBox.NoRole)
            launcher_update_msgbox.setCheckBox(
                no_launcher_version_check_checkbox)
            launcher_update_msgbox.setIcon(QMessageBox.Question)

            if launcher_update_msgbox.exec() == 0:
                flags = Qt.WindowTitleHint | Qt.WindowCloseButtonHint

                launcher_update_dialog = (LauncherUpdateDialog(executable_url,
                    version_text, self, flags))
                launcher_update_dialog.exec()

                if launcher_update_dialog.updated:
                    self.close()

        else:
            self.no_launcher_update_found()

    def nlvcc_changed(self, state):
        no_launcher_version_check_checkbox = (
            self.central_widget.settings_tab.launcher_settings_group_box.no_launcher_version_check_checkbox)
        no_launcher_version_check_checkbox.setCheckState(state)

    def manual_update_check(self):
        self.in_manual_update_check = True
        self.check_new_launcher_version()

    def no_launcher_update_found(self):
        if self.in_manual_update_check:
            up_to_date_msgbox = QMessageBox()
            up_to_date_msgbox.setWindowTitle(_('Up to date'))
            up_to_date_msgbox.setText(_('The CDDA Game Launcher is up to date.'
                ))
            up_to_date_msgbox.setIcon(QMessageBox.Information)

            up_to_date_msgbox.exec()

            self.in_manual_update_check = False

    def lv_http_ready_read(self):
        self.lv_html.write(self.http_reply.readAll())

    def init_named_pipe(self):
        class PipeReadWaitThread(QThread):
            read = pyqtSignal(bytes)

            def __init__(self):
                super(PipeReadWaitThread, self).__init__()

                try:
                    self.pipe = SimpleNamedPipe('cddagl_instance')
                except (OSError, PyWinError):
                    self.pipe = None

            def __del__(self):
                self.wait()

            def run(self):
                if self.pipe is None:
                    return

                while self.pipe is not None:
                    if self.pipe.connect() and self.pipe is not None:
                        try:
                            value = self.pipe.read(1024)
                            self.read.emit(value)
                        except (PyWinError, IOError):
                            pass

        def instance_read(value):
            if value == b'dupe':
                self.showNormal()
                self.raise_()
                self.activateWindow()

        pipe_read_wait_thread = PipeReadWaitThread()
        pipe_read_wait_thread.read.connect(instance_read)
        pipe_read_wait_thread.start()

        self.pipe_read_wait_thread = pipe_read_wait_thread

    def showEvent(self, event):
        if not self.shown:
            if not config_true(get_config_value('prevent_version_check_launch',
                'False')):
                if getattr(sys, 'frozen', False):
                    self.in_manual_update_check = False
                    self.check_new_launcher_version()

        self.shown = True

    def save_geometry(self):
        geometry = self.saveGeometry().toBase64().data().decode('utf8')
        set_config_value('window_geometry', geometry)

        backups_tab = self.central_widget.backups_tab
        backups_tab.save_geometry()

    def closeEvent(self, event):
        update_group_box = self.central_widget.main_tab.update_group_box
        soundpacks_tab = self.central_widget.soundpacks_tab

        if update_group_box.updating:
            update_group_box.close_after_update = True
            update_group_box.update_game()

            if not update_group_box.updating:
                self.save_geometry()
                event.accept()
            else:
                event.ignore()
        elif soundpacks_tab.installing_new_soundpack:
            soundpacks_tab.close_after_install = True
            soundpacks_tab.install_new()

            if not soundpacks_tab.installing_new_soundpack:
                self.save_geometry()
                event.accept()
            else:
                event.ignore()
        else:
            self.save_geometry()
            event.accept()


class CentralWidget(QTabWidget):
    def __init__(self):
        super(CentralWidget, self).__init__()

        self.create_main_tab()
        self.create_backups_tab()
        self.create_mods_tab()
        #self.create_tilesets_tab()
        self.create_soundpacks_tab()
        #self.create_fonts_tab()
        self.create_settings_tab()

    def set_text(self):
        self.setTabText(self.indexOf(self.main_tab), _('Main'))
        self.setTabText(self.indexOf(self.backups_tab), _('Backups'))
        self.setTabText(self.indexOf(self.mods_tab), _('Mods'))
        #self.setTabText(self.indexOf(self.tilesets_tab), _('Tilesets'))
        self.setTabText(self.indexOf(self.soundpacks_tab), _('Soundpacks'))
        #self.setTabText(self.indexOf(self.fonts_tab), _('Fonts'))
        self.setTabText(self.indexOf(self.settings_tab), _('Settings'))

        self.main_tab.set_text()
        self.backups_tab.set_text()
        self.mods_tab.set_text()
        #self.tilesets_tab.set_text()
        self.soundpacks_tab.set_text()
        #self.fonts_tab.set_text()
        self.settings_tab.set_text()

    def create_main_tab(self):
        main_tab = MainTab()
        self.addTab(main_tab, _('Main'))
        self.main_tab = main_tab

    def create_backups_tab(self):
        backups_tab = BackupsTab()
        self.addTab(backups_tab, _('Backups'))
        self.backups_tab = backups_tab

    def create_mods_tab(self):
        mods_tab = ModsTab()
        self.addTab(mods_tab, _('Mods'))
        self.mods_tab = mods_tab

    def create_tilesets_tab(self):
        tilesets_tab = TilesetsTab()
        self.addTab(tilesets_tab, _('Tilesets'))
        self.tilesets_tab = tilesets_tab

    def create_soundpacks_tab(self):
        soundpacks_tab = SoundpacksTab()
        self.addTab(soundpacks_tab, _('Soundpacks'))
        self.soundpacks_tab = soundpacks_tab

    def create_fonts_tab(self):
        fonts_tab = FontsTab()
        self.addTab(fonts_tab, _('Fonts'))
        self.fonts_tab = fonts_tab

    def create_settings_tab(self):
        settings_tab = SettingsTab()
        self.addTab(settings_tab, _('Settings'))
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

    def set_text(self):
        self.game_dir_group_box.set_text()
        self.update_group_box.set_text()

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_settings_tab(self):
        return self.parentWidget().parentWidget().settings_tab

    def get_soundpacks_tab(self):
        return self.parentWidget().parentWidget().soundpacks_tab

    def get_mods_tab(self):
        return self.parentWidget().parentWidget().mods_tab

    def get_backups_tab(self):
        return self.parentWidget().parentWidget().backups_tab

    def disable_tab(self):
        self.game_dir_group_box.disable_controls()
        self.update_group_box.disable_controls(True)

    def enable_tab(self):
        self.game_dir_group_box.enable_controls()
        self.update_group_box.enable_controls()


class GameDirGroupBox(QGroupBox):
    def __init__(self):
        super(GameDirGroupBox, self).__init__()

        self.shown = False
        self.exe_path = None
        self.restored_previous = False
        self.current_build = None

        self.exe_reading_timer = None
        self.update_saves_timer = None
        self.saves_size = 0

        self.dir_combo_inserting = False

        self.game_process = None
        self.game_process_id = None
        self.game_started = False

        layout = QGridLayout()

        dir_label = QLabel()
        layout.addWidget(dir_label, 0, 0, Qt.AlignRight)
        self.dir_label = dir_label

        dir_combo = QComboBox()
        dir_combo.setEditable(True)
        dir_combo.setInsertPolicy(QComboBox.InsertAtTop)
        dir_combo.currentIndexChanged.connect(self.dc_index_changed)
        self.dir_combo = dir_combo
        layout.addWidget(dir_combo, 0, 1)

        dir_combo_model = QStringListModel(json.loads(get_config_value(
            'game_directories', '[]')), self)
        dir_combo.setModel(dir_combo_model)
        self.dir_combo_model = dir_combo_model

        dir_change_button = QToolButton()
        dir_change_button.setText('...')
        dir_change_button.clicked.connect(self.set_game_directory)
        layout.addWidget(dir_change_button, 0, 2)
        self.dir_change_button = dir_change_button

        version_label = QLabel()
        layout.addWidget(version_label, 1, 0, Qt.AlignRight)
        self.version_label = version_label

        version_value_label = QLineEdit()
        version_value_label.setReadOnly(True)
        layout.addWidget(version_value_label, 1, 1)
        self.version_value_label = version_value_label

        build_label = QLabel()
        layout.addWidget(build_label, 2, 0, Qt.AlignRight)
        self.build_label = build_label

        build_value_label = QLineEdit()
        build_value_label.setReadOnly(True)
        build_value_label.setText(_('Unknown'))
        layout.addWidget(build_value_label, 2, 1)
        self.build_value_label = build_value_label

        saves_label = QLabel()
        layout.addWidget(saves_label, 3, 0, Qt.AlignRight)
        self.saves_label = saves_label

        saves_value_edit = QLineEdit()
        saves_value_edit.setReadOnly(True)
        saves_value_edit.setText(_('Unknown'))
        layout.addWidget(saves_value_edit, 3, 1)
        self.saves_value_edit = saves_value_edit

        saves_warning_label = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning)
        saves_warning_label.setPixmap(icon.pixmap(16, 16))
        saves_warning_label.hide()
        layout.addWidget(saves_warning_label, 3, 2)
        self.saves_warning_label = saves_warning_label

        buttons_container = QWidget()
        buttons_layout = QGridLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_container.setLayout(buttons_layout)

        launch_game_button = QPushButton()
        launch_game_button.setEnabled(False)
        launch_game_button.setStyleSheet("font-size: 20px;")
        launch_game_button.clicked.connect(self.launch_game)
        buttons_layout.addWidget(launch_game_button, 0, 0, 1, 3)
        self.launch_game_button = launch_game_button

        restore_button = QPushButton()
        restore_button.setEnabled(False)
        restore_button.clicked.connect(self.restore_previous)
        buttons_layout.addWidget(restore_button, 0, 3, 1, 1)
        self.restore_button = restore_button

        layout.addWidget(buttons_container, 4, 0, 1, 3)
        self.buttons_container = buttons_container
        self.buttons_layout = buttons_layout

        self.setLayout(layout)
        self.set_text()

    def set_text(self):
        self.dir_label.setText(_('Directory:'))
        self.version_label.setText(_('Version:'))
        self.build_label.setText(_('Build:'))
        self.saves_label.setText(_('Saves:'))
        self.saves_warning_label.setToolTip(
            _('Your save directory might be large '
            'enough to cause significant delays during the update process.\n'
            'You might want to enable the "Do not copy or move the save '
            'directory" option in the settings tab.'))
        self.launch_game_button.setText(_('Launch game'))
        self.restore_button.setText(_('Restore previous version'))
        self.setTitle(_('Game'))

    def showEvent(self, event):
        if not self.shown:
            self.shown = True

            self.last_game_directory = None

            if (getattr(sys, 'frozen', False)
                and config_true(get_config_value('use_launcher_dir', 'False'))):
                game_directory = os.path.dirname(os.path.abspath(
                    os.path.realpath(sys.executable)))

                self.dir_combo.setEnabled(False)
                self.dir_change_button.setEnabled(False)

                self.set_dir_combo_value(game_directory)
            else:
                game_directory = get_config_value('game_directory')
                if game_directory is None:
                    cddagl_path = os.path.dirname(os.path.realpath(
                        sys.executable))
                    default_dir = os.path.join(cddagl_path, 'cdda')
                    game_directory = default_dir

                self.set_dir_combo_value(game_directory)

            self.game_directory_changed()

        self.shown = True

    def set_dir_combo_value(self, value):
        dir_model = self.dir_combo.model()

        index_list = dir_model.match(dir_model.index(0, 0), Qt.DisplayRole,
            value, 1, Qt.MatchFixedString)
        if len(index_list) > 0:
            self.dir_combo.setCurrentIndex(index_list[0].row())
        else:
            self.dir_combo_inserting = True
            self.dir_combo.insertItem(0, value)
            self.dir_combo_inserting = False

            self.dir_combo.setCurrentIndex(0)

    def disable_controls(self):
        self.dir_combo.setEnabled(False)
        self.dir_change_button.setEnabled(False)

        self.launch_game_button.setEnabled(False)
        self.restore_button.setEnabled(False)

    def enable_controls(self):
        self.dir_combo.setEnabled(True)
        self.dir_change_button.setEnabled(True)

        self.launch_game_button.setEnabled(
            self.exe_path is not None and os.path.isfile(self.exe_path))

        directory = self.dir_combo.currentText()
        previous_version_dir = os.path.join(directory, 'previous_version')
        self.restore_button.setEnabled(os.path.isdir(previous_version_dir))

    def restore_previous(self):
        self.disable_controls()

        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box
        update_group_box.disable_controls(True)

        self.restored_previous = False

        try:
            game_dir = self.dir_combo.currentText()
            previous_version_dir = os.path.join(game_dir, 'previous_version')

            if os.path.isdir(previous_version_dir) and os.path.isdir(game_dir):

                with tempfile.TemporaryDirectory(prefix=cons.TEMP_PREFIX
                    ) as temp_move_dir:

                    excluded_entries = set(['previous_version'])
                    if config_true(get_config_value('prevent_save_move',
                        'False')):
                        excluded_entries.add('save')

                    # Prevent moving the launcher if it's in the game directory
                    if getattr(sys, 'frozen', False):
                        launcher_exe = os.path.abspath(sys.executable)
                        launcher_dir = os.path.dirname(launcher_exe)
                        if os.path.abspath(game_dir) == launcher_dir:
                            excluded_entries.add(os.path.basename(launcher_exe))

                    for entry in os.listdir(game_dir):
                        if entry not in excluded_entries:
                            entry_path = os.path.join(game_dir, entry)
                            shutil.move(entry_path, temp_move_dir)

                    excluded_entries = set()
                    if config_true(get_config_value('prevent_save_move', 'False')):
                        excluded_entries.add('save')
                    for entry in os.listdir(previous_version_dir):
                        if entry not in excluded_entries:
                            entry_path = os.path.join(previous_version_dir, entry)
                            shutil.move(entry_path, game_dir)

                    for entry in os.listdir(temp_move_dir):
                        entry_path = os.path.join(temp_move_dir, entry)
                        shutil.move(entry_path, previous_version_dir)

                self.restored_previous = True
        except OSError as e:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(str(e))

        self.last_game_directory = None
        self.enable_controls()
        update_group_box.enable_controls()
        self.game_directory_changed()

    def focus_game(self):
        if self.game_process is None and self.game_process_id is None:
            return

        if self.game_process is not None:
            pid = self.game_process.pid
        elif self.game_process_id is not None:
            pid = self.game_process_id

        try:
            activate_window(pid)
        except (OSError, PyWinError):
            # Can't activate window, we will assume that the game ended
            self.game_ended()

    def launch_game(self):
        if self.game_started:
            return self.focus_game()

        if config_true(get_config_value('backup_on_launch', 'False')):
            main_tab = self.get_main_tab()
            backups_tab = main_tab.get_backups_tab()

            backups_tab.prune_auto_backups()

            name = '{auto}_{name}'.format(auto=_('auto'),
                name=_('before_launch'))

            backups_tab.after_backup = self.launch_game_process
            backups_tab.backup_saves(name)
        else:
            self.launch_game_process()

    def launch_game_process(self):
        if self.exe_path is None or not os.path.isfile(self.exe_path):
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Game executable not found'))

            self.launch_game_button.setEnabled(False)
            return

        self.get_main_window().setWindowState(Qt.WindowMinimized)
        exe_dir = os.path.dirname(self.exe_path)

        params = get_config_value('command.params', '').strip()
        if params != '':
            params = ' ' + params

        cmd = '"{exe_path}"{params}'.format(exe_path=self.exe_path,
            params=params)

        try:
            game_process = subprocess.Popen(cmd, cwd=exe_dir,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        except OSError as e:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Could not launch the game executable'))

            error_msgbox = QMessageBox()
            error_msgbox.setWindowTitle(_('Cannot launch game'))

            text = _('''
<p>The launcher failed to start the game executable in <strong>{filename}</strong> .</p>
<p>It received the following error from the operating system: {error}</p>
<p>Poor antivirus products are known to detect the game binary as a threat and
block its execution. A simple workaround is to add the game binary in your
antivirus whitelist or select the action to trust this binary when detected.</p>
''').format(
    filename=html.escape(e.filename or _('[unknown]')),
    error=html.escape(e.strerror))

            error_msgbox.setText(text)
            error_msgbox.addButton(_('OK'), QMessageBox.YesRole)
            error_msgbox.setIcon(QMessageBox.Critical)

            error_msgbox.exec()
            return

        self.game_process = game_process
        self.game_started = True

        if not config_true(get_config_value('keep_launcher_open', 'False')):
            self.get_main_window().close()
        else:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Game process is running'))

            main_tab = self.get_main_tab()
            update_group_box = main_tab.update_group_box

            self.disable_controls()
            update_group_box.disable_controls(True)

            soundpacks_tab = main_tab.get_soundpacks_tab()
            mods_tab = main_tab.get_mods_tab()
            settings_tab = main_tab.get_settings_tab()
            backups_tab = main_tab.get_backups_tab()

            soundpacks_tab.disable_tab()
            mods_tab.disable_tab()
            settings_tab.disable_tab()
            backups_tab.disable_tab()

            self.launch_game_button.setText(_('Show current game'))
            self.launch_game_button.setEnabled(True)

            class ProcessWaitThread(QThread):
                ended = pyqtSignal()

                def __init__(self, process):
                    super(ProcessWaitThread, self).__init__()

                    self.process = process

                def __del__(self):
                    self.wait()

                def run(self):
                    self.process.wait()
                    self.ended.emit()

            def process_ended():
                self.game_ended()

            process_wait_thread = ProcessWaitThread(self.game_process)
            process_wait_thread.ended.connect(process_ended)
            process_wait_thread.start()

            self.process_wait_thread = process_wait_thread

    def game_ended(self):
        if self.process_wait_thread is not None:
            self.process_wait_thread.quit()
            self.process_wait_thread = None

        self.game_process = None
        self.game_started = False

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_bar.showMessage(_('Game process has ended'))

        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box

        soundpacks_tab = main_tab.get_soundpacks_tab()
        mods_tab = main_tab.get_mods_tab()
        settings_tab = main_tab.get_settings_tab()
        backups_tab = main_tab.get_backups_tab()

        self.enable_controls()
        update_group_box.enable_controls()

        soundpacks_tab.enable_tab()
        mods_tab.enable_tab()
        settings_tab.enable_tab()
        backups_tab.enable_tab()

        self.launch_game_button.setText(_('Launch game'))

        self.get_main_window().setWindowState(Qt.WindowActive)

        self.update_saves()

        if config_true(get_config_value('backup_on_end', 'False')):
            backups_tab.prune_auto_backups()

            name = '{auto}_{name}'.format(auto=_('auto'),
                name=_('after_end'))

            backups_tab.backup_saves(name)

    def get_main_tab(self):
        return self.parentWidget()

    def get_main_window(self):
        return self.get_main_tab().get_main_window()

    def update_soundpacks(self):
        main_window = self.get_main_window()
        central_widget = main_window.central_widget
        soundpacks_tab = central_widget.soundpacks_tab

        directory = self.dir_combo.currentText()
        soundpacks_tab.game_dir_changed(directory)

    def update_mods(self):
        main_window = self.get_main_window()
        central_widget = main_window.central_widget
        mods_tab = central_widget.mods_tab

        directory = self.dir_combo.currentText()
        mods_tab.game_dir_changed(directory)

    def update_backups(self):
        main_window = self.get_main_window()
        central_widget = main_window.central_widget
        backups_tab = central_widget.backups_tab

        directory = self.dir_combo.currentText()
        backups_tab.game_dir_changed(directory)

    def clear_soundpacks(self):
        main_window = self.get_main_window()
        central_widget = main_window.central_widget
        soundpacks_tab = central_widget.soundpacks_tab

        soundpacks_tab.clear_soundpacks()

    def clear_mods(self):
        main_window = self.get_main_window()
        central_widget = main_window.central_widget
        mods_tab = central_widget.mods_tab

        mods_tab.clear_mods()

    def clear_backups(self):
        main_window = self.get_main_window()
        central_widget = main_window.central_widget
        backups_tab = central_widget.backups_tab

        backups_tab.clear_backups()

    def set_game_directory(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self,
                _('Game directory'), self.dir_combo.currentText(),
                options=options)
        if directory:
            self.set_dir_combo_value(clean_qt_path(directory))

    def dc_index_changed(self, index):
        if self.shown and not self.dir_combo_inserting:
            self.game_directory_changed()

    def game_directory_changed(self):
        directory = self.dir_combo.currentText()

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        self.exe_path = None

        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box

        if not os.path.isdir(directory):
            self.version_value_label.setText(_('Not a valid directory'))
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
                version_type = _('console')
                exe_path = console_exe
            elif os.path.isfile(tiles_exe):
                version_type = _('tiles')
                exe_path = tiles_exe

            if version_type is None:
                self.version_value_label.setText(_('Not a CDDA directory'))
            else:
                self.exe_path = exe_path
                self.version_type = version_type
                if self.last_game_directory != directory:
                    self.update_version()
                    self.update_saves()
                    self.update_soundpacks()
                    self.update_mods()
                    self.update_backups()

        if self.exe_path is None:
            self.launch_game_button.setEnabled(False)
            update_group_box.update_button.setText(_('Install game'))
            self.restored_previous = False

            self.current_build = None
            self.build_value_label.setText(_('Unknown'))
            self.saves_value_edit.setText(_('Unknown'))
            self.clear_soundpacks()
            self.clear_mods()
            self.clear_backups()
        else:
            self.launch_game_button.setEnabled(True)
            update_group_box.update_button.setText(_('Update game'))

            self.check_running_process(self.exe_path)

        self.last_game_directory = directory
        if not (getattr(sys, 'frozen', False)
            and config_true(get_config_value('use_launcher_dir', 'False'))):
            set_config_value('game_directory', directory)

    @property
    def app_locale(self):
        return QApplication.instance().app_locale

    def update_version(self):
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        if (self.exe_reading_timer is not None
            and self.exe_reading_timer.isActive()):
            self.exe_reading_timer.stop()

            status_bar = main_window.statusBar()
            status_bar.removeWidget(self.reading_label)
            status_bar.removeWidget(self.reading_progress_bar)

            status_bar.busy -= 1

        status_bar.clearMessage()
        status_bar.busy += 1

        reading_label = QLabel()
        reading_label.setText(_('Reading: {0}').format(self.exe_path))
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
            bytes = self.opened_exe.read(cons.READ_BUFFER_SIZE)
            if len(bytes) == 0:
                self.opened_exe.close()
                self.exe_reading_timer.stop()
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                if self.game_version == '':
                    self.game_version = _('Unknown')
                else:
                    self.add_game_dir()

                self.version_value_label.setText(
                    _('{version} ({type})').format(version=self.game_version,
                    type=self.version_type))

                status_bar.removeWidget(self.reading_label)
                status_bar.removeWidget(self.reading_progress_bar)

                status_bar.busy -= 1
                if status_bar.busy == 0 and not self.game_started:
                    if self.restored_previous:
                        status_bar.showMessage(
                            _('Previous version restored'))
                    else:
                        status_bar.showMessage(_('Ready'))

                if status_bar.busy == 0 and self.game_started:
                    status_bar.showMessage(_('Game process is running'))

                sha256 = self.exe_sha256.hexdigest()

                new_version(self.game_version, sha256)

                build = get_build_from_sha256(sha256)

                if build is not None:
                    build_date = arrow.get(build['released_on'], 'UTC')
                    human_delta = build_date.humanize(arrow.utcnow(),
                        locale=self.app_locale)
                    self.build_value_label.setText(_('{build} ({time_delta})'
                        ).format(build=build['build'], time_delta=human_delta))
                    self.current_build = build['build']

                    main_tab = self.get_main_tab()
                    update_group_box = main_tab.update_group_box

                    if (update_group_box.builds is not None
                        and len(update_group_box.builds) > 0
                        and status_bar.busy == 0
                        and not self.game_started):
                        last_build = update_group_box.builds[0]

                        message = status_bar.currentMessage()
                        if message != '':
                            message = message + ' - '

                        if last_build['number'] == self.current_build:
                            message = message + _('Your game is up to date')
                        else:
                            message = message + _('There is a new update '
                            'available')
                        status_bar.showMessage(message)

                else:
                    self.build_value_label.setText(_('Unknown'))
                    self.current_build = None

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

    def check_running_process(self, exe_path):
        pid = process_id_from_path(exe_path)

        if pid is not None:
            self.game_started = True
            self.game_process_id = pid

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            if status_bar.busy == 0:
                status_bar.showMessage(_('Game process is running'))

            main_tab = self.get_main_tab()
            update_group_box = main_tab.update_group_box

            self.disable_controls()
            update_group_box.disable_controls(True)

            soundpacks_tab = main_tab.get_soundpacks_tab()
            mods_tab = main_tab.get_mods_tab()
            settings_tab = main_tab.get_settings_tab()
            backups_tab = main_tab.get_backups_tab()

            soundpacks_tab.disable_tab()
            mods_tab.disable_tab()
            settings_tab.disable_tab()
            backups_tab.disable_tab()

            self.launch_game_button.setText(_('Show current game'))
            self.launch_game_button.setEnabled(True)

            class ProcessWaitThread(QThread):
                ended = pyqtSignal()

                def __init__(self, pid):
                    super(ProcessWaitThread, self).__init__()

                    self.pid = pid

                def __del__(self):
                    self.wait()

                def run(self):
                    wait_for_pid(self.pid)
                    self.ended.emit()

            def process_ended():
                self.process_wait_thread = None

                self.game_process_id = None
                self.game_started = False

                status_bar.showMessage(_('Game process has ended'))

                self.enable_controls()
                update_group_box.enable_controls()

                soundpacks_tab.enable_tab()
                mods_tab.enable_tab()
                settings_tab.enable_tab()
                backups_tab.enable_tab()

                self.launch_game_button.setText(_('Launch game'))

                self.get_main_window().setWindowState(Qt.WindowActive)

                self.update_saves()

                if config_true(get_config_value('backup_on_end', 'False')):
                    backups_tab.prune_auto_backups()

                    name = '{auto}_{name}'.format(auto=_('auto'),
                        name=_('after_end'))

                    backups_tab.backup_saves(name)

            process_wait_thread = ProcessWaitThread(self.game_process_id)
            process_wait_thread.ended.connect(process_ended)
            process_wait_thread.start()

            self.process_wait_thread = process_wait_thread

    def add_game_dir(self):
        new_game_dir = self.dir_combo.currentText()

        game_dirs = json.loads(get_config_value('game_directories', '[]'))

        try:
            index = game_dirs.index(new_game_dir)
            if index > 0:
                del game_dirs[index]
                game_dirs.insert(0, new_game_dir)
        except ValueError:
            game_dirs.insert(0, new_game_dir)

        if len(game_dirs) > cons.MAX_GAME_DIRECTORIES:
            del game_dirs[cons.MAX_GAME_DIRECTORIES:]

        set_config_value('game_directories', json.dumps(game_dirs))

    def update_saves(self):
        self.game_dir = self.dir_combo.currentText()

        if (self.update_saves_timer is not None
            and self.update_saves_timer.isActive()):
            self.update_saves_timer.stop()
            self.saves_value_edit.setText(_('Unknown'))

        save_dir = os.path.join(self.game_dir, 'save')
        if not os.path.isdir(save_dir):
            self.saves_value_edit.setText(_('Not found'))
            return

        timer = QTimer(self)
        self.update_saves_timer = timer

        self.saves_size = 0
        self.saves_worlds = 0
        self.saves_characters = 0
        self.world_dirs = set()

        self.saves_scan = scandir(save_dir)
        self.next_scans = []
        self.save_dir = save_dir

        def timeout():
            try:
                entry = next(self.saves_scan)
                if entry.is_dir():
                    self.next_scans.append(entry.path)
                elif entry.is_file():
                    self.saves_size += entry.stat().st_size

                    if entry.name.endswith('.sav'):
                        world_dir = os.path.dirname(entry.path)
                        if self.save_dir == os.path.dirname(world_dir):
                            self.saves_characters += 1

                    if entry.name in cons.WORLD_FILES:
                        world_dir = os.path.dirname(entry.path)
                        if (world_dir not in self.world_dirs
                            and self.save_dir == os.path.dirname(world_dir)):
                            self.world_dirs.add(world_dir)
                            self.saves_worlds += 1

                worlds_text = ngettext('World', 'Worlds', self.saves_worlds)

                characters_text = ngettext('Character', 'Characters',
                    self.saves_characters)

                self.saves_value_edit.setText(_('{world_count} {worlds} - '
                    '{character_count} {characters} ({size})').format(
                    world_count=self.saves_worlds,
                    character_count=self.saves_characters,
                    size=sizeof_fmt(self.saves_size),
                    worlds=worlds_text,
                    characters=characters_text))
            except StopIteration:
                if len(self.next_scans) > 0:
                    self.saves_scan = scandir(self.next_scans.pop())
                else:
                    # End of the tree
                    self.update_saves_timer.stop()
                    self.update_saves_timer = None

                    # Warning about saves size
                    if (self.saves_size > cons.SAVES_WARNING_SIZE and
                        not config_true(get_config_value('prevent_save_move',
                            'False'))):
                        self.saves_warning_label.show()
                    else:
                        self.saves_warning_label.hide()

        timer.timeout.connect(timeout)
        timer.start(0)

    def analyse_new_build(self, build):
        game_dir = self.dir_combo.currentText()

        self.previous_exe_path = self.exe_path
        self.exe_path = None

        console_exe = os.path.join(game_dir, 'cataclysm.exe')
        tiles_exe = os.path.join(game_dir, 'cataclysm-tiles.exe')

        exe_path = None
        version_type = None
        if os.path.isfile(console_exe):
            version_type = _('console')
            exe_path = console_exe
        elif os.path.isfile(tiles_exe):
            version_type = _('tiles')
            exe_path = tiles_exe

        if version_type is None:
            self.version_value_label.setText(_('Not a CDDA directory'))
            self.build_value_label.setText(_('Unknown'))
            self.current_build = None

            main_tab = self.get_main_tab()
            update_group_box = main_tab.update_group_box
            update_group_box.finish_updating()

            self.launch_game_button.setEnabled(False)

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()
            status_bar.showMessage(_('No executable found in the downloaded '
                'archive. You might want to restore your previous version.'))

        else:
            if (self.exe_reading_timer is not None
                and self.exe_reading_timer.isActive()):
                self.exe_reading_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()
                status_bar.removeWidget(self.reading_label)
                status_bar.removeWidget(self.reading_progress_bar)

                status_bar.busy -= 1

            self.exe_path = exe_path
            self.version_type = version_type
            self.build_number = build['number']
            self.build_date = build['date']

            main_window = self.get_main_window()

            status_bar = main_window.statusBar()
            status_bar.clearMessage()

            status_bar.busy += 1

            reading_label = QLabel()
            reading_label.setText(_('Reading: {0}').format(self.exe_path))
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
                bytes = self.opened_exe.read(cons.READ_BUFFER_SIZE)
                if len(bytes) == 0:
                    self.opened_exe.close()
                    self.exe_reading_timer.stop()
                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    if self.game_version == '':
                        self.game_version = _('Unknown')
                    self.version_value_label.setText(
                        _('{version} ({type})').format(
                            version=self.game_version,
                            type=self.version_type))

                    build_date = arrow.get(self.build_date, 'UTC')
                    human_delta = build_date.humanize(arrow.utcnow(),
                        locale=self.app_locale)
                    self.build_value_label.setText(_('{build} ({time_delta})'
                        ).format(build=self.build_number,
                            time_delta=human_delta))
                    self.current_build = self.build_number

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


class ChangelogParsingThread(QThread):
    completed = pyqtSignal(StringIO)

    def __init__(self, changelog_http_data):
        super(ChangelogParsingThread, self).__init__()
        self.changelog_http_data = changelog_http_data

    def __del__(self):
        self.wait()

    def get_results_by_platform(self, build_data):
        regex = re.compile(r'.*\b'
                           r'(?P<ui>Curses|Tiles),'
                           r'(?P<plat>Linux_x64|Windows(?:_x64)?)'
                           r'\b.*')

        def platform_display_name(code_name):
            code_name = regex.sub(r'\g<ui>-\g<plat>',
                                  code_name.find('fullDisplayName').text)

            if code_name == 'Tiles-Windows': return 'Windows x86'
            if code_name == 'Tiles-Windows_x64': return 'Windows x64'
            if code_name == 'Curses-Linux_x64': return 'All Platforms'
            return None

        build_platforms = build_data.findall(r'.//run')
        build_platforms = filter(
            lambda x: x.find('result') is not None and
                      x.find('fullDisplayName') is not None and
                      regex.search(x.find('fullDisplayName').text) is not None,
            build_platforms
        )

        return tuple({'result': x.find('result').text,
                      'platform': platform_display_name(x)}
                     for x in build_platforms
                     if platform_display_name(x) is not None)

    @property
    def app_locale(self):
        return QApplication.instance().app_locale

    def run(self):
        changelog_html = StringIO()
        self.changelog_http_data.seek(0)
        try:
            changelog_xml = xml.etree.ElementTree.fromstring(
                                self.changelog_http_data.read())
        except xml.etree.ElementTree.ParseError as err:
            log_exception(*sys.exc_info())
            changelog_html.write(
                '<h3 style="color:red">{0}</h3>'.format(
                    _('Error parsing Changelog data. Retry later.')))
            self.completed.emit(changelog_html)
            return


        ### "((?<![\w#])(?=[\w#])|(?<=[\w#])(?![\w#]))" is like a \b
        ### that accepts "#" as word char too.
        ### regex used to match issues / PR IDs like "#43151"
        id_regex = re.compile(r'((?<![\w#])(?=[\w#])|(?<=[\w#])(?![\w#]))'
                              r'#(?P<id>\d+)\b')

        for build_data in changelog_xml:
            build_by_platform = self.get_results_by_platform(build_data)
            if build_data.find('building').text == 'true':
                build_status = 'IN_PROGRESS'
            elif any(x['result'] == 'FAILURE' for x in build_by_platform):
                build_status = 'FAILURE'
            else:
                ### possible "result" values: 'SUCCESS' or 'FAILURE'
                build_status = 'SUCCESS'

            build_timestamp = int(build_data.find('timestamp').text) // 1000
            build_date_utc = datetime.utcfromtimestamp(build_timestamp)
            build_date_utc = build_date_utc.replace(tzinfo=timezone.utc)
            build_date_local = build_date_utc.astimezone(tz=None)
            build_date_text = format_datetime(build_date_local,
                format='long', locale=self.app_locale)

            build_changes = build_data.findall(r'.//changeSet/item/msg')
            build_changes = map(lambda x: html.escape(x.text.strip(), True),
                                build_changes)
            build_changes = list(unique(build_changes))
            build_number = int(build_data.find('number').text)
            build_link = f'<a href="{cons.BUILD_CHANGES_URL(build_number)}">' \
                         f'Build #{build_number}</a>'

            if build_status == 'IN_PROGRESS':
                changelog_html.write(
                    '<h4>{0} - {1} <span style="color:purple">{2}</span></h4>'
                    .format(
                        build_link,
                        build_date_text,
                        _('build still in progress!')
                    )
                )
            elif build_status == 'SUCCESS':
                changelog_html.write(
                    '<h4>{0} - {1}</h4>'
                    .format(build_link, build_date_text)
                )
            else:   ### build_status == 'FAILURE'
                changelog_html.write(
                    '<h4>{0} - {1} <span style="color:red">{2} {3}</span></h4>'
                    .format(
                        build_link,
                        build_date_text,
                        _('but build failed for:'),
                        ', '.join(map(lambda x: x['platform'],
                                      filter(lambda y: y['result'] == 'FAILURE',
                                             build_by_platform)))
                    )
                )

            changelog_html.write('<ul>')
            if len(build_changes) < 1:
                changelog_html.write(
                    '<li><span style="color:green">{0}</span></li>'
                    .format(_('No changes, same code as previous build!')))
            else:
                for change in build_changes:
                    link_repl = rf'<a href="{cons.CDDA_ISSUE_URL_ROOT}\g<id>">#\g<id></a>'
                    change = id_regex.sub(link_repl, change)
                    changelog_html.write(f'<li>{change}</li>')
            changelog_html.write('</ul>')

        self.completed.emit(changelog_html)


class UpdateGroupBox(QGroupBox):
    def __init__(self):
        super(UpdateGroupBox, self).__init__()

        self.shown = False
        self.updating = False
        self.close_after_update = False
        self.builds = []
        self.progress_rmtree = None
        self.progress_copy = None

        self.qnam = QNetworkAccessManager()
        self.http_reply = None

        self.changelog_http_reply = None
        self.changelog_http_data = None

        layout = QGridLayout()

        platform_label = QLabel()
        layout.addWidget(platform_label, 0, 0, Qt.AlignRight)
        self.platform_label = platform_label

        platform_button_group = QButtonGroup()
        self.platform_button_group = platform_button_group

        x64_radio_button = QRadioButton()
        layout.addWidget(x64_radio_button, 0, 1)
        self.x64_radio_button = x64_radio_button
        platform_button_group.addButton(x64_radio_button)

        platform_button_group.buttonClicked.connect(self.platform_clicked)

        if not is_64_windows():
            x64_radio_button.setEnabled(False)

        x86_radio_button = QRadioButton()
        layout.addWidget(x86_radio_button, 0, 2)
        self.x86_radio_button = x86_radio_button
        platform_button_group.addButton(x86_radio_button)

        available_builds_label = QLabel()
        layout.addWidget(available_builds_label, 1, 0, Qt.AlignRight)
        self.available_builds_label = available_builds_label

        builds_combo = QComboBox()
        builds_combo.setEnabled(False)
        builds_combo.addItem(_('Unknown'))
        layout.addWidget(builds_combo, 1, 1, 1, 2)
        self.builds_combo = builds_combo

        refresh_warning_label = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning)
        refresh_warning_label.setPixmap(icon.pixmap(16, 16))
        refresh_warning_label.hide()
        layout.addWidget(refresh_warning_label, 1, 3)
        self.refresh_warning_label = refresh_warning_label

        refresh_builds_button = QToolButton()
        refresh_builds_button.clicked.connect(self.refresh_builds)
        layout.addWidget(refresh_builds_button, 1, 4)
        self.refresh_builds_button = refresh_builds_button

        changelog_groupbox = QGroupBox()
        changelog_layout = QHBoxLayout()
        changelog_groupbox.setLayout(changelog_layout)
        layout.addWidget(changelog_groupbox, 2, 0, 1, 5)
        self.changelog_groupbox = changelog_groupbox
        self.changelog_layout = changelog_layout

        changelog_content = QTextBrowser()
        changelog_content.setReadOnly(True)
        changelog_content.setOpenExternalLinks(True)
        self.changelog_layout.addWidget(changelog_content)
        self.changelog_content = changelog_content

        update_button = QPushButton()
        update_button.setEnabled(False)
        update_button.setStyleSheet('font-size: 20px;')
        update_button.clicked.connect(self.update_game)
        layout.addWidget(update_button, 3, 0, 1, 5)
        self.update_button = update_button

        layout.setColumnStretch(1, 100)
        layout.setColumnStretch(2, 100)

        self.setLayout(layout)
        self.set_text()

    def set_text(self):
        self.platform_label.setText(_('Platform:'))
        self.x64_radio_button.setText(_('Windows x64 (64-bit)'))
        self.x86_radio_button.setText(_('Windows x86 (32-bit)'))
        self.available_builds_label.setText(_('Available builds:'))
        self.refresh_builds_button.setText(_('Refresh'))
        self.changelog_groupbox.setTitle(_('Changelog'))
        self.update_button.setText(_('Update game'))
        self.setTitle(_('Update/Installation'))

    def showEvent(self, event):
        if not self.shown:
            platform = get_config_value('platform')

            if platform == 'Windows x64':
                platform = 'x64'
            elif platform == 'Windows x86':
                platform = 'x86'

            if platform is None or platform not in ('x64', 'x86'):
                if is_64_windows():
                    platform = 'x64'
                else:
                    platform = 'x86'

            if platform == 'x64':
                self.x64_radio_button.setChecked(True)
            elif platform == 'x86':
                self.x86_radio_button.setChecked(True)

            self.start_lb_request(cons.BASE_ASSETS['Tiles'][platform])
            self.refresh_changelog()

        self.shown = True

    def update_game(self):
        if not self.updating:
            if self.builds is None or len(self.builds) < 1:
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(_('Cannot update or install the game '
                    'since no build was found'))
                return

            main_tab = self.get_main_tab()
            game_dir_group_box = main_tab.game_dir_group_box
            game_dir = game_dir_group_box.dir_combo.currentText()

            # Check if we are installing in an empty directory
            if (game_dir_group_box.exe_path is None and
                os.path.exists(game_dir) and
                os.path.isdir(game_dir)):

                current_scan = scandir(game_dir)
                game_dir_empty = True

                try:
                    next(current_scan)
                    game_dir_empty = False
                except StopIteration:
                    pass

                if not game_dir_empty:
                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    status_bar.showMessage(_('Cannot install the game if the '
                        'game directory is not empty'))
                    return

            self.updating = True
            self.download_aborted = False
            self.clearing_previous_dir = False
            self.backing_up_game = False
            self.extracting_new_build = False
            self.analysing_new_build = False
            self.in_post_extraction = False

            self.selected_build = self.builds[self.builds_combo.currentIndex()]

            latest_build = self.builds[0]
            if game_dir_group_box.current_build == latest_build['number']:
                confirm_msgbox = QMessageBox()
                confirm_msgbox.setWindowTitle(_('Game is up to date'))
                confirm_msgbox.setText(_('You already have the latest version.'
                    ))
                confirm_msgbox.setInformativeText(_('Are you sure you want to '
                    'update your game?'))
                confirm_msgbox.addButton(_('Update the game again'),
                    QMessageBox.YesRole)
                confirm_msgbox.addButton(_('I do not need to update the '
                    'game again'), QMessageBox.NoRole)
                confirm_msgbox.setIcon(QMessageBox.Question)

                if confirm_msgbox.exec() == 1:
                    self.updating = False
                    return

            game_dir_group_box.disable_controls()
            self.disable_controls()

            soundpacks_tab = main_tab.get_soundpacks_tab()
            mods_tab = main_tab.get_mods_tab()
            settings_tab = main_tab.get_settings_tab()
            backups_tab = main_tab.get_backups_tab()

            soundpacks_tab.disable_tab()
            mods_tab.disable_tab()
            settings_tab.disable_tab()
            backups_tab.disable_tab()

            try:
                if not os.path.exists(game_dir):
                    os.makedirs(game_dir)
                elif os.path.isfile(game_dir):
                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    status_bar.showMessage(_('Cannot install game on a file'))

                    self.finish_updating()
                    return

                download_dir = tempfile.mkdtemp(prefix=cons.TEMP_PREFIX)

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

                self.finish_updating()

                status_bar.showMessage(str(e))
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
                        status_bar.showMessage(_('Update cancelled'))
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Installation cancelled'))
            elif self.clearing_previous_dir:
                if self.progress_rmtree is not None:
                    self.progress_rmtree.stop()
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
                        status_bar.showMessage(_('Update cancelled'))
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Installation cancelled'))

            elif self.extracting_new_build:
                self.extracting_timer.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.removeWidget(self.extracting_label)
                status_bar.removeWidget(self.extracting_progress_bar)

                status_bar.busy -= 1

                self.extracting_zipfile.close()

                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)

                path = self.clean_game_dir()
                self.restore_backup()
                self.restore_previous_content(path)

                if path is not None:
                    delete_path(path)

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Update cancelled'))
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Installation cancelled'))
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

                if path is not None:
                    delete_path(path)

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Update cancelled'))
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Installation cancelled'))
            elif self.in_post_extraction:
                self.in_post_extraction = False

                if self.progress_copy is not None:
                    self.progress_copy.stop()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()
                status_bar.clearMessage()

                path = self.clean_game_dir()
                self.restore_backup()
                self.restore_previous_content(path)

                if path is not None:
                    delete_path(path)

                if game_dir_group_box.exe_path is not None:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Update cancelled'))
                else:
                    if status_bar.busy == 0:
                        status_bar.showMessage(_('Installation cancelled'))

            self.finish_updating()

    def clean_game_dir(self):
        game_dir = self.game_dir
        dir_list = os.listdir(game_dir)
        if len(dir_list) == 0 or (
            len(dir_list) == 1 and dir_list[0] == 'previous_version'):
            return None

        temp_move_dir = tempfile.mkdtemp(prefix=cons.TEMP_PREFIX)

        excluded_entries = set(['previous_version'])
        if config_true(get_config_value('prevent_save_move', 'False')):
            excluded_entries.add('save')
        # Prevent moving the launcher if it's in the game directory
        if getattr(sys, 'frozen', False):
            launcher_exe = os.path.abspath(sys.executable)
            launcher_dir = os.path.dirname(launcher_exe)
            if os.path.abspath(game_dir) == launcher_dir:
                excluded_entries.add(os.path.basename(launcher_exe))
        for entry in dir_list:
            if entry not in excluded_entries:
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
                    config_true(get_config_value('prevent_save_move',
                        'False'))):
                    continue
                entry_path = os.path.join(previous_version_dir, entry)
                shutil.move(entry_path, game_dir)

            delete_path(previous_version_dir)

    def get_main_tab(self):
        return self.parentWidget()

    def get_main_window(self):
        return self.get_main_tab().get_main_window()

    def disable_controls(self, update_button=False):
        self.x64_radio_button.setEnabled(False)
        self.x86_radio_button.setEnabled(False)

        self.previous_bc_enabled = self.builds_combo.isEnabled()
        self.builds_combo.setEnabled(False)
        self.refresh_builds_button.setEnabled(False)

        self.previous_ub_enabled = self.update_button.isEnabled()
        if update_button:
            self.update_button.setEnabled(False)

    def enable_controls(self, builds_combo=False, update_button=False):
        if is_64_windows():
            self.x64_radio_button.setEnabled(True)
        self.x86_radio_button.setEnabled(True)

        self.refresh_builds_button.setEnabled(True)

        if builds_combo:
            self.builds_combo.setEnabled(True)
        else:
            self.builds_combo.setEnabled(self.previous_bc_enabled)

        if update_button:
            self.update_button.setEnabled(True)
        else:
            self.update_button.setEnabled(self.previous_ub_enabled)

    def download_game_update(self, url):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        status_bar.busy += 1

        downloading_label = QLabel()
        downloading_label.setText(_('Downloading: {0}').format(url))
        status_bar.addWidget(downloading_label, 100)
        self.downloading_label = downloading_label

        dowloading_speed_label = QLabel()
        status_bar.addWidget(dowloading_speed_label)
        self.dowloading_speed_label = dowloading_speed_label

        downloading_size_label = QLabel()
        status_bar.addWidget(downloading_size_label)
        self.downloading_size_label = downloading_size_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.downloading_progress_bar = progress_bar
        progress_bar.setMinimum(0)

        self.download_last_read = datetime.utcnow()
        self.download_last_bytes_read = 0
        self.download_speed_count = 0

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent',
            b'CDDA-Game-Launcher/' + version.encode('utf8'))

        self.download_http_reply = self.qnam.get(request)
        self.download_http_reply.finished.connect(self.download_http_finished)
        self.download_http_reply.readyRead.connect(
            self.download_http_ready_read)
        self.download_http_reply.downloadProgress.connect(
            self.download_dl_progress)

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        if game_dir_group_box.exe_path is not None:
            self.update_button.setText(_('Cancel update'))
        else:
            self.update_button.setText(_('Cancel installation'))

    def download_http_finished(self):
        self.downloading_file.close()

        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.removeWidget(self.downloading_label)
        status_bar.removeWidget(self.dowloading_speed_label)
        status_bar.removeWidget(self.downloading_size_label)
        status_bar.removeWidget(self.downloading_progress_bar)

        status_bar.busy -= 1

        if self.download_aborted:
            download_dir = os.path.dirname(self.downloaded_file)
            delete_path(download_dir)
        else:
            redirect = self.download_http_reply.attribute(
                QNetworkRequest.RedirectionTargetAttribute)
            if redirect is not None:
                redirected_url = urljoin(
                    self.download_http_reply.request().url().toString(),
                    redirect.toString())

                downloading_label = QLabel()
                downloading_label.setText(_('Downloading: {0}').format(
                    redirected_url))
                status_bar.addWidget(downloading_label, 100)
                self.downloading_label = downloading_label

                dowloading_speed_label = QLabel()
                status_bar.addWidget(dowloading_speed_label)
                self.dowloading_speed_label = dowloading_speed_label

                downloading_size_label = QLabel()
                status_bar.addWidget(downloading_size_label)
                self.downloading_size_label = downloading_size_label

                progress_bar = QProgressBar()
                status_bar.addWidget(progress_bar)
                self.downloading_progress_bar = progress_bar
                progress_bar.setMinimum(0)

                self.download_last_read = datetime.utcnow()
                self.download_last_bytes_read = 0
                self.download_speed_count = 0

                request = QNetworkRequest(QUrl(redirected_url))
                request.setRawHeader(b'User-Agent',
                    b'CDDA-Game-Launcher/' + version.encode('utf8'))

                self.downloading_file = open(self.downloaded_file, 'wb')

                self.download_http_reply = self.qnam.get(request)
                self.download_http_reply.finished.connect(
                    self.download_http_finished)
                self.download_http_reply.readyRead.connect(
                    self.download_http_ready_read)
                self.download_http_reply.downloadProgress.connect(
                    self.download_dl_progress)

                return

            # Test downloaded file
            status_bar.showMessage(_('Testing downloaded file archive'))

            class TestingZipThread(QThread):
                completed = pyqtSignal()
                invalid = pyqtSignal()
                not_downloaded = pyqtSignal()

                def __init__(self, downloaded_file):
                    super(TestingZipThread, self).__init__()

                    self.downloaded_file = downloaded_file

                def __del__(self):
                    self.wait()

                def run(self):
                    try:
                        with zipfile.ZipFile(self.downloaded_file) as z:
                            if z.testzip() is not None:
                                self.invalid.emit()
                                return
                    except zipfile.BadZipFile:
                        self.not_downloaded.emit()
                        return

                    self.completed.emit()

            def completed_test():
                self.test_thread = None

                status_bar.clearMessage()
                self.clear_previous_dir()

            def invalid():
                self.test_thread = None

                status_bar.clearMessage()
                status_bar.showMessage(_('Downloaded archive is invalid'))

                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)
                self.finish_updating()

            def not_downloaded():
                self.test_thread = None

                status_bar.clearMessage()
                status_bar.showMessage(_('Could not download game'))

                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)
                self.finish_updating()

            test_thread = TestingZipThread(self.downloaded_file)
            test_thread.completed.connect(completed_test)
            test_thread.invalid.connect(invalid)
            test_thread.not_downloaded.connect(not_downloaded)
            test_thread.start()

            self.test_thread = test_thread

    def clear_previous_dir(self):
        self.clearing_previous_dir = True

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        game_dir = game_dir_group_box.dir_combo.currentText()
        self.game_dir = game_dir

        backup_dir = os.path.join(game_dir, 'previous_version')
        if os.path.isdir(backup_dir):
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Deleting {name}').format(
                name=_('previous_version directory')))

            if delete_path(backup_dir):
                self.backup_current_game()
            else:
                status_bar.showMessage(_('Update cancelled - Could not delete '
                'the {name}.').format(name=_('previous_version directory')))
                self.finish_updating()
        else:
            self.backup_current_game()

    def backup_current_game(self):
        self.clearing_previous_dir = False
        self.progress_rmtree = None

        self.backing_up_game = True

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        game_dir = game_dir_group_box.dir_combo.currentText()
        self.game_dir = game_dir

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        backup_dir = os.path.join(game_dir, 'previous_version')

        dir_list = os.listdir(game_dir)
        self.backup_dir_list = dir_list

        if (config_true(get_config_value('prevent_save_move', 'False'))
            and 'save' in dir_list):
            dir_list.remove('save')

        if getattr(sys, 'frozen', False):
            launcher_exe = os.path.abspath(sys.executable)
            launcher_dir = os.path.dirname(launcher_exe)
            if os.path.abspath(game_dir) == launcher_dir:
                launcher_name = os.path.basename(launcher_exe)
                if launcher_name in dir_list:
                    dir_list.remove(launcher_name)

        if len(dir_list) > 0:
            status_bar.showMessage(_('Backing up current game'))

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
            self.backup_current_display = True

            def timeout():
                self.backup_progress_bar.setValue(self.backup_index)

                if self.backup_index == len(self.backup_dir_list):
                    self.backup_timer.stop()

                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    status_bar.removeWidget(self.backup_label)
                    status_bar.removeWidget(self.backup_progress_bar)

                    status_bar.busy -= 1
                    status_bar.clearMessage()

                    self.backing_up_game = False
                    self.extract_new_build()

                else:
                    backup_element = self.backup_dir_list[self.backup_index]

                    if self.backup_current_display:
                        self.backup_label.setText(_('Backing up {0}').format(
                            backup_element))
                        self.backup_current_display = False
                    else:
                        srcpath = os.path.join(self.game_dir, backup_element)
                        if not move_path(srcpath, self.backup_dir):
                            self.backup_timer.stop()

                            main_window = self.get_main_window()
                            status_bar = main_window.statusBar()

                            status_bar.removeWidget(self.backup_label)
                            status_bar.removeWidget(self.backup_progress_bar)

                            status_bar.busy -= 1
                            status_bar.clearMessage()

                            self.finish_updating()

                            msg = (_('Could not move {srcpath} in {dstpath} .')
                                ).format(
                                    srcpath=srcpath,
                                    dstpath=self.backup_dir
                                )

                            status_bar.showMessage(msg)

                        self.backup_index += 1
                        self.backup_current_display = True

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

                # Keep a copy of the archive if selected in the settings
                if config_true(get_config_value('keep_archive_copy', 'False')):
                    archive_dir = get_config_value('archive_directory', '')
                    archive_name = os.path.basename(self.downloaded_file)
                    move_target = os.path.join(archive_dir, archive_name)
                    if (os.path.isdir(archive_dir)
                        and not os.path.exists(move_target)):
                        shutil.move(self.downloaded_file, archive_dir)

                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)

                main_tab = self.get_main_tab()
                game_dir_group_box = main_tab.game_dir_group_box

                self.analysing_new_build = True
                game_dir_group_box.analyse_new_build(self.selected_build)

            else:
                extracting_element = self.extracting_infolist[
                    self.extracting_index]
                self.extracting_label.setText(_('Extracting {0}').format(
                    extracting_element.filename))

                try:
                    self.extracting_zipfile.extract(extracting_element,
                        self.game_dir)
                except OSError as e:
                    # Display the error and stop the update process
                    error_msgbox = QMessageBox()
                    error_msgbox.setWindowTitle(
                        _('Cannot extract game archive'))

                    text = _('''
<p>The launcher failed to extract the game archive.</p>
<p>It received the following error from the operating system: {error}</p>'''
                        ).format(error=html.escape(e.strerror))

                    error_msgbox.setText(text)
                    error_msgbox.addButton(_('OK'), QMessageBox.YesRole)
                    error_msgbox.setIcon(QMessageBox.Critical)

                    error_msgbox.exec()

                    self.update_game()

                self.extracting_index += 1

        timer.timeout.connect(timeout)
        timer.start(0)

    def asset_name(self, path, filename):
        asset_file = os.path.join(path, filename)

        if not os.path.isfile(asset_file):
            disabled_asset_file = os.path.join(path, filename + '.disabled')
            if not os.path.isfile(disabled_asset_file):
                return None
            else:
                asset_file_path = disabled_asset_file
        else:
            asset_file_path = asset_file

        try:
            with open(asset_file_path, 'r', encoding='latin1') as f:
                for line in f:
                    if line.startswith('NAME'):
                        space_index = line.find(' ')
                        name = line[space_index:].strip().replace(
                            ',', '')
                        return name
        except FileNotFoundError:
            return None
        return None

    def mod_ident(self, path):
        json_file = os.path.join(path, 'modinfo.json')
        if not os.path.isfile(json_file):
            json_file = os.path.join(path, 'modinfo.json.disabled')
        if os.path.isfile(json_file):
            try:
                with open(json_file, 'r', encoding='utf8') as f:
                    try:
                        values = json.load(f)
                        if isinstance(values, dict):
                            if values.get('type', '') == 'MOD_INFO':
                                return values.get('ident', None)
                        elif isinstance(values, list):
                            for item in values:
                                if (isinstance(item, dict)
                                    and item.get('type', '') == 'MOD_INFO'):
                                        return item.get('ident', None)
                    except ValueError:
                        pass
            except FileNotFoundError:
                return None

        return None

    def copy_next_dir(self):
        if self.in_post_extraction and len(self.previous_dirs) > 0:
            next_dir = self.previous_dirs.pop()
            src_path = os.path.join(self.previous_version_dir, next_dir)
            dst_path = os.path.join(self.game_dir, next_dir)
            if os.path.isdir(src_path) and not os.path.exists(dst_path):
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                progress_copy = ProgressCopyTree(src_path, dst_path,
                    self.previous_dirs_skips, status_bar,
                    _('{0} directory').format(next_dir))
                progress_copy.completed.connect(self.copy_next_dir)
                self.progress_copy = progress_copy
                progress_copy.start()
            else:
                self.copy_next_dir()
        elif self.in_post_extraction:
            self.progress_copy = None
            self.post_extraction_step2()

    def post_extraction(self):
        self.analysing_new_build = False
        self.in_post_extraction = True

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        # Copy config, save, templates and memorial directory from previous
        # version
        previous_version_dir = os.path.join(self.game_dir, 'previous_version')
        if os.path.isdir(previous_version_dir) and self.in_post_extraction:

            previous_dirs = ['config', 'save', 'templates', 'memorial',
                'graveyard', 'save_backups']
            if (config_true(get_config_value('prevent_save_move', 'False')) and
                'save' in previous_dirs):
                previous_dirs.remove('save')

            self.previous_dirs = previous_dirs
            self.previous_version_dir = previous_version_dir

            # Skip debug files
            self.previous_dirs_skips = set()
            self.previous_dirs_skips.update((
                 os.path.join(previous_version_dir, 'config', 'debug.log'),
                 os.path.join(previous_version_dir, 'config', 'debug.log.prev')
            ))

            self.progress_copy = None
            self.copy_next_dir()
        elif self.in_post_extraction:
            # New install
            self.in_post_extraction = False
            self.finish_updating()

    def post_extraction_step2(self):
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        # Copy custom tilesets and soundpack from previous version
        # tilesets
        tilesets_dir = os.path.join(self.game_dir, 'gfx')
        previous_tilesets_dir = os.path.join(self.game_dir, 'previous_version',
            'gfx')

        if (os.path.isdir(tilesets_dir) and os.path.isdir(previous_tilesets_dir)
            and self.in_post_extraction):
            status_bar.showMessage(_('Restoring custom tilesets'))

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
            status_bar.showMessage(_('Restoring custom soundpacks'))

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
            if len(custom_set) > 0:
                self.soundpack_dir = soundpack_dir
                self.previous_soundpack_set = previous_set
                self.custom_soundpacks = list(custom_set)

                self.copy_next_soundpack()
            else:
                status_bar.clearMessage()
                self.post_extraction_step3()

        else:
            self.post_extraction_step3()

    def copy_next_soundpack(self):
        if self.in_post_extraction and len(self.custom_soundpacks) > 0:
            next_item = self.custom_soundpacks.pop()
            dst_path = os.path.join(self.soundpack_dir, os.path.basename(
                self.previous_soundpack_set[next_item]))
            src_path = self.previous_soundpack_set[next_item]
            if os.path.isdir(src_path) and not os.path.exists(dst_path):
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                progress_copy = ProgressCopyTree(src_path, dst_path, None,
                    status_bar, _('{name} soundpack').format(name=next_item))
                progress_copy.completed.connect(self.copy_next_soundpack)
                self.progress_copy = progress_copy
                progress_copy.start()
            else:
                self.copy_next_soundpack()
        elif self.in_post_extraction:
            self.progress_copy = None

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()
            status_bar.clearMessage()

            self.post_extraction_step3()

    def post_extraction_step3(self):
        if not self.in_post_extraction:
            return

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        # Copy custom mods from previous version
        # mods
        mods_dir = os.path.join(self.game_dir, 'data', 'mods')
        previous_mods_dir = os.path.join(self.game_dir, 'previous_version',
            'data', 'mods')

        if (os.path.isdir(mods_dir) and os.path.isdir(previous_mods_dir) and
            self.in_post_extraction):
            status_bar.showMessage(_('Restoring custom mods'))

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

        # user mods
        user_mods_dir = os.path.join(self.game_dir, 'mods')
        previous_user_mods_dir = os.path.join(self.game_dir, 'previous_version',
            'mods')

        if (os.path.isdir(previous_user_mods_dir) and self.in_post_extraction):
            status_bar.showMessage(_('Restoring user custom mods'))

            if not os.path.exists(user_mods_dir):
                os.makedirs(user_mods_dir)

            official_set = {}
            for entry in os.listdir(user_mods_dir):
                entry_path = os.path.join(user_mods_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.mod_ident(entry_path)
                    if name is not None and name not in official_set:
                        official_set[name] = entry_path
            previous_set = {}
            for entry in os.listdir(previous_user_mods_dir):
                entry_path = os.path.join(previous_user_mods_dir, entry)
                if os.path.isdir(entry_path):
                    name = self.mod_ident(entry_path)
                    if name is not None and name not in previous_set:
                        previous_set[name] = entry_path

            custom_set = set(previous_set.keys()) - set(official_set.keys())
            for item in custom_set:
                target_dir = os.path.join(user_mods_dir, os.path.basename(
                    previous_set[item]))
                if not os.path.exists(target_dir):
                    shutil.copytree(previous_set[item], target_dir)

            status_bar.clearMessage()

        if not self.in_post_extraction:
            return

        # Copy user-default-mods.json if present
        user_default_mods_file = os.path.join(mods_dir,
            'user-default-mods.json')
        previous_user_default_mods_file = os.path.join(previous_mods_dir,
            'user-default-mods.json')

        if (not os.path.exists(user_default_mods_file)
            and os.path.isfile(previous_user_default_mods_file)):
            status_bar.showMessage(_('Restoring user-default-mods.json'))

            shutil.copy2(previous_user_default_mods_file,
                user_default_mods_file)

            status_bar.clearMessage()

        # Copy custom fonts
        fonts_dir = os.path.join(self.game_dir, 'data', 'font')
        previous_fonts_dir = os.path.join(self.game_dir, 'previous_version',
            'data', 'font')

        if (os.path.isdir(fonts_dir) and os.path.isdir(previous_fonts_dir) and
            self.in_post_extraction):
            status_bar.showMessage(_('Restoring custom fonts'))

            official_set = set(os.listdir(fonts_dir))
            previous_set = set(os.listdir(previous_fonts_dir))

            custom_set = previous_set - official_set
            for entry in custom_set:
                source = os.path.join(previous_fonts_dir, entry)
                target = os.path.join(fonts_dir, entry)
                if os.path.isfile(source):
                    shutil.copy2(source, target)
                elif os.path.isdir(source):
                    shutil.copytree(source, target)

            status_bar.clearMessage()

        if not self.in_post_extraction:
            return

        self.in_post_extraction = False

        if config_true(get_config_value('remove_previous_version', 'False')):
            self.remove_previous_version()
        else:
            self.after_updating_message()
            self.finish_updating()

    def remove_previous_version(self):
        previous_version_dir = os.path.join(self.game_dir, 'previous_version')

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        progress_rmtree = ProgressRmTree(previous_version_dir, status_bar,
            _('previous_version directory'))

        def rmtree_completed():
            self.progress_rmtree = None

            self.after_updating_message()
            self.finish_updating()

        progress_rmtree.completed.connect(rmtree_completed)
        progress_rmtree.aborted.connect(rmtree_completed)
        self.progress_rmtree = progress_rmtree
        progress_rmtree.start()

    def after_updating_message(self):
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        if game_dir_group_box.previous_exe_path is not None:
            status_bar.showMessage(_('Update completed'))
        else:
            status_bar.showMessage(_('Installation completed'))

        if (game_dir_group_box.current_build is not None
            and status_bar.busy == 0):
            last_build = self.builds[0]

            message = status_bar.currentMessage()
            if message != '':
                message = message + ' - '

            if last_build['number'] == game_dir_group_box.current_build:
                message = message + _('Your game is up to date')
            else:
                message = message + _('There is a new update available')
            status_bar.showMessage(message)

    def finish_updating(self):
        self.updating = False
        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        game_dir_group_box.enable_controls()
        self.enable_controls(True)

        game_dir_group_box.update_soundpacks()
        game_dir_group_box.update_mods()
        game_dir_group_box.update_backups()

        soundpacks_tab = main_tab.get_soundpacks_tab()
        mods_tab = main_tab.get_mods_tab()
        settings_tab = main_tab.get_settings_tab()
        backups_tab = main_tab.get_backups_tab()

        soundpacks_tab.enable_tab()
        mods_tab.enable_tab()
        settings_tab.enable_tab()
        backups_tab.enable_tab()

        if game_dir_group_box.exe_path is not None:
            self.update_button.setText(_('Update game'))
        else:
            self.update_button.setText(_('Install game'))

        if self.close_after_update:
            self.get_main_window().close()

    def download_http_ready_read(self):
        self.downloading_file.write(self.download_http_reply.readAll())

    def download_dl_progress(self, bytes_read, total_bytes):
        self.downloading_progress_bar.setMaximum(total_bytes)
        self.downloading_progress_bar.setValue(bytes_read)

        self.download_speed_count += 1

        self.downloading_size_label.setText(_('{bytes_read}/{total_bytes}'
            ).format(bytes_read=sizeof_fmt(bytes_read),
                total_bytes=sizeof_fmt(total_bytes)))

        if self.download_speed_count % 5 == 0:
            delta_bytes = bytes_read - self.download_last_bytes_read
            delta_time = datetime.utcnow() - self.download_last_read

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.dowloading_speed_label.setText(_('{bytes_sec}/s').format(
                bytes_sec=sizeof_fmt(bytes_secs)))

            self.download_last_bytes_read = bytes_read
            self.download_last_read = datetime.utcnow()

    def start_lb_request(self, base_asset):
        self.disable_controls(True)
        self.refresh_warning_label.hide()

        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        status_bar.busy += 1

        self.builds_combo.clear()
        self.builds_combo.addItem(_('Fetching remote builds'))

        url = cons.GITHUB_REST_API_URL + cons.CDDA_RELEASES
        self.base_asset = base_asset

        fetching_label = QLabel()
        fetching_label.setText(_('Fetching: {url}').format(url=url))
        self.base_url = url
        status_bar.addWidget(fetching_label, 100)
        self.fetching_label = fetching_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.fetching_progress_bar = progress_bar

        progress_bar.setMinimum(0)

        self.lb_html = BytesIO()

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent',
            b'CDDA-Game-Launcher/' + version.encode('utf8'))
        request.setRawHeader(b'Accept', cons.GITHUB_API_VERSION)

        self.http_reply = self.qnam.get(request)
        self.http_reply.finished.connect(self.lb_http_finished)
        self.http_reply.readyRead.connect(self.lb_http_ready_read)
        self.http_reply.downloadProgress.connect(self.lb_dl_progress)

    @property
    def app_locale(self):
        return QApplication.instance().app_locale

    def lb_http_finished(self):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.removeWidget(self.fetching_label)
        status_bar.removeWidget(self.fetching_progress_bar)

        redirect = self.http_reply.attribute(
            QNetworkRequest.RedirectionTargetAttribute)
        if redirect is not None:
            redirected_url = urljoin(
                self.http_reply.request().url().toString(),
                redirect.toString())

            fetching_label = QLabel()
            fetching_label.setText(_('Fetching: {url}').format(
                url=redirected_url))
            self.base_url = redirected_url
            status_bar.addWidget(fetching_label, 100)
            self.fetching_label = fetching_label

            progress_bar = QProgressBar()
            status_bar.addWidget(progress_bar)
            self.fetching_progress_bar = progress_bar

            progress_bar.setMinimum(0)

            self.lb_html = BytesIO()

            request = QNetworkRequest(QUrl(redirected_url))
            request.setRawHeader(b'User-Agent',
                b'CDDA-Game-Launcher/' + version.encode('utf8'))
            request.setRawHeader(b'Accept', cons.GITHUB_API_VERSION)

            self.http_reply = self.qnam.get(request)
            self.http_reply.finished.connect(self.lb_http_finished)
            self.http_reply.readyRead.connect(self.lb_http_ready_read)
            self.http_reply.downloadProgress.connect(self.lb_dl_progress)
            return

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        status_bar.busy -= 1

        if not game_dir_group_box.game_started:
            if status_bar.busy == 0:
                status_bar.showMessage(_('Ready'))

            self.enable_controls()
        else:
            if status_bar.busy == 0:
                status_bar.showMessage(_('Game process is running'))

        requests_remaining = None
        if self.http_reply.hasRawHeader(cons.GITHUB_XRL_REMAINING):
            requests_remaining = self.http_reply.rawHeader(cons.GITHUB_XRL_REMAINING)
            requests_remaining = tryint(requests_remaining)

        reset_dt = None
        if self.http_reply.hasRawHeader(cons.GITHUB_XRL_RESET):
            reset_dt = self.http_reply.rawHeader(cons.GITHUB_XRL_RESET)
            reset_dt = tryint(reset_dt)
            reset_dt = arrow.get(reset_dt)

        if requests_remaining is not None and requests_remaining <= 10:
            # Warn about remaining requests on GitHub API
            reset_dt_display = _('Unknown')
            if reset_dt is not None:
                reset_dt_local = reset_dt.astimezone(tz=None)
                reset_dt_display = format_datetime(reset_dt_local,
                    format='long', locale=self.app_locale)

            self.refresh_warning_label.show()
            self.refresh_warning_label.setToolTip(_('You have {remaining} '
            'request(s) remaining for accessing GitHub API.\nYou will have to '
            'wait until {datetime} to get more requests.\nThose requests are '
            'needed to get the available builds.\nIf you keep running low on '
            'those remaining requests, avoid quickly refreshing often\n for the'
            'available builds. For more information, search GitHub API rate '
            'limiting.').format(
                remaining=requests_remaining,
                datetime=reset_dt_display
            ))

        status_code = self.http_reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            reason = self.http_reply.attribute(
                QNetworkRequest.HttpReasonPhraseAttribute)
            url = self.http_reply.request().url().toString()
            msg = _('Could not find remote builds [HTTP {status_code}] '
                '({reason}) when requesting {url}').format(
                    status_code=status_code,
                    reason=reason,
                    url=url
                )
            if status_bar.busy == 0:
                status_bar.showMessage(msg)
            logger.warning(msg)

            self.builds = None

            self.builds_combo.clear()
            self.builds_combo.addItem(msg)
            self.builds_combo.setEnabled(False)

            self.lb_html = None
            return

        self.lb_html.seek(0)
        try:
            releases = json.loads(TextIOWrapper(self.lb_html, encoding='utf8'
                ).read())
        except json.decoder.JSONDecodeError:
            releases = []
        self.lb_html = None

        builds = []

        asset_platform = self.base_asset['Platform']
        asset_graphics = self.base_asset['Graphics']

        target_regex = re.compile(r'cataclysmdda-(?P<major>.+)-' +
            re.escape(asset_platform) + r'-' +
            re.escape(asset_graphics) + r'-' +
            r'(?P<build>\d+)\.zip'
            )

        build_regex = re.compile(r'build #(?P<build>\d+)')

        for release in releases:
            if any(x not in release for x in ('name', 'created_at')):
                continue

            build_match = build_regex.search(release['name'])
            if build_match is not None:
                asset = None
                if 'assets' in release:
                    asset_iter = (
                        x for x in release['assets']
                        if 'browser_download_url' in x
                           and 'name' in x
                           and target_regex.search(x['name']) is not None
                    )
                    asset = next(asset_iter, None)

                build = {
                    'url': asset['browser_download_url'] if asset is not None
                                                         else None,
                    'name': asset['name'] if asset is not None else None,
                    'number': build_match.group('build'),
                    'date': arrow.get(release['created_at']).datetime
                }
                builds.append(build)

        if len(builds) > 0:
            builds.sort(key=lambda x: (x['number'], x['date']), reverse=True)
            self.builds = builds

            self.builds_combo.clear()
            for index, build in enumerate(builds):
                if build['date'] is not None:
                    build_date = arrow.get(build['date'], 'UTC')
                    human_delta = build_date.humanize(arrow.utcnow(),
                        locale=self.app_locale)
                else:
                    human_delta = _('Unknown')

                self.builds_combo.addItem(
                    _('{number} ({delta})').format(
                    number=build['number'], delta=human_delta),
                    userData=build)

            combo_model = self.builds_combo.model()
            default_set = False
            for x in range(combo_model.rowCount()):
                if combo_model.item(x).data(Qt.UserRole)['url'] is None:
                    combo_model.item(x).setEnabled(False)
                    combo_model.item(x).setText(combo_model.item(x).text() +
                        _(' - build unavailable'))
                elif not default_set:
                    default_set = True
                    self.builds_combo.setCurrentIndex(x)
                    combo_model.item(x).setText(combo_model.item(x).text() +
                        _(' - latest build available'))


            if not game_dir_group_box.game_started:
                self.builds_combo.setEnabled(True)
                self.update_button.setEnabled(True)
            else:
                self.previous_bc_enabled = True
                self.previous_ub_enabled = True

            if game_dir_group_box.exe_path is not None:
                self.update_button.setText(_('Update game'))

                if (game_dir_group_box.current_build is not None
                    and status_bar.busy == 0
                    and not game_dir_group_box.game_started):
                    last_build = self.builds[0]

                    message = status_bar.currentMessage()
                    if message != '':
                        message = message + ' - '

                    if last_build['number'] == game_dir_group_box.current_build:
                        message = message + _('Your game is up to date')
                    else:
                        message = message + _('There is a new update available')
                    status_bar.showMessage(message)
            else:
                self.update_button.setText(_('Install game'))

        else:
            self.builds = None

            self.builds_combo.clear()
            self.builds_combo.addItem(_('Could not find remote builds'))
            self.builds_combo.setEnabled(False)

    def lb_http_ready_read(self):
        self.lb_html.write(self.http_reply.readAll())

    def lb_dl_progress(self, bytes_read, total_bytes):
        self.fetching_progress_bar.setMaximum(total_bytes)
        self.fetching_progress_bar.setValue(bytes_read)

    def refresh_builds(self):
        selected_platform = self.platform_button_group.checkedButton()

        if selected_platform is self.x64_radio_button:
            selected_platform = 'x64'
        elif selected_platform is self.x86_radio_button:
            selected_platform = 'x86'

        release_asset = cons.BASE_ASSETS['Tiles'][selected_platform]

        self.start_lb_request(release_asset)
        self.refresh_changelog()

    def refresh_changelog(self):
        if self.changelog_http_reply is not None:
            self.changelog_http_data = None
            self.changelog_http_reply.abort()
            self.changelog_http_reply = None

        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()
        self.changelog_content.setHtml(_('<h3>Loading changelog...</h3>'))

        status_bar.busy += 1

        changelog_label = QLabel()
        changelog_label.setText(_('Fetching latest build changelogs'))
        status_bar.addWidget(changelog_label, 100)
        self.changelog_label = changelog_label

        progress_bar = QProgressBar()
        status_bar.addWidget(progress_bar)
        self.changelog_progress_bar = progress_bar

        progress_bar.setMinimum(0)

        self.changelog_http_data = BytesIO()

        request = QNetworkRequest(QUrl(cons.CHANGELOG_URL))
        request.setRawHeader(b'User-Agent',
            b'CDDA-Game-Launcher/' + version.encode('utf8'))

        self.changelog_http_reply = self.qnam.get(request)
        self.changelog_http_reply.finished.connect(self.changelog_http_finished)
        self.changelog_http_reply.readyRead.connect(
            self.changelog_http_ready_read)
        self.changelog_http_reply.downloadProgress.connect(
            self.changelog_dl_progress)

    def changelog_http_finished(self):
        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.removeWidget(self.changelog_label)
        status_bar.removeWidget(self.changelog_progress_bar)

        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box

        status_bar.busy -= 1

        if not game_dir_group_box.game_started:
            if status_bar.busy == 0:
                status_bar.showMessage(_('Ready'))
        else:
            if status_bar.busy == 0:
                status_bar.showMessage(_('Game process is running'))

        if self.changelog_http_data is not None:
            self.changelog_content.setHtml(_('<h3>Parsing changelog...</h3>'))

            # Use thread to avoid blocking UI during parsing
            parsing_thread = ChangelogParsingThread(self.changelog_http_data)
            parsing_thread.completed.connect(
                lambda x: self.changelog_content.setHtml(x.getvalue()))
            parsing_thread.start()

        self.changelog_http_data = None
        self.changelog_http_reply = None

    def changelog_http_ready_read(self):
        self.changelog_http_data.write(self.changelog_http_reply.readAll())

    def changelog_dl_progress(self, bytes_read, total_bytes):
        if total_bytes == -1:
            total_bytes = bytes_read * 2
        self.changelog_progress_bar.setMaximum(total_bytes)
        self.changelog_progress_bar.setValue(bytes_read)

    def platform_clicked(self, button):
        if button is self.x64_radio_button:
            config_value = 'x64'
        elif button is self.x86_radio_button:
            config_value = 'x86'

        set_config_value('platform', config_value)

        self.refresh_builds()


class AboutDialog(QDialog):
    def __init__(self, parent=0, f=0):
        super(AboutDialog, self).__init__(parent, f)

        layout = QGridLayout()

        text_content = QTextBrowser()
        text_content.setReadOnly(True)
        text_content.setOpenExternalLinks(True)

        text_content.setSearchPaths([get_resource_path()])
        layout.addWidget(text_content, 0, 0)
        self.text_content = text_content

        ok_button = QPushButton()
        ok_button.clicked.connect(self.done)
        layout.addWidget(ok_button, 1, 0, Qt.AlignRight)
        self.ok_button = ok_button

        layout.setRowStretch(0, 100)

        self.setMinimumSize(640, 450)

        self.setLayout(layout)
        self.set_text()

    def set_text(self):
        self.setWindowTitle(_('About CDDA Game Launcher'))
        self.ok_button.setText(_('OK'))
        self.text_content.setHtml(_('''
<p>CDDA Game Launcher version {version}</p>

<p>Get the latest release <a
href="https://github.com/remyroy/CDDA-Game-Launcher/releases">on GitHub</a>.</p>

<p>Please report any issue <a
href="https://github.com/remyroy/CDDA-Game-Launcher/issues/new">on GitHub</a>.
</p>

<p>If you like the CDDA Game Launcher, you can buy me a beer by donating
bitcoins to <a href="bitcoin:3N2BRM61bZLuFRHjSj2Lhtw6DrwPUGeTvV">
3N2BRM61bZLuFRHjSj2Lhtw6DrwPUGeTvV</a> <img src="btc-qr.png"> or by donating
ethers to <a href="https://etherscan.io/address/0xdb731476e913d75061a78105c3d1b5a7a03aa21b">
0xDb731476e913d75061A78105C3D1b5A7a03Aa21B</a>
<img src="eth-qr.png">.</p>

<p>Thanks to the following people for their efforts in translating the CDDA Game
Launcher</p>
<ul>
<li>Russian: Daniel from <a href="http://cataclysmdda.ru/">cataclysmdda.ru</a>
and Night_Pryanik</li>
<li>Italian: Rettiliano Verace from <a
href="http://emigrantebestemmiante.blogspot.com">Emigrante Bestemmiante</a></li>
<li>French: Rémy Roy</li>
</ul>

<p>Thanks to <a href="http://mattahan.deviantart.com/">Paul Davey aka
Mattahan</a> for the permission to use his artwork for the launcher icon.</p>

<p>Copyright (c) 2015-2019 Rémy Roy</p>

<p>Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:</p>

<p>The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.</p>

<p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.</p>

''').format(version=version))


class LauncherUpdateDialog(QDialog):
    def __init__(self, url, version, parent=0, f=0):
        super(LauncherUpdateDialog, self).__init__(parent, f)

        self.updated = False
        self.url = url

        layout = QGridLayout()

        self.shown = False
        self.qnam = QNetworkAccessManager()
        self.http_reply = None

        progress_label = QLabel()
        progress_label.setText(_('Progress:'))
        layout.addWidget(progress_label, 0, 0, Qt.AlignRight)
        self.progress_label = progress_label

        progress_bar = QProgressBar()
        layout.addWidget(progress_bar, 0, 1)
        self.progress_bar = progress_bar

        url_label = QLabel()
        url_label.setText(_('Url:'))
        layout.addWidget(url_label, 1, 0, Qt.AlignRight)
        self.url_label = url_label

        url_lineedit = QLineEdit()
        url_lineedit.setText(url)
        url_lineedit.setReadOnly(True)
        layout.addWidget(url_lineedit, 1, 1)
        self.url_lineedit = url_lineedit

        size_label = QLabel()
        size_label.setText(_('Size:'))
        layout.addWidget(size_label, 2, 0, Qt.AlignRight)
        self.size_label = size_label

        size_value_label = QLabel()
        layout.addWidget(size_value_label, 2, 1)
        self.size_value_label = size_value_label

        speed_label = QLabel()
        speed_label.setText(_('Speed:'))
        layout.addWidget(speed_label, 3, 0, Qt.AlignRight)
        self.speed_label = speed_label

        speed_value_label = QLabel()
        layout.addWidget(speed_value_label, 3, 1)
        self.speed_value_label = speed_value_label

        cancel_button = QPushButton()
        cancel_button.setText(_('Cancel update'))
        cancel_button.setStyleSheet('font-size: 15px;')
        cancel_button.clicked.connect(self.cancel_update)
        layout.addWidget(cancel_button, 4, 0, 1, 2)
        self.cancel_button = cancel_button

        layout.setColumnStretch(1, 100)

        self.setLayout(layout)
        self.setMinimumSize(300, 0)
        self.setWindowTitle(_('CDDA Game Launcher self-update'))

    def showEvent(self, event):
        if not self.shown:
            temp_dl_dir = tempfile.mkdtemp(prefix=cons.TEMP_PREFIX)

            exe_name = os.path.basename(sys.executable)

            self.downloaded_file = os.path.join(temp_dl_dir, exe_name)
            self.downloading_file = open(self.downloaded_file, 'wb')

            self.download_last_read = datetime.utcnow()
            self.download_last_bytes_read = 0
            self.download_speed_count = 0
            self.download_aborted = False

            self.http_reply = self.qnam.get(QNetworkRequest(QUrl(self.url)))
            self.http_reply.finished.connect(self.http_finished)
            self.http_reply.readyRead.connect(self.http_ready_read)
            self.http_reply.downloadProgress.connect(self.dl_progress)

        self.shown = True

    def closeEvent(self, event):
        self.cancel_update(True)

    def http_finished(self):
        self.downloading_file.close()

        if self.download_aborted:
            download_dir = os.path.dirname(self.downloaded_file)
            delete_path(download_dir)
        else:
            redirect = self.http_reply.attribute(
                QNetworkRequest.RedirectionTargetAttribute)
            if redirect is not None:
                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)
                os.makedirs(download_dir)

                redirected_url = urljoin(
                    self.http_reply.request().url().toString(),
                    redirect.toString())

                self.downloading_file = open(self.downloaded_file, 'wb')

                self.download_last_read = datetime.utcnow()
                self.download_last_bytes_read = 0
                self.download_speed_count = 0
                self.download_aborted = False

                self.progress_bar.setValue(0)

                self.http_reply = self.qnam.get(QNetworkRequest(QUrl(
                    redirected_url)))
                self.http_reply.finished.connect(self.http_finished)
                self.http_reply.readyRead.connect(self.http_ready_read)
                self.http_reply.downloadProgress.connect(self.dl_progress)
            else:
                # Download completed
                if getattr(sys, 'frozen', False):
                    # Launch self.downloaded_file and close

                    subprocess.Popen([self.downloaded_file])

                    self.updated = True
                    self.done(0)

    def http_ready_read(self):
        self.downloading_file.write(self.http_reply.readAll())

    def dl_progress(self, bytes_read, total_bytes):
        self.progress_bar.setMaximum(total_bytes)
        self.progress_bar.setValue(bytes_read)

        self.download_speed_count += 1

        self.size_value_label.setText(_('{bytes_read}/{total_bytes}').format(
            bytes_read=sizeof_fmt(bytes_read),
            total_bytes=sizeof_fmt(total_bytes)))

        if self.download_speed_count % 5 == 0:
            delta_bytes = bytes_read - self.download_last_bytes_read
            delta_time = datetime.utcnow() - self.download_last_read

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.speed_value_label.setText(_('{bytes_sec}/s').format(
                bytes_sec=sizeof_fmt(bytes_secs)))

            self.download_last_bytes_read = bytes_read
            self.download_last_read = datetime.utcnow()

    def cancel_update(self, from_close=False):
        if self.http_reply.isRunning():
            self.download_aborted = True
            self.http_reply.abort()

        if not from_close:
            self.close()


class BackupsTab(QTabWidget):
    def __init__(self):
        super(BackupsTab, self).__init__()

        self.game_dir = None
        self.update_backups_timer = None
        self.after_backup = None
        self.after_update_backups = None

        self.extracting_backup = False
        self.manual_backup = False
        self.backup_searching = False
        self.backup_compressing = False

        self.compressing_timer = None

        current_backups_gb = QGroupBox()
        self.current_backups_gb = current_backups_gb

        current_backups_gb_layout = QGridLayout()
        current_backups_gb.setLayout(current_backups_gb_layout)
        self.current_backups_gb_layout = current_backups_gb_layout

        backups_table = QTableWidget()
        backups_table.setColumnCount(8)
        backups_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        backups_table.setSelectionMode(QAbstractItemView.SingleSelection)
        backups_table.verticalHeader().setVisible(False)
        backups_table.horizontalHeader().sortIndicatorChanged.connect(
            self.backups_table_header_sort)
        backups_table.itemSelectionChanged.connect(
            self.backups_table_selection_changed)
        current_backups_gb_layout.addWidget(backups_table, 0, 0, 1, 3)
        self.backups_table = backups_table

        columns_width = get_config_value('backups_columns_width', None)
        if columns_width is not None:
            columns_width = json.loads(columns_width)

            for index, value in enumerate(columns_width):
                if index < self.backups_table.columnCount():
                    self.backups_table.setColumnWidth(index, value)

        restore_button = QPushButton()
        restore_button.clicked.connect(self.restore_button_clicked)
        restore_button.setEnabled(False)
        current_backups_gb_layout.addWidget(restore_button, 1, 0)
        self.restore_button = restore_button

        refresh_list_button = QPushButton()
        refresh_list_button.setEnabled(False)
        refresh_list_button.clicked.connect(self.refresh_list_button_clicked)
        current_backups_gb_layout.addWidget(refresh_list_button, 1, 1)
        self.refresh_list_button = refresh_list_button

        delete_button = QPushButton()
        delete_button.clicked.connect(self.delete_button_clicked)
        delete_button.setEnabled(False)
        current_backups_gb_layout.addWidget(delete_button, 1, 2)
        self.delete_button = delete_button

        do_not_backup_previous_cb = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'do_not_backup_previous', 'False')) else Qt.Unchecked)
        do_not_backup_previous_cb.setCheckState(check_state)
        do_not_backup_previous_cb.stateChanged.connect(self.dnbp_changed)
        current_backups_gb_layout.addWidget(do_not_backup_previous_cb, 2, 0, 1,
            3)
        self.do_not_backup_previous_cb = do_not_backup_previous_cb

        manual_backups_gb = QGroupBox()
        self.manual_backups_gb = manual_backups_gb

        manual_backups_layout = QGridLayout()
        manual_backups_gb.setLayout(manual_backups_layout)
        self.manual_backups_layout = manual_backups_layout

        name_label = QLabel()
        manual_backups_layout.addWidget(name_label, 0, 0, Qt.AlignRight)
        self.name_label = name_label

        name_le = QLineEdit()
        name_le.setText(get_config_value('last_manual_backup_name', ''))
        manual_backups_layout.addWidget(name_le, 0, 1)
        self.name_le = name_le

        backup_current_button = QPushButton()
        backup_current_button.setEnabled(False)
        backup_current_button.clicked.connect(self.backup_current_clicked)
        manual_backups_layout.addWidget(backup_current_button, 1, 0, 1, 2)
        self.backup_current_button = backup_current_button

        automatic_backups_gb = QGroupBox()
        automatic_backups_layout = QGridLayout()
        automatic_backups_gb.setLayout(automatic_backups_layout)
        self.automatic_backups_layout = automatic_backups_layout
        self.automatic_backups_gb = automatic_backups_gb

        backup_on_launch_cb = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'backup_on_launch', 'False')) else Qt.Unchecked)
        backup_on_launch_cb.setCheckState(check_state)
        backup_on_launch_cb.stateChanged.connect(self.bol_changed)
        automatic_backups_layout.addWidget(backup_on_launch_cb, 0, 0)
        self.backup_on_launch_cb = backup_on_launch_cb

        backup_on_end_cb = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'backup_on_end', 'False')) else Qt.Unchecked)
        backup_on_end_cb.setCheckState(check_state)
        backup_on_end_cb.stateChanged.connect(self.boe_changed)
        automatic_backups_layout.addWidget(backup_on_end_cb, 1, 0)
        self.backup_on_end_cb = backup_on_end_cb

        backup_on_end = check_state
        keep_launcher_open = config_true(get_config_value('keep_launcher_open',
            'False'))

        backup_on_end_warning_label = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning)
        backup_on_end_warning_label.setPixmap(icon.pixmap(16, 16))
        if not (backup_on_end and not keep_launcher_open):
            backup_on_end_warning_label.hide()
        automatic_backups_layout.addWidget(backup_on_end_warning_label, 1, 1)
        self.backup_on_end_warning_label = backup_on_end_warning_label

        mab_group = QWidget()
        mab_group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        mab_layout = QHBoxLayout()
        mab_layout.setContentsMargins(0, 0, 0, 0)

        max_auto_backups_label = QLabel()
        mab_layout.addWidget(max_auto_backups_label)
        self.max_auto_backups_label = max_auto_backups_label

        max_auto_backups_spinbox = QSpinBox()
        max_auto_backups_spinbox.setMinimum(1)
        max_auto_backups_spinbox.setMaximum(1000)
        max_auto_backups_spinbox.setValue(int(get_config_value(
            'max_auto_backups', '6')))
        max_auto_backups_spinbox.valueChanged.connect(self.mabs_changed)
        mab_layout.addWidget(max_auto_backups_spinbox)
        self.max_auto_backups_spinbox = max_auto_backups_spinbox

        mab_group.setLayout(mab_layout)
        automatic_backups_layout.addWidget(mab_group, 2, 0, 1, 2)
        self.mab_group = mab_group
        self.mab_layout = mab_layout

        layout = QGridLayout()
        layout.addWidget(current_backups_gb, 0, 0, 1, 2)
        layout.addWidget(manual_backups_gb, 1, 0)
        layout.addWidget(automatic_backups_gb, 1, 1)
        self.setLayout(layout)

        self.set_text()

    def set_text(self):
        self.current_backups_gb.setTitle(_('Backups available'))
        self.manual_backups_gb.setTitle(_('Manual backup'))
        self.automatic_backups_gb.setTitle(_('Automatic backups'))

        self.restore_button.setText(_('Restore backup'))
        self.refresh_list_button.setText(_('Refresh list'))
        self.delete_button.setText(_('Delete backup'))
        self.do_not_backup_previous_cb.setText(_('Do not backup the current '
            'saves before restoring a backup'))
        self.backups_table.setHorizontalHeaderLabels((_('Name'),
            _('Modified'), _('Worlds'), _('Characters'), _('Actual size'),
            _('Compressed size'), _('Compression ratio'), _('Modified date')))

        self.name_label.setText(_('Name:'))
        self.backup_current_button.setText(_('Backup current saves'))

        self.backup_on_launch_cb.setText(_('Backup saves before game launch'))
        self.backup_on_end_cb.setText(_('Backup saves after game end'))

        self.backup_on_end_warning_label.setToolTip(_('This option will only '
            'work if you also have the option to keep the launcher opened '
            'after launching the game in the settings tab.'))

        self.max_auto_backups_label.setText(_('Maximum automatic backups '
            'count:'))

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab

    def get_soundpacks_tab(self):
        return self.get_main_tab().get_soundpacks_tab()

    def get_settings_tab(self):
        return self.get_main_tab().get_settings_tab()

    def get_mods_tab(self):
        return self.get_main_tab().get_mods_tab()

    def get_backups_tab(self):
        return self.get_main_tab().get_backups_tab()

    def disable_tab(self):
        self.backups_table.setEnabled(False)
        self.restore_button.setEnabled(False)
        self.refresh_list_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.backup_current_button.setEnabled(False)

    def enable_tab(self):
        self.backups_table.setEnabled(True)

        if (self.game_dir is not None and os.path.isdir(
            os.path.join(self.game_dir, 'save_backups'))):
            self.refresh_list_button.setEnabled(True)

        if (self.game_dir is not None and os.path.isdir(
            os.path.join(self.game_dir, 'save'))):
            self.backup_current_button.setEnabled(True)

        selection_model = self.backups_table.selectionModel()
        if not (selection_model is None or not selection_model.hasSelection()):
            self.restore_button.setEnabled(True)
            self.delete_button.setEnabled(True)

    def save_geometry(self):
        columns_width = []

        for index in range(self.backups_table.columnCount()):
            columns_width.append(self.backups_table.columnWidth(index))

        set_config_value('backups_columns_width', json.dumps(columns_width))

    def mabs_changed(self, value):
        set_config_value('max_auto_backups', value)

    def dnbp_changed(self, state):
        set_config_value('do_not_backup_previous', str(state != Qt.Unchecked))

    def bol_changed(self, state):
        set_config_value('backup_on_launch', str(state != Qt.Unchecked))

    def boe_changed(self, state):
        checked = state != Qt.Unchecked

        set_config_value('backup_on_end', str(checked))

        keep_launcher_open = config_true(get_config_value('keep_launcher_open',
            'False'))

        if not (checked and not keep_launcher_open):
            self.backup_on_end_warning_label.hide()
        else:
            self.backup_on_end_warning_label.show()

    def restore_button_clicked(self):
        class WaitingThread(QThread):
            completed = pyqtSignal()

            def __init__(self, wthread):
                super(WaitingThread, self).__init__()

                self.wthread = wthread

            def __del__(self):
                self.wait()

            def run(self):
                self.wthread.wait()
                self.completed.emit()

        if self.backup_searching:
            if (self.compressing_timer is not None and
                self.compressing_timer.isActive()):
                self.compressing_timer.stop()

            self.backup_searching = False

            self.finish_backup_saves()

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Restore backup cancelled'))

            self.restore_button.setText(_('Restore backup'))

        elif self.backup_compressing:
            if self.compress_thread is not None:
                self.backup_current_button.setEnabled(False)
                self.compress_thread.quit()

                def completed():
                    self.finish_backup_saves()
                    delete_path(self.backup_path)
                    self.compress_thread = None

                waiting_thread = WaitingThread(self.compress_thread)
                waiting_thread.completed.connect(completed)
                self.waiting_thread = waiting_thread

                waiting_thread.start()
            else:
                self.finish_backup_saves()
                delete_path(self.backup_path)
                self.compress_thread = None

            self.backup_compressing = False

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Restore backup cancelled'))

            self.restore_button.setText(_('Restore backup'))
        elif self.extracting_backup:
            if self.extracting_thread is not None:
                self.restore_button.setEnabled(False)
                self.extracting_thread.quit()

                def completed():
                    save_dir = os.path.join(self.game_dir, 'save')
                    delete_path(save_dir)
                    if self.temp_save_dir is not None:
                        retry_rename(self.temp_save_dir, save_dir)
                    self.temp_save_dir = None

                    self.finish_restore_backup()
                    self.extracting_thread = None

                waiting_thread = WaitingThread(self.extracting_thread)
                waiting_thread.completed.connect(completed)
                self.waiting_thread = waiting_thread

                waiting_thread.start()
            else:
                self.finish_restore_backup()
                self.extracting_thread = None

            self.extracting_backup = False

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Restore backup cancelled'))
        else:
            selection_model = self.backups_table.selectionModel()
            if selection_model is None or not selection_model.hasSelection():
                return

            selected = selection_model.currentIndex()
            table_item = self.backups_table.item(selected.row(), 0)
            selected_info = self.backups[table_item]

            if not os.path.isfile(selected_info['path']):
                return

            backup_previous = not config_true(get_config_value(
                'do_not_backup_previous', 'False'))

            if backup_previous:
                '''
                If restoring the before_last_restore, we rename it to make sure
                we make a proper backup first.
                '''
                model = selection_model.model()
                backup_name = model.data(model.index(selected.row(), 0))

                before_last_restore_name = _('before_last_restore')

                if backup_name.lower() == before_last_restore_name.lower():
                    backup_dir = os.path.join(self.game_dir, 'save_backups')

                    name_lower = backup_name.lower()
                    name_key = alphanum_key(name_lower)
                    max_counter = 1

                    for entry in scandir(backup_dir):
                        filename, ext = os.path.splitext(entry.name)
                        if ext.lower() == '.zip':
                            filename_lower = filename.lower()

                            filename_key = alphanum_key(filename_lower)

                            counter = filename_key[-1:][0]
                            if len(filename_key) > 1 and isinstance(counter,
                                int):
                                filename_key = filename_key[:-1]

                                if name_key == filename_key:
                                    max_counter = max(max_counter, counter)

                    new_backup_name = (before_last_restore_name +
                        str(max_counter + 1))
                    new_backup_path = os.path.join(backup_dir,
                        new_backup_name + '.zip')

                    if not retry_rename(selected_info['path'], new_backup_path):
                        return

                    selected_info['path'] = new_backup_path

                def next_step():
                    self.restore_backup()

                self.after_backup = next_step

                self.backup_saves(before_last_restore_name, True)

                self.restore_button.setEnabled(True)
                self.restore_button.setText(_('Cancel restore backup'))
            else:
                self.restore_backup()

    def restore_backup(self):
        selection_model = self.backups_table.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            return

        selected = selection_model.currentIndex()
        table_item = self.backups_table.item(selected.row(), 0)
        selected_info = self.backups[table_item]

        model = selection_model.model()
        backup_name = model.data(model.index(selected.row(), 0))

        if not os.path.isfile(selected_info['path']):
            return

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        self.temp_save_dir = None
        save_dir = os.path.join(self.game_dir, 'save')
        if os.path.isdir(save_dir):
            temp_save_dir = os.path.join(self.game_dir, 'save-{0}'.format(
                '%08x' % random.randrange(16**8)))
            while os.path.exists(temp_save_dir):
                temp_save_dir = os.path.join(self.game_dir, 'save-{0}'.format(
                    '%08x' % random.randrange(16**8)))

            if not retry_rename(save_dir, temp_save_dir):
                status_bar.showMessage(_('Could not rename the save directory'))
                return
            self.temp_save_dir = temp_save_dir
        elif os.path.isfile(save_dir):
            if not delete_path(save_dir):
                status_bar.showMessage(_('Could not remove the save file'))
                return

        # Extract the backup archive

        self.extracting_backup = True

        self.extract_dir = self.game_dir

        status_bar.clearMessage()
        status_bar.busy += 1

        self.total_extract_size = selected_info['actual_size']

        extracting_label = QLabel()
        extracting_label.setText(_('Extracting backup'))
        status_bar.addWidget(extracting_label, 100)
        self.extracting_label = extracting_label

        extracting_speed_label = QLabel()
        extracting_speed_label.setText(_('{bytes_sec}/s'
            ).format(bytes_sec=sizeof_fmt(0)))
        status_bar.addWidget(extracting_speed_label)
        self.extracting_speed_label = extracting_speed_label

        extracting_size_label = QLabel()
        extracting_size_label.setText(
            _('{bytes_read}/{total_bytes}').format(
            bytes_read=sizeof_fmt(0),
            total_bytes=sizeof_fmt(self.total_extract_size)))
        status_bar.addWidget(extracting_size_label)
        self.extracting_size_label = (
            extracting_size_label)

        progress_bar = QProgressBar()
        progress_bar.setRange(0, self.total_extract_size)
        progress_bar.setValue(0)
        status_bar.addWidget(progress_bar)
        self.extracting_progress_bar = progress_bar

        self.extract_size = 0
        self.extract_files = 0
        self.last_extract_bytes = 0
        self.last_extract = datetime.utcnow()
        self.next_backup_file = None

        self.disable_tab()
        self.get_main_tab().disable_tab()
        self.get_soundpacks_tab().disable_tab()
        self.get_settings_tab().disable_tab()
        self.get_mods_tab().disable_tab()
        self.get_backups_tab().disable_tab()

        self.restore_button.setEnabled(True)
        self.restore_button.setText(_('Cancel restore backup'))

        class ExtractingThread(QThread):
            completed = pyqtSignal()

            def __init__(self, zfile, element, dir):
                super(ExtractingThread, self).__init__()

                self.zfile = zfile
                self.element = element
                self.dir = dir

            def __del__(self):
                self.wait()

            def run(self):
                self.zfile.extract(self.element, self.dir)
                self.completed.emit()

        def extract_next_file():
            try:
                if self.extracting_backup:
                    extracting_element = self.extracting_infolist.popleft()
                    self.extracting_label.setText(_('Extracting {filename}'
                        ).format(filename=extracting_element.filename))
                    self.next_extract_file = extracting_element

                    extracting_thread = ExtractingThread(
                        self.extracting_zipfile, extracting_element,
                        self.extract_dir)
                    extracting_thread.completed.connect(completed_extract)
                    self.extracting_thread = extracting_thread

                    extracting_thread.start()

            except IndexError:
                self.extracting_backup = False
                self.extracting_thread = None

                self.finish_restore_backup()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(_('{backup_name} backup restored'
                    ).format(backup_name=backup_name))

        def completed_extract():
            self.extract_size += self.next_extract_file.file_size
            self.extracting_progress_bar.setValue(self.extract_size)

            self.extracting_size_label.setText(
                _('{bytes_read}/{total_bytes}').format(
                bytes_read=sizeof_fmt(self.extract_size),
                total_bytes=sizeof_fmt(self.total_extract_size)))

            delta_bytes = self.extract_size - self.last_extract_bytes
            delta_time = datetime.utcnow() - self.last_extract
            if delta_time.total_seconds() == 0:
                delta_time = timedelta.resolution

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.extracting_speed_label.setText(_('{bytes_sec}/s'
                ).format(bytes_sec=sizeof_fmt(bytes_secs)))

            self.last_extract_bytes = self.extract_size
            self.last_extract = datetime.utcnow()

            extract_next_file()

        self.extracting_zipfile = zipfile.ZipFile(selected_info['path'])
        self.extracting_infolist = deque(self.extracting_zipfile.infolist())
        extract_next_file()

    def finish_restore_backup(self):
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_bar.removeWidget(self.extracting_label)
        status_bar.removeWidget(self.extracting_speed_label)
        status_bar.removeWidget(self.extracting_size_label)
        status_bar.removeWidget(self.extracting_progress_bar)

        status_bar.busy -= 1

        self.extracting_backup = False

        if self.extracting_zipfile is not None:
            self.extracting_zipfile.close()

        if self.temp_save_dir is not None:
            delete_path(self.temp_save_dir)

        self.enable_tab()
        self.get_main_tab().enable_tab()
        self.get_soundpacks_tab().enable_tab()
        self.get_settings_tab().enable_tab()
        self.get_mods_tab().enable_tab()
        self.get_backups_tab().enable_tab()

        self.restore_button.setText(_('Restore backup'))

        self.get_main_tab().game_dir_group_box.update_saves()

    def refresh_list_button_clicked(self):
        self.update_backups_table()

    def delete_button_clicked(self):
        selection_model = self.backups_table.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            return

        selected = selection_model.currentIndex()
        table_item = self.backups_table.item(selected.row(), 0)
        selected_info = self.backups[table_item]

        if not os.path.isfile(selected_info['path']):
            return

        confirm_msgbox = QMessageBox()
        confirm_msgbox.setWindowTitle(_('Delete backup'))
        confirm_msgbox.setText(_('This will delete the backup file. It '
            'cannot be undone.'))
        confirm_msgbox.setInformativeText(_('Are you sure you want to '
            'delete the <strong>{filename}</strong> backup?').format(
            filename=selected_info['path']))
        confirm_msgbox.addButton(_('Delete the backup'),
            QMessageBox.YesRole)
        confirm_msgbox.addButton(_('I want to keep the backup'),
            QMessageBox.NoRole)
        confirm_msgbox.setIcon(QMessageBox.Warning)

        if confirm_msgbox.exec() == 0:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            if not delete_path(selected_info['path']):
                status_bar.showMessage(_('Backup deletion cancelled'))
            else:
                self.backups_table.removeRow(selected.row())
                del self.backups[table_item]

                status_bar.showMessage(_('Backup deleted'))

    def backup_current_clicked(self):
        if self.manual_backup and self.backup_searching:
            if (self.compressing_timer is not None and
                self.compressing_timer.isActive()):
                self.compressing_timer.stop()

            self.backup_searching = False

            self.finish_backup_saves()

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Manual backup cancelled'))

        elif self.manual_backup and self.backup_compressing:
            class WaitingThread(QThread):
                completed = pyqtSignal()

                def __init__(self, wthread):
                    super(WaitingThread, self).__init__()

                    self.wthread = wthread

                def __del__(self):
                    self.wait()

                def run(self):
                    self.wthread.wait()
                    self.completed.emit()

            if self.compress_thread is not None:
                self.backup_current_button.setEnabled(False)
                self.compress_thread.quit()

                def completed():
                    self.finish_backup_saves()
                    delete_path(self.backup_path)
                    self.compress_thread = None

                waiting_thread = WaitingThread(self.compress_thread)
                waiting_thread.completed.connect(completed)
                self.waiting_thread = waiting_thread

                waiting_thread.start()
            else:
                self.finish_backup_saves()
                delete_path(self.backup_path)
                self.compress_thread = None

            self.backup_compressing = False

            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            status_bar.showMessage(_('Manual backup cancelled'))
        else:
            self.manual_backup = True

            name = safe_filename(self.name_le.text())
            if name == '':
                name = _('manual_backup')
            self.name_le.setText(name)

            set_config_value('last_manual_backup_name', name)

            self.backup_saves(name)

    def prune_auto_backups(self):
        max_auto_backups = max(int(get_config_value('max_auto_backups', '6'))
            , 1)

        search_start = (_('auto') + '_').lower()

        backup_dir = os.path.join(self.game_dir, 'save_backups')
        if not os.path.isdir(backup_dir):
            return

        auto_backups = []

        for entry in scandir(backup_dir):
            filename, ext = os.path.splitext(entry.name)
            if entry.is_file() and ext.lower() == '.zip':
                filename_lower = filename.lower()

                if filename_lower.startswith(search_start):
                    auto_backups.append({
                        'path': entry.path,
                        'modified': datetime.fromtimestamp(
                            entry.stat().st_mtime)
                    })

        if len(auto_backups) >= max_auto_backups:
            # Remove backups to have a total of max_auto_backups - 1
            auto_backups.sort(key=lambda x: x['modified'])
            remove_count = len(auto_backups) - max_auto_backups + 1

            to_remove = auto_backups[:remove_count]

            for backup in to_remove:
                delete_path(backup['path'])

    def backup_saves(self, name, single=False):
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        save_dir = os.path.join(self.game_dir, 'save')
        if not os.path.isdir(save_dir):
            status_bar.showMessage(_('Save directory not found'))
            if self.after_backup is not None:
                self.after_backup()
                self.after_backup = None
            return
        self.save_dir = save_dir

        backup_dir = os.path.join(self.game_dir, 'save_backups')
        if not os.path.isdir(backup_dir):
            if os.path.isfile(backup_dir):
                os.remove(backup_dir)

            os.makedirs(backup_dir)

        if single:
            backup_filename = name + '.zip'
            self.backup_path = os.path.join(backup_dir, backup_filename)
            if os.path.isfile(self.backup_path):
                if not delete_path(self.backup_path):
                    status_bar.showMessage(_('Could not delete previous '
                        'backup archive'))
                    return
        else:
            '''
            Finding a backup filename which does not already exists or is the
            next backup name based on an incremental counter placed at the end
            of the filename without the extension.
            '''

            name_lower = name.lower()
            name_key = alphanum_key(name_lower)
            if len(name_key) > 1 and isinstance(name_key[-1:][0], int):
                name_key = name_key[:-1]

            duplicate_name = False
            duplicate_basename = False
            max_counter = 0

            for entry in scandir(backup_dir):
                filename, ext = os.path.splitext(entry.name)
                if entry.is_file() and ext.lower() == '.zip':
                    filename_lower = filename.lower()

                    if filename_lower == name_lower:
                        duplicate_name = True
                    else:
                        filename_key = alphanum_key(filename_lower)

                        counter = filename_key[-1:][0]
                        if len(filename_key) > 1 and isinstance(counter, int):
                            filename_key = filename_key[:-1]

                            if name_key == filename_key:
                                duplicate_basename = True
                                max_counter = max(max_counter, counter)

            if duplicate_basename:
                name_key = alphanum_key(name)
                if len(name_key) > 1 and isinstance(name_key[-1:][0], int):
                    name_key = name_key[:-1]

                name_key.append(max_counter + 1)
                backup_filename = ''.join(map(lambda x: str(x), name_key))
            elif duplicate_name:
                backup_filename = name + '2'
            else:
                backup_filename = name

            backup_filename = backup_filename + '.zip'

            self.backup_path = os.path.join(backup_dir, backup_filename)

        self.backup_file = None

        status_bar.clearMessage()
        status_bar.busy += 1

        compressing_label = QLabel()
        status_bar.addWidget(compressing_label, 100)
        self.compressing_label = compressing_label

        self.compressing_progress_bar = None
        self.compressing_speed_label = None
        self.compressing_size_label = None

        timer = QTimer(self)
        self.compressing_timer = timer

        self.backup_searching = True
        self.backup_compressing = False

        self.backup_files = deque()
        self.backup_file_sizes = {}

        self.backup_scan = None
        self.next_backup_scans = deque()

        self.total_backup_size = 0
        self.total_files = 0

        self.disable_tab()
        self.get_main_tab().disable_tab()
        self.get_soundpacks_tab().disable_tab()
        self.get_settings_tab().disable_tab()
        self.get_mods_tab().disable_tab()
        self.get_backups_tab().disable_tab()

        if self.manual_backup:
            self.backup_current_button.setText(_('Cancel backup'))
            self.backup_current_button.setEnabled(True)

        compressing_label.setText(_('Searching for save files'))

        def timeout():
            if self.backup_scan is None:
                self.backup_scan = scandir(self.save_dir)
            else:
                try:
                    entry = next(self.backup_scan)

                    if entry.is_file():
                        self.compressing_label.setText(
                            _('Found {filename} in {path}').format(
                                filename=entry.name,
                                path=os.path.dirname(entry.path)))
                        self.backup_files.append(entry.path)
                        self.total_backup_size += entry.stat().st_size
                        self.backup_file_sizes[entry.path
                            ] = entry.stat().st_size
                        self.total_files += 1
                    elif entry.is_dir():
                        self.next_backup_scans.append(entry.path)
                except StopIteration:
                    try:
                        self.backup_scan = scandir(
                            self.next_backup_scans.popleft())
                    except IndexError:
                        self.backup_searching = False
                        self.backup_compressing = True

                        self.compressing_label.setText(
                            _('Compressing save files'))

                        compressing_speed_label = QLabel()
                        compressing_speed_label.setText(_('{bytes_sec}/s'
                            ).format(bytes_sec=sizeof_fmt(0)))
                        status_bar.addWidget(compressing_speed_label)
                        self.compressing_speed_label = (
                            compressing_speed_label)

                        compressing_size_label = QLabel()
                        compressing_size_label.setText(
                            _('{bytes_read}/{total_bytes}').format(
                            bytes_read=sizeof_fmt(0),
                            total_bytes=sizeof_fmt(self.total_backup_size)))
                        status_bar.addWidget(compressing_size_label)
                        self.compressing_size_label = (
                            compressing_size_label)

                        progress_bar = QProgressBar()
                        progress_bar.setRange(0, self.total_backup_size)
                        progress_bar.setValue(0)
                        status_bar.addWidget(progress_bar)
                        self.compressing_progress_bar = progress_bar

                        self.comp_size = 0
                        self.comp_files = 0
                        self.last_comp_bytes = 0
                        self.last_comp = datetime.utcnow()
                        self.next_backup_file = None

                        if self.compressing_timer is not None:
                            self.compressing_timer.stop()
                            self.compressing_timer = None

                        self.backup_saves_step2()

        timer.timeout.connect(timeout)
        timer.start(0)

    def backup_saves_step2(self):

        class CompressThread(QThread):
            completed = pyqtSignal()

            def __init__(self, zfile, filename, arcname):
                super(CompressThread, self).__init__()

                self.zfile = zfile
                self.filename = filename
                self.arcname = arcname

            def __del__(self):
                self.wait()

            def run(self):
                self.zfile.write(self.filename, self.arcname)
                self.completed.emit()

        def backup_next_file():
            try:
                if self.backup_compressing:
                    next_file = self.backup_files.popleft()
                    relpath = os.path.relpath(next_file, self.game_dir)
                    self.next_backup_file = next_file

                    self.compressing_label.setText(
                        _('Compressing {filename}').format(filename=relpath))

                    compress_thread = CompressThread(self.backup_file,
                        next_file, relpath)
                    compress_thread.completed.connect(completed_compress)
                    self.compress_thread = compress_thread

                    compress_thread.start()

            except IndexError:
                self.backup_compressing = False
                self.compress_thread = None

                self.finish_backup_saves()

                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                if self.after_backup is not None:
                    self.after_update_backups = self.after_backup
                    self.after_backup = None
                else:
                    status_bar.showMessage(_('Saves backup completed'))

                self.update_backups_table()

        def completed_compress():
            self.comp_size += self.backup_file_sizes[self.next_backup_file]
            self.compressing_progress_bar.setValue(self.comp_size)

            self.compressing_size_label.setText(
                _('{bytes_read}/{total_bytes}').format(
                bytes_read=sizeof_fmt(self.comp_size),
                total_bytes=sizeof_fmt(self.total_backup_size)))

            delta_bytes = self.comp_size - self.last_comp_bytes
            delta_time = datetime.utcnow() - self.last_comp
            if delta_time.total_seconds() == 0:
                delta_time = timedelta.resolution

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.compressing_speed_label.setText(_('{bytes_sec}/s'
                ).format(bytes_sec=sizeof_fmt(bytes_secs)))

            self.last_comp_bytes = self.comp_size
            self.last_comp = datetime.utcnow()

            backup_next_file()

        self.backup_file = zipfile.ZipFile(self.backup_path, 'w',
            zipfile.ZIP_DEFLATED)
        backup_next_file()

    def finish_backup_saves(self):
        if self.backup_file is not None:
            self.backup_file.close()

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_bar.removeWidget(self.compressing_label)
        if self.compressing_progress_bar is not None:
            status_bar.removeWidget(self.compressing_progress_bar)
        if self.compressing_speed_label is not None:
            status_bar.removeWidget(self.compressing_speed_label)
        if self.compressing_size_label is not None:
            status_bar.removeWidget(self.compressing_size_label)

        status_bar.busy -= 1

        self.enable_tab()
        self.get_main_tab().enable_tab()
        self.get_soundpacks_tab().enable_tab()
        self.get_settings_tab().enable_tab()
        self.get_mods_tab().enable_tab()
        self.get_backups_tab().enable_tab()

        if self.manual_backup:
            self.manual_backup = False
            self.backup_current_button.setText(_('Backup current saves'))

    def game_dir_changed(self, new_dir):
        self.game_dir = new_dir

        save_dir = os.path.join(self.game_dir, 'save')
        if os.path.isdir(save_dir):
            self.backup_current_button.setEnabled(True)

        self.update_backups_table()

    def backups_table_header_sort(self, index, order):
        self.backups_table.sortItems(index, order)

    def backups_table_selection_changed(self):
        items = self.backups_table.selectedItems()
        has_items = len(items) > 0

        self.restore_button.setEnabled(has_items)
        self.delete_button.setEnabled(has_items)

    def clear_backups(self):
        self.game_dir = None
        self.backups = {}

        self.restore_button.setEnabled(False)
        self.refresh_list_button.setEnabled(False)
        self.delete_button.setEnabled(False)

        self.backup_current_button.setEnabled(False)

        self.backups_table.horizontalHeader().setSortIndicatorShown(False)

        self.backups_table.clearContents()
        for i in range(self.backups_table.rowCount()):
            self.backups_table.removeRow(0)

    @property
    def app_locale(self):
        return QApplication.instance().app_locale

    def update_backups_table(self):
        selection_model = self.backups_table.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            self.previous_selection = None
        else:
            selected = selection_model.currentIndex()
            table_item = self.backups_table.item(selected.row(), 0)
            selected_info = self.backups[table_item]

            self.previous_selection = selected_info['path']

        self.previous_selection_index = None

        self.backups_table.horizontalHeader().setSortIndicatorShown(False)

        self.backups_table.clearContents()
        for i in range(self.backups_table.rowCount()):
            self.backups_table.removeRow(0)

        self.backups = {}

        if self.game_dir is None:
            return

        backup_dir = os.path.join(self.game_dir, 'save_backups')
        if not os.path.isdir(backup_dir):
            return

        self.refresh_list_button.setEnabled(True)

        if (self.update_backups_timer is not None
            and self.update_backups_timer.isActive()):
            self.update_backups_timer.stop()

        timer = QTimer(self)
        self.update_backups_timer = timer

        self.backups_scan = scandir(backup_dir)

        def timeout():
            try:
                entry = next(self.backups_scan)
                filename, ext = os.path.splitext(entry.name)
                if ext.lower() == '.zip':
                    uncompressed_size = 0
                    character_count = 0
                    worlds_set = set()
                    try:
                        with zipfile.ZipFile(entry.path) as zfile:
                            for info in zfile.infolist():
                                if not info.filename.startswith('save/'):
                                    return

                                uncompressed_size += info.file_size

                                path_items = info.filename.split('/')

                                if len(path_items) == 3:
                                    save_file = path_items[-1]
                                    if save_file.endswith('.sav'):
                                        character_count += 1
                                    if save_file in cons.WORLD_FILES:
                                        worlds_set.add(path_items[1])
                    except zipfile.BadZipFile:
                        pass

                    # We found a valid backup

                    compressed_size = entry.stat().st_size
                    modified_date = datetime.fromtimestamp(
                        entry.stat().st_mtime)
                    formated_date = format_datetime(modified_date,
                        format='short', locale=self.app_locale)
                    arrow_date = arrow.get(entry.stat().st_mtime)
                    human_delta = arrow_date.humanize(arrow.utcnow(),
                        locale=self.app_locale)

                    row_index = self.backups_table.rowCount()
                    self.backups_table.insertRow(row_index)

                    flags = (Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                    if uncompressed_size == 0:
                        compression_ratio = 0
                    else:
                        compression_ratio = 1.0 - (compressed_size /
                            uncompressed_size)
                    rounded_ratio = round(compression_ratio, 4)
                    ratio_percent = format_percent(rounded_ratio,
                        format='#.##%', locale=self.app_locale)

                    if self.previous_selection is not None:
                        if entry.path == self.previous_selection:
                            self.previous_selection_index = row_index

                    fields = (
                        (filename, alphanum_key(filename)),
                        (human_delta, modified_date),
                        (str(len(worlds_set)), len(worlds_set)),
                        (str(character_count), character_count),
                        (sizeof_fmt(uncompressed_size), uncompressed_size),
                        (sizeof_fmt(compressed_size), compressed_size),
                        (ratio_percent, compression_ratio),
                        (formated_date, modified_date)
                        )

                    for index, value in enumerate(fields):
                        item = SortEnabledTableWidgetItem(value[0], value[1])
                        item.setFlags(flags)
                        self.backups_table.setItem(row_index, index, item)

                        if index == 0:
                            self.backups[item] = {
                                'path': entry.path,
                                'actual_size': uncompressed_size
                            }

            except StopIteration:
                self.update_backups_timer.stop()

                if self.previous_selection_index is not None:
                    selection_model = self.backups_table.selectionModel()
                    model = selection_model.model()

                    first_index = model.index(self.previous_selection_index, 0)
                    last_index = model.index(self.previous_selection_index,
                        self.backups_table.columnCount() - 1)
                    row_selection = QItemSelection(first_index, last_index)

                    selection_model.select(row_selection,
                        QItemSelectionModel.Select)
                    selection_model.setCurrentIndex(first_index,
                        QItemSelectionModel.Select)

                self.backups_table.sortItems(1, Qt.DescendingOrder)
                self.backups_table.horizontalHeader().setSortIndicatorShown(
                    True)

                if self.after_update_backups is not None:
                    self.after_update_backups()
                    self.after_update_backups = None

        timer.timeout.connect(timeout)
        timer.start(0)


class SortEnabledTableWidgetItem(QTableWidgetItem):
    def __init__(self, value, sort_data):
        super(SortEnabledTableWidgetItem, self).__init__(value)

        self.sort_data = sort_data

    def __lt__(self, other):
        return self.sort_data < other.sort_data

    def __hash__(self):
        return id(self)


class TilesetsTab(QTabWidget):
    def __init__(self):
        super(TilesetsTab, self).__init__()

    def set_text(self):
        pass

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab


class FontsTab(QTabWidget):
    def __init__(self):
        super(FontsTab, self).__init__()

        layout = QGridLayout()

        font_window = CataWindow(4, 4, QFont('Consolas'), 18, 9, 18, False)
        layout.addWidget(font_window, 0, 0)
        self.font_window = font_window

        self.setLayout(layout)

    def set_text(self):
        pass

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab


class CataWindow(QWidget):
    def __init__(self, terminalwidth, terminalheight, font, fontsize, fontwidth,
            fontheight, fontblending):
        super(CataWindow, self).__init__()

        self.terminalwidth = terminalwidth
        self.terminalheight = terminalheight

        self.cfont = font
        self.fontsize = fontsize
        self.cfont.setPixelSize(fontsize)
        self.cfont.setStyle(QFont.StyleNormal)
        self.fontwidth = fontwidth
        self.fontheight = fontheight
        self.fontblending = fontblending

        #self.text = '@@@\nBBB\n@@@\nCCC'
        self.text = '####\n####\n####\n####\n'

    def sizeHint(self):
        return QSize(self.terminalwidth * self.fontwidth,
            self.terminalheight * self.fontheight)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), QColor(0, 0, 0))
        painter.setPen(QColor(99, 99, 99));
        painter.setFont(self.cfont)

        term_x = 0
        term_y = 0
        for char in self.text:
            if char == '\n':
                term_y += 1
                term_x = 0
                continue
            x = self.fontwidth * term_x
            y = self.fontheight * term_y

            rect = QRect(x, y, self.fontwidth, self.fontheight)
            painter.drawText(rect, 0, char)

            term_x += 1

        x = self.fontwidth * term_x
        y = self.fontheight * term_y

        rect = QRect(x, y, self.fontwidth, self.fontheight)

        painter.fillRect(rect, Qt.green)


# Recursively delete an entire directory tree while showing progress in a
# status bar. Also display a dialog to retry the delete if there is a problem.
class ProgressRmTree(QTimer):
    completed = pyqtSignal()
    aborted = pyqtSignal()

    def __init__(self, src, status_bar, name):
        if not os.path.isdir(src):
            raise OSError(_("Source path '%s' is not a directory") % src)

        super(ProgressRmTree, self).__init__()

        self.src = src

        self.status_bar = status_bar
        self.name = name

        self.started = False

        self.status_label = None
        self.progress_bar = None

        self.analysing = False
        self.deleting = False
        self.delete_completed = False

    def step(self):
        if self.analysing:
            if self.current_scan is None:
                self.current_scan = scandir(self.src)
            else:
                try:
                    entry = next(self.current_scan)
                    self.source_entries.append(entry)
                    if entry.is_dir():
                        self.next_scans.append(entry.path)
                    elif entry.is_file():
                        self.total_files += 1

                        files_text = ngettext('file', 'files', self.total_files)

                        self.status_label.setText(_('Analysing {name} - Found '
                            '{file_count} {files}').format(
                                name=self.name,
                                file_count=self.total_files,
                                files=files_text))

                except StopIteration:
                    if len(self.next_scans) > 0:
                        self.current_scan = scandir(self.next_scans.popleft())
                    else:
                        self.analysing = False

                        if len(self.source_entries) > 0:
                            self.deleting = True

                            progress_bar = QProgressBar()
                            progress_bar.setRange(0, self.total_files)
                            progress_bar.setValue(0)
                            self.status_bar.addWidget(progress_bar)
                            self.progress_bar = progress_bar

                            self.deleted_files = 0
                            self.current_entry = None
                        else:
                            self.delete_completed = True
                            self.stop()

        elif self.deleting:
            if self.current_entry is None:
                if len(self.source_entries) > 0:
                    self.current_entry = self.source_entries.pop()
                    self.display_entry(self.current_entry)
                else:
                    # Remove the source directory
                    while os.path.exists(self.src):
                        try:
                            try:
                                os.rmdir(self.src)
                            except OSError:
                                # Remove read-only and try again
                                os.chmod(self.src, stat.S_IWRITE)
                                os.rmdir(self.src)
                        except OSError as e:
                            retry_msgbox = QMessageBox()
                            retry_msgbox.setWindowTitle(
                                _('Cannot remove directory'))

                            process = None
                            if e.filename is not None:
                                process = find_process_with_file_handle(
                                    e.filename)

                            text = _('''
<p>The launcher failed to remove the following directory: {directory}</p>
<p>When trying to remove or access {filename}, the launcher raised the
following error: {error}</p>''').format(
                                directory=html.escape(self.src),
                                filename=html.escape(e.filename),
                                error=html.escape(e.strerror))

                            if process is None:
                                text = text + _('''
<p>No process seems to be using that file or directory.</p>''')
                            else:
                                text = text + _('''
<p>The process <strong>{image_file_name} ({pid})</strong> is currently using
that file or directory. You might need to end it if you want to retry.</p>'''
                                ).format(
                                    image_file_name=process['image_file_name'],
                                    pid=process['pid'])

                            retry_msgbox.setText(text)
                            retry_msgbox.setInformativeText(_('Do you want to '
                                'retry removing this directory?'))
                            retry_msgbox.addButton(
                                _('Retry removing the directory'),
                                QMessageBox.YesRole)
                            retry_msgbox.addButton(_('Cancel the operation'),
                                QMessageBox.NoRole)
                            retry_msgbox.setIcon(QMessageBox.Critical)

                            if retry_msgbox.exec() == 1:
                                self.deleting = False
                                self.stop()
                                break

                    self.deleting = False
                    self.delete_completed = True
                    self.stop()
            else:
                while os.path.exists(self.current_entry.path):
                    try:
                        if self.current_entry.is_dir():
                            try:
                                os.rmdir(self.current_entry.path)
                            except OSError:
                                # Remove read-only and try again
                                os.chmod(self.current_entry.path, stat.S_IWRITE)
                                os.rmdir(self.current_entry.path)
                        elif self.current_entry.is_file():
                            try:
                                os.unlink(self.current_entry.path)
                            except OSError:
                                # Remove read-only and try again
                                os.chmod(self.current_entry.path, stat.S_IWRITE)
                                os.unlink(self.current_entry.path)
                    except OSError as e:
                        retry_msgbox = QMessageBox()
                        retry_msgbox.setWindowTitle(
                            _('Cannot remove directory'))

                        process = None
                        if e.filename is not None:
                            process = find_process_with_file_handle(e.filename)

                        text = _('''
<p>The launcher failed to remove the following directory: {directory}</p>
<p>When trying to remove or access {filename}, the launcher raised the
following error: {error}</p>''').format(
                            directory=html.escape(self.src),
                            filename=html.escape(e.filename),
                            error=html.escape(e.strerror))

                        if process is None:
                            text = text + _('''
<p>No process seems to be using that file or directory.</p>''')
                        else:
                            text = text + _('''
<p>The process <strong>{image_file_name} ({pid})</strong> is currently using
that file or directory. You might need to end it if you want to retry.</p>'''
                            ).format(image_file_name=process['image_file_name'],
                                pid=process['pid'])

                        retry_msgbox.setText(text)
                        retry_msgbox.setInformativeText(_('Do you want to '
                            'retry removing this directory?'))
                        retry_msgbox.addButton(
                            _('Retry removing the directory'),
                            QMessageBox.YesRole)
                        retry_msgbox.addButton(_('Cancel the operation'),
                            QMessageBox.NoRole)
                        retry_msgbox.setIcon(QMessageBox.Critical)

                        if retry_msgbox.exec() == 1:
                            self.deleting = False
                            self.stop()
                            break

                self.current_entry = None
                self.deleted_files += 1

                self.progress_bar.setValue(self.deleted_files)
    def display_entry(self, entry):
        if self.status_label is not None:
            entry_rel_path = os.path.relpath(entry.path, self.src)
            self.status_label.setText(
                _('Deleting {name} - {entry}').format(name=self.name,
                    entry=entry_rel_path))

    def start(self):
        self.started = True
        self.status_bar.clearMessage()
        self.status_bar.busy += 1

        self.analysing = True
        status_label = QLabel()
        status_label.setText(_('Analysing {name}').format(name=self.name))
        self.status_bar.addWidget(status_label, 100)
        self.status_label = status_label

        self.total_files = 0

        self.timeout.connect(self.step)

        self.current_scan = None
        self.next_scans = deque()
        self.source_entries = deque()

        super(ProgressRmTree, self).start(0)

    def stop(self):
        super(ProgressRmTree, self).stop()

        if self.started:
            self.status_bar.busy -= 1
            if self.status_label is not None:
                self.status_bar.removeWidget(self.status_label)
            if self.progress_bar is not None:
                self.status_bar.removeWidget(self.progress_bar)

        if self.delete_completed:
            self.completed.emit()
        else:
            self.aborted.emit()

# Recursively copy an entire directory tree while showing progress in a
# status bar. Optionally skip files or directories.
class ProgressCopyTree(QTimer):
    completed = pyqtSignal()
    aborted = pyqtSignal()

    def __init__(self, src, dst, skips, status_bar, name):
        if not os.path.isdir(src):
            raise OSError(_("Source path '%s' is not a directory") % src)
        if os.path.exists(dst):
            raise OSError(_("Destination path '%s' already exists") % dst)

        super(ProgressCopyTree, self).__init__()

        self.src = src
        self.dst = dst
        self.skips = skips

        self.status_bar = status_bar
        self.name = name

        self.started = False
        self.callback = None

        self.status_label = None
        self.copying_speed_label = None
        self.copying_size_label = None
        self.progress_bar = None

        self.source_file = None
        self.destination_file = None

        self.analysing = False
        self.copying = False
        self.copy_completed = False

    def step(self):
        if self.analysing:
            if self.current_scan is None:
                self.current_scan = scandir(self.src)
            else:
                try:
                    entry = next(self.current_scan)
                    if self.skips is None or entry.path not in self.skips:
                        self.source_entries.append(entry)
                        if entry.is_dir():
                            self.next_scans.append(entry.path)
                        elif entry.is_file():
                            self.total_files += 1
                            self.total_copy_size += entry.stat().st_size

                            files_text = ngettext('file', 'files',
                                self.total_files)

                            self.status_label.setText(_('Analysing {name} - '
                                'Found {file_count} {files} ({size})').format(
                                    name=self.name,
                                    file_count=self.total_files,
                                    files=files_text,
                                    size=sizeof_fmt(self.total_copy_size)))

                except StopIteration:
                    if len(self.next_scans) > 0:
                        self.current_scan = scandir(self.next_scans.popleft())
                    else:
                        self.analysing = False

                        os.makedirs(self.dst)

                        if len(self.source_entries) > 0:
                            self.copying = True

                            copying_speed_label = QLabel()
                            copying_speed_label.setText(_('{bytes_sec}/s'
                                ).format(bytes_sec=sizeof_fmt(0)))
                            self.status_bar.addWidget(copying_speed_label)
                            self.copying_speed_label = copying_speed_label

                            copying_size_label = QLabel()
                            copying_size_label.setText(
                                _('{bytes_read}/{total_bytes}').format(
                                bytes_read=sizeof_fmt(0),
                                total_bytes=sizeof_fmt(self.total_copy_size)))
                            self.status_bar.addWidget(copying_size_label)
                            self.copying_size_label = copying_size_label

                            progress_bar = QProgressBar()
                            progress_bar.setRange(0, self.total_copy_size)
                            progress_bar.setValue(0)
                            self.status_bar.addWidget(progress_bar)
                            self.progress_bar = progress_bar

                            self.copied_size = 0
                            self.copied_files = 0
                            self.copy_speed_count = 0
                            self.last_copied_bytes = 0
                            self.last_copied = datetime.utcnow()
                            self.current_entry = None
                            self.source_file = None
                            self.destination_file = None
                        else:
                            self.copy_completed = True
                            self.stop()

        elif self.copying:
            if self.current_entry is None:
                if len(self.source_entries) > 0:
                    self.current_entry = self.source_entries.popleft()
                    self.display_entry(self.current_entry)
                else:
                    self.copying = False
                    self.copy_completed = True
                    self.stop()
            elif self.source_file is None and self.destination_file is None:
                relpath = os.path.relpath(self.current_entry.path, self.src)
                dstpath = os.path.join(self.dst, relpath)
                self.dstpath = dstpath

                if self.current_entry.is_dir():
                    os.makedirs(dstpath)
                    self.current_entry = None
                elif self.current_entry.is_file():
                    filedir = os.path.dirname(dstpath)
                    if not os.path.isdir(filedir):
                        os.makedirs(filedir)
                    self.source_file = open(self.current_entry.path, 'rb')
                    self.destination_file = open(dstpath, 'wb')
            else:
                buf = self.source_file.read(cons.READ_BUFFER_SIZE)
                buf_len = len(buf)
                if buf_len == 0:
                    self.source_file.close()
                    self.destination_file.close()
                    shutil.copystat(self.current_entry.path, self.dstpath)
                    self.source_file = None
                    self.destination_file = None
                    self.current_entry = None

                    self.copied_files += 1
                else:
                    self.destination_file.write(buf)

                    self.copied_size += buf_len
                    self.progress_bar.setValue(self.copied_size)

                    self.copy_speed_count += 1

                    if self.copy_speed_count % 10 == 0:
                        self.copying_size_label.setText(
                            _('{bytes_read}/{total_bytes}').format(
                            bytes_read=sizeof_fmt(self.copied_size),
                            total_bytes=sizeof_fmt(self.total_copy_size)))

                        delta_bytes = self.copied_size - self.last_copied_bytes
                        delta_time = datetime.utcnow() - self.last_copied
                        if delta_time.total_seconds() == 0:
                            delta_time = timedelta.resolution

                        bytes_secs = delta_bytes / delta_time.total_seconds()
                        self.copying_speed_label.setText(_('{bytes_sec}/s'
                            ).format(bytes_sec=sizeof_fmt(bytes_secs)))

                        self.last_copied_bytes = self.copied_size
                        self.last_copied = datetime.utcnow()


    def display_entry(self, entry):
        if self.status_label is not None:
            entry_rel_path = os.path.relpath(entry.path, self.src)
            self.status_label.setText(
                _('Copying {name} - {entry}').format(name=self.name,
                    entry=entry_rel_path))

    def start(self):
        self.started = True
        self.status_bar.clearMessage()
        self.status_bar.busy += 1

        self.analysing = True
        status_label = QLabel()
        status_label.setText(_('Analysing {name}').format(name=self.name))
        self.status_bar.addWidget(status_label, 100)
        self.status_label = status_label

        self.total_copy_size = 0
        self.total_files = 0

        self.timeout.connect(self.step)

        self.current_scan = None
        self.next_scans = deque()
        self.source_entries = deque()

        super(ProgressCopyTree, self).start(0)

    def stop(self):
        super(ProgressCopyTree, self).stop()

        if self.started:
            self.status_bar.busy -= 1
            if self.status_label is not None:
                self.status_bar.removeWidget(self.status_label)
            if self.progress_bar is not None:
                self.status_bar.removeWidget(self.progress_bar)
            if self.copying_speed_label is not None:
                self.status_bar.removeWidget(self.copying_speed_label)
            if self.copying_size_label is not None:
                self.status_bar.removeWidget(self.copying_size_label)

            if self.source_file is not None:
                self.source_file.close()
            if self.destination_file is not None:
                self.destination_file.close()

        if self.copy_completed:
            self.completed.emit()
        else:
            self.aborted.emit()


class ExceptionWindow(QWidget):
    def __init__(self, app, extype, value, tb):
        super(ExceptionWindow, self).__init__()

        self.app = app

        layout = QGridLayout()

        information_label = QLabel()
        information_label.setText(_('The CDDA Game Launcher just crashed. An '
            'unhandled exception was raised. Here are the details.'))
        layout.addWidget(information_label, 0, 0)
        self.information_label = information_label

        tb_io = StringIO()
        traceback.print_tb(tb, file=tb_io)
        traceback_content = html.escape(tb_io.getvalue()).replace('\n', '<br>')

        text_content = QTextBrowser()
        text_content.setReadOnly(True)
        text_content.setOpenExternalLinks(True)
        text_content.setHtml(_('''
<p>CDDA Game Launcher version: {version}</p>
<p>OS: {os} ({bitness})</p>
<p>Type: {extype}</p>
<p>Value: {value}</p>
<p>Traceback:</p>
<code>{traceback}</code>
''').format(version=html.escape(version), extype=html.escape(str(extype)),
    value=html.escape(str(value)), os=html.escape(platform.platform()),
    traceback=traceback_content, bitness=html.escape(bitness())))

        layout.addWidget(text_content, 1, 0)
        self.text_content = text_content

        report_url = cons.NEW_ISSUE_URL + '?' + urlencode({
            'title': _('Unhandled exception: [Enter a title]'),
            'body': _('''* Description: [Enter what you did and what happened]
* Version: {version}
* OS: {os} ({bitness})
* Type: `{extype}`
* Value: {value}
* Traceback:
```
{traceback}
```
''').format(version=version, extype=str(extype), value=str(value),
    traceback=tb_io.getvalue(), os=platform.platform(), bitness=bitness())
        })

        report_label = QLabel()
        report_label.setOpenExternalLinks(True)
        report_label.setText(_('Please help us make a better launcher '
            '<a href="{url}">by reporting this issue on GitHub</a>.').format(
                url=html.escape(report_url)))
        layout.addWidget(report_label, 2, 0)
        self.report_label = report_label

        exit_button = QPushButton()
        exit_button.setText(_('Exit'))
        exit_button.clicked.connect(lambda: self.app.exit(-100))
        layout.addWidget(exit_button, 3, 0, Qt.AlignRight)
        self.exit_button = exit_button

        self.setLayout(layout)
        self.setWindowTitle(_('Something went wrong'))
        self.setMinimumSize(350, 0)

def start_ui(locale, single_instance):
    load_gettext_locale(get_locale_path(), locale)

    main_app = QApplication(sys.argv)
    main_app.setWindowIcon(QIcon(get_resource_path('launcher.ico')))

    main_win = MainWindow('CDDA Game Launcher')
    main_win.show()

    main_app.main_win = main_win
    main_app.single_instance = single_instance
    main_app.app_locale = locale
    sys.exit(main_app.exec_())

def ui_exception(extype, value, tb):
    main_app = QApplication.instance()

    if main_app is not None:
        main_app_still_up = True
        main_app.closeAllWindows()
    else:
        main_app_still_up = False
        main_app = QApplication(sys.argv)

    ex_win = ExceptionWindow(main_app, extype, value, tb)
    ex_win.show()
    main_app.ex_win = ex_win

    if not main_app_still_up:
        sys.exit(main_app.exec_())