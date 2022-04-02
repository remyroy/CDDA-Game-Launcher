# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import hashlib
import html
import json
import logging
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
import random

from collections import deque
from datetime import datetime, timedelta
from io import BytesIO, TextIOWrapper
from os import scandir
from pathlib import Path
from urllib.parse import urljoin

import arrow
from PyQt5.QtCore import (
    Qt, QTimer, QUrl, QFileInfo, pyqtSignal, QStringListModel, QThread, QRegularExpression
)
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QGroupBox, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QToolButton, QProgressBar, QButtonGroup, QRadioButton,
    QComboBox, QTextBrowser, QMessageBox, QStyle, QHBoxLayout, QSizePolicy
)
from PyQt5.QtGui import QRegularExpressionValidator
from babel.dates import format_datetime
from pywintypes import error as PyWinError

import cddagl.constants as cons
from cddagl.constants import get_cddagl_path, get_cdda_uld_path
from cddagl import __version__ as version
from cddagl.functions import (
    tryint, move_path, is_64_windows, sizeof_fmt, delete_path,
    clean_qt_path, unique, log_exception, ensure_slash, safe_humanize
)
from cddagl.i18n import proxy_ngettext as ngettext, proxy_gettext as _
from cddagl.sql.functions import (
    get_config_value, set_config_value, new_version, get_build_from_sha256,
    new_build, config_true
)
from cddagl.win32 import (
    find_process_with_file_handle, activate_window, process_id_from_path, wait_for_pid,
    get_documents_directory
)

logger = logging.getLogger('cddagl')


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

        self.played = 0

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

    def get_statistics_tab(self):
        return self.parentWidget().parentWidget().statistics_tab

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

        self.layout_dir = QHBoxLayout()
        layout.addLayout(self.layout_dir, 0, 1)

        self.dir_combo = QComboBox()
        self.layout_dir.addWidget(self.dir_combo)
        self.dir_combo.setEditable(True)
        self.dir_combo.setInsertPolicy(QComboBox.InsertAtTop)
        self.dir_combo.currentIndexChanged.connect(self.dc_index_changed)
        self.dir_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        game_directories = json.loads(get_config_value('game_directories', '[]'))
        self.dir_combo_model = QStringListModel(game_directories, self)
        self.dir_combo.setModel(self.dir_combo_model)

        dir_change_button = QToolButton()
        self.layout_dir.addWidget(dir_change_button)
        dir_change_button.setText('...')
        dir_change_button.clicked.connect(self.set_game_directory)
        self.dir_change_button = dir_change_button

        self.dir_state_icon = QLabel()
        self.layout_dir.addWidget(self.dir_state_icon)
        self.dir_state_icon.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.dir_state_icon.hide()

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

    def set_dir_state_icon(self, state):
        style = QApplication.style()
        if state == 'critical':
            icon = style.standardIcon(QStyle.SP_MessageBoxCritical).pixmap(16, 16)
        elif state == 'warning':
            icon = style.standardIcon(QStyle.SP_MessageBoxWarning).pixmap(16, 16)
        elif state == 'ok':
            icon = style.standardIcon(QStyle.SP_DialogApplyButton).pixmap(16, 16)
        elif state == 'hide':
            self.dir_state_icon.hide()
            return

        self.dir_state_icon.setPixmap(icon)
        self.dir_state_icon.show()

    def showEvent(self, event):
        if not self.shown:
            self.shown = True

            self.last_game_directory = None

            game_directory = get_config_value('game_directory')
            if game_directory is None:
                documents_path = get_documents_directory()
                default_dir = os.path.join(documents_path, 'cdda')
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

            statistics_tab = main_tab.get_statistics_tab()

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

            statistics_tab.game_started()

            self.process_wait_thread = process_wait_thread

    def game_ended(self):
        if self.process_wait_thread is not None:
            self.process_wait_thread.quit()
            self.process_wait_thread = None

        self.game_process = None
        self.game_started = False

        main_tab = self.get_main_tab()
        statistics_tab = main_tab.get_statistics_tab()
        statistics_tab.game_ended()

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
        self.set_dir_state_icon('hide')

        self.exe_path = None

        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box

        dir_state = None
        if ensure_slash(get_cddagl_path()).startswith(ensure_slash(directory)):
            dir_state = 'critical'
            self.set_dir_state_icon(dir_state)
            self.version_value_label.setText(
                _('Unknown version - Reason:') + ' ' +
                _('CDDA Game Launcher files cannot be inside Game directory!')
            )
        elif os.path.isfile(directory):
            dir_state = 'critical'
            self.set_dir_state_icon(dir_state)
            self.version_value_label.setText(
                _('Unknown version - Reason:') + ' ' +
                _('Game directory was set to a file!')
            )
        elif not os.path.isdir(directory):
            dir_state = 'warning'
            self.set_dir_state_icon(dir_state)
            self.version_value_label.setText(
                _('Unknown version - Reason:') + ' ' +
                _("Game directory doesn't exist, Game is not installed here.")
            )
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
                dir_state = 'warning'
                self.set_dir_state_icon(dir_state)
                self.version_value_label.setText(
                    _('Unknown version - Reason:') + ' ' +
                    _("Game is not installed in this directory.")
                )
            else:
                dir_state = 'ok'
                self.exe_path = exe_path
                self.version_type = version_type
                if self.last_game_directory != directory:
                    self.version_value_label.setText(_('Analyzing...'))
                    self.build_value_label.setText(_('Analyzing...'))
                    self.saves_value_edit.setText(_('Analyzing...'))
                    self.update_version()
                    self.update_saves()
                    self.update_soundpacks()
                    self.update_mods()
                    self.update_backups()

        if self.exe_path is None:
            self.launch_game_button.setEnabled(False)
            update_group_box.update_button.setText(_('Install game'))
            update_group_box.update_button.setEnabled(dir_state != 'critical')

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
            update_group_box.update_button.setEnabled(dir_state == 'ok')

            self.check_running_process(self.exe_path)

        self.last_game_directory = directory
        
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
        self.game_version = ''

        game_dir = self.dir_combo.currentText()
        version_file = os.path.join(game_dir, 'VERSION.txt')
        if os.path.isfile(version_file):
            file_content = None
            with open(version_file, 'r', encoding='utf8') as read_file:
                file_content = read_file.read(1024)
            if file_content is not None:
                match = re.search(r'Build version: (?P<buildversion>\S+)', file_content)
                if match:
                    build_version = match.group('buildversion')
                    if len(build_version) > 2:
                        self.game_version = build_version
        
        self.opened_exe = open(self.exe_path, 'rb')

        def timeout():
            bytes = self.opened_exe.read(cons.READ_BUFFER_SIZE)
            if len(bytes) == 0:
                self.opened_exe.close()
                self.exe_reading_timer.stop()
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

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

                stable_version = cons.STABLE_SHA256.get(sha256, None)
                is_stable = stable_version is not None

                if is_stable:
                    self.game_version = stable_version
                
                if self.game_version == '':
                    self.game_version = _('Unknown')
                else:
                    self.add_game_dir()

                self.version_value_label.setText(
                    '{version} ({type})'
                    .format(version=self.game_version, type=self.version_type)
                )

                new_version(self.game_version, sha256, is_stable)

                build = get_build_from_sha256(sha256)

                if build is not None:
                    build_date = arrow.get(build['released_on'], 'UTC')
                    human_delta = safe_humanize(build_date, arrow.utcnow(), locale=self.app_locale)
                    self.build_value_label.setText(
                        '{build} ({time_delta})'
                        .format(build=build['build'], time_delta=human_delta)
                    )
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
                            message = message + _('There is a new update available')
                        status_bar.showMessage(message)

                else:
                    self.build_value_label.setText(_('Unknown'))
                    self.current_build = None

            else:
                self.exe_total_read += len(bytes)
                self.reading_progress_bar.setValue(self.exe_total_read)
                self.exe_sha256.update(bytes)

        timer.timeout.connect(timeout)
        timer.start(0)

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

        if (self.update_saves_timer is not None and self.update_saves_timer.isActive()):
            self.update_saves_timer.stop()
            self.saves_value_edit.setText(_('Unknown'))

        save_dir = os.path.join(self.game_dir, 'save')
        if not os.path.isdir(save_dir):
            self.saves_value_edit.setText(
                '{world_count} {worlds} - {character_count} {characters}'
                    .format(
                    world_count=0,
                    character_count=0,
                    worlds=ngettext('World', 'Worlds', 0),
                    characters=ngettext('Character', 'Characters', 0)
                )
            )
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
                characters_text = ngettext('Character', 'Characters',self.saves_characters)
                self.saves_value_edit.setText(
                    '{world_count} {worlds} - {character_count} {characters} ({size})'
                    .format(
                        world_count=self.saves_worlds,
                        character_count=self.saves_characters,
                        size=sizeof_fmt(self.saves_size),
                        worlds=worlds_text,
                        characters=characters_text
                    )
                )
            except StopIteration:
                if len(self.next_scans) > 0:
                    self.saves_scan = scandir(self.next_scans.pop())
                else:
                    # End of the tree
                    self.update_saves_timer.stop()
                    self.update_saves_timer = None

                    # no more path to scan but still 0 chars/worlds
                    if self.saves_worlds == 0 and self.saves_characters == 0:
                        self.saves_value_edit.setText(
                            '{world_count} {worlds} - {character_count} {characters}'
                            .format(
                                world_count=0,
                                character_count=0,
                                worlds=ngettext('World', 'Worlds', 0),
                                characters=ngettext('Character', 'Characters', 0)
                            )
                        )

                    # Warning about saves size
                    if (self.saves_size > cons.SAVES_WARNING_SIZE and
                        not config_true(get_config_value('prevent_save_move', 'False'))):
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
            self.game_version = ''

            version_file = os.path.join(game_dir, 'VERSION.txt')
            if os.path.isfile(version_file):
                file_content = None
                with open(version_file, 'r', encoding='utf8') as read_file:
                    file_content = read_file.read(1024)
                if file_content is not None:
                    match = re.search(r'commit sha: (?P<commitsha>\S+)', file_content)
                    if match:
                        commit_sha = match.group('commitsha')
                        if len(commit_sha) >= 7:
                            self.game_version = commit_sha[:7]

            self.opened_exe = open(self.exe_path, 'rb')

            def timeout():
                bytes = self.opened_exe.read(cons.READ_BUFFER_SIZE)
                if len(bytes) == 0:
                    self.opened_exe.close()
                    self.exe_reading_timer.stop()
                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    build_date = arrow.get(self.build_date, 'UTC')
                    human_delta = safe_humanize(build_date, arrow.utcnow(), locale=self.app_locale)
                    self.build_value_label.setText(
                        '{build} ({time_delta})'
                        .format(build=self.build_number, time_delta=human_delta)
                    )
                    self.current_build = self.build_number

                    status_bar.removeWidget(self.reading_label)
                    status_bar.removeWidget(self.reading_progress_bar)

                    status_bar.busy -= 1

                    sha256 = self.exe_sha256.hexdigest()

                    stable_version = cons.STABLE_SHA256.get(sha256, None)
                    is_stable = stable_version is not None

                    if is_stable:
                        self.game_version = stable_version

                    if self.game_version == '':
                        self.game_version = _('Unknown')
                    self.version_value_label.setText(
                        '{version} ({type})'
                        .format(version=self.game_version, type=self.version_type)
                    )

                    new_build(self.game_version, sha256, is_stable, self.build_number,
                        self.build_date)

                    main_tab = self.get_main_tab()
                    update_group_box = main_tab.update_group_box

                    update_group_box.post_extraction()

                else:
                    self.exe_total_read += len(bytes)
                    self.reading_progress_bar.setValue(self.exe_total_read)
                    self.exe_sha256.update(bytes)

            timer.timeout.connect(timeout)
            timer.start(0)


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

        self.api_reply = None
        self.api_response_content = None

        self.find_build_count = 0

        layout = QGridLayout()

        layout_row = 0

        branch_label = QLabel()
        layout.addWidget(branch_label, layout_row, 0, Qt.AlignRight)
        self.branch_label = branch_label

        branch_button_group = QButtonGroup()
        self.branch_button_group = branch_button_group

        stable_radio_button = QRadioButton()
        layout.addWidget(stable_radio_button, layout_row, 1)
        self.stable_radio_button = stable_radio_button
        branch_button_group.addButton(stable_radio_button)

        branch_button_group.buttonClicked.connect(self.branch_clicked)

        experimental_radio_button = QRadioButton()
        layout.addWidget(experimental_radio_button, layout_row, 2)
        self.experimental_radio_button = experimental_radio_button
        branch_button_group.addButton(experimental_radio_button)

        layout_row = layout_row + 1

        platform_label = QLabel()
        layout.addWidget(platform_label, layout_row, 0, Qt.AlignRight)
        self.platform_label = platform_label

        platform_button_group = QButtonGroup()
        self.platform_button_group = platform_button_group

        x64_radio_button = QRadioButton()
        layout.addWidget(x64_radio_button, layout_row, 1)
        self.x64_radio_button = x64_radio_button
        platform_button_group.addButton(x64_radio_button)

        platform_button_group.buttonClicked.connect(self.platform_clicked)

        if not is_64_windows():
            x64_radio_button.setEnabled(False)

        x86_radio_button = QRadioButton()
        layout.addWidget(x86_radio_button, layout_row, 2)
        self.x86_radio_button = x86_radio_button
        platform_button_group.addButton(x86_radio_button)

        layout_row = layout_row + 1

        available_builds_label = QLabel()
        layout.addWidget(available_builds_label, layout_row, 0, Qt.AlignRight)
        self.available_builds_label = available_builds_label

        builds_combo = QComboBox()
        builds_combo.setEnabled(False)
        self.previous_bc_enabled = False
        builds_combo.addItem(_('Unknown'))
        layout.addWidget(builds_combo, layout_row, 1, 1, 2)
        self.builds_combo = builds_combo

        refresh_warning_label = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning)
        refresh_warning_label.setPixmap(icon.pixmap(16, 16))
        refresh_warning_label.hide()
        layout.addWidget(refresh_warning_label, layout_row, 3)
        self.refresh_warning_label = refresh_warning_label

        refresh_builds_button = QToolButton()
        refresh_builds_button.clicked.connect(self.refresh_builds)
        layout.addWidget(refresh_builds_button, layout_row, 4)
        self.refresh_builds_button = refresh_builds_button

        layout_row = layout_row + 1

        find_build_label = QLabel()
        layout.addWidget(find_build_label, layout_row, 0, Qt.AlignRight)
        self.find_build_label = find_build_label

        find_build_value = QLineEdit()
        find_build_value.setValidator(QRegularExpressionValidator(
            QRegularExpression(r'\d+(-\d+)*')))
        find_build_value.returnPressed.connect(self.find_build)
        layout.addWidget(find_build_value, layout_row, 1, 1, 2)
        self.find_build_value = find_build_value

        find_build_warning_label = QLabel()
        icon = QApplication.style().standardIcon(QStyle.SP_MessageBoxWarning)
        find_build_warning_label.setPixmap(icon.pixmap(16, 16))
        find_build_warning_label.hide()
        layout.addWidget(find_build_warning_label, layout_row, 3)
        self.find_build_warning_label = find_build_warning_label

        find_build_button = QToolButton()
        find_build_button.clicked.connect(self.find_build)
        layout.addWidget(find_build_button, layout_row, 4)
        self.find_build_button = find_build_button

        layout_row = layout_row + 1

        changelog_groupbox = QGroupBox()
        changelog_layout = QHBoxLayout()
        changelog_groupbox.setLayout(changelog_layout)
        layout.addWidget(changelog_groupbox, layout_row, 0, 1, 5)
        self.changelog_groupbox = changelog_groupbox
        self.changelog_layout = changelog_layout

        changelog_content = QTextBrowser()
        changelog_content.setReadOnly(True)
        changelog_content.setOpenExternalLinks(True)
        self.changelog_layout.addWidget(changelog_content)
        self.changelog_content = changelog_content

        layout_row = layout_row + 1

        update_button = QPushButton()
        update_button.setEnabled(False)
        self.previous_ub_enabled = False
        update_button.setStyleSheet('font-size: 20px;')
        update_button.clicked.connect(self.update_game)
        layout.addWidget(update_button, layout_row, 0, 1, 5)
        self.update_button = update_button

        layout.setColumnStretch(1, 100)
        layout.setColumnStretch(2, 100)

        self.setLayout(layout)
        self.set_text()

    def set_text(self):
        self.branch_label.setText(_('Branch:'))
        self.stable_radio_button.setText(_('Stable'))
        self.experimental_radio_button.setText(_('Experimental'))
        self.platform_label.setText(_('Platform:'))
        self.x64_radio_button.setText('{so} ({bit})'.format(so=_('Windows x64'), bit=_('64-bit')))
        self.x86_radio_button.setText('{so} ({bit})'.format(so=_('Windows x86'), bit=_('32-bit')))
        self.available_builds_label.setText(_('Available builds:'))
        self.find_build_label.setText(_('Find build #:'))
        self.find_build_button.setText(_('Add to list'))
        self.refresh_builds_button.setText(_('Refresh'))
        self.changelog_groupbox.setTitle(_('Changelog'))
        self.update_button.setText(_('Update game'))
        self.setTitle(_('Update/Installation'))

    def showEvent(self, event):
        if not self.shown:
            branch = get_config_value(cons.CONFIG_BRANCH_KEY)

            if branch is None or branch not in (cons.CONFIG_BRANCH_STABLE,
                cons.CONFIG_BRANCH_EXPERIMENTAL):
                branch = cons.CONFIG_BRANCH_EXPERIMENTAL

            if branch == cons.CONFIG_BRANCH_STABLE:
                self.stable_radio_button.setChecked(True)
            elif branch == cons.CONFIG_BRANCH_EXPERIMENTAL:
                self.experimental_radio_button.setChecked(True)

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

            self.show_hide_find_build()

            self.refresh_builds()

        self.shown = True

    def find_build(self):
        build_number = self.find_build_value.text()
        build_number = build_number.strip()

        build_number = re.sub(r'[^0-9\-]', '', build_number)

        if build_number == '':
            return

        if self.find_build_count == 0:
            url = cons.GITHUB_REST_API_URL + cons.CDDA_RELEASE_BY_TAG(cons.BUILD_TAG(build_number))
            self.find_build_count = 1
        elif self.find_build_count == 1:
            url = cons.GITHUB_REST_API_URL + cons.CDDA_RELEASE_BY_TAG(
                cons.NEW_BUILD_TAG(build_number))
            self.find_build_count = 0

        self.api_response_content = BytesIO()

        request = QNetworkRequest(QUrl(url))
        request.setRawHeader(b'User-Agent',
            b'CDDA-Game-Launcher/' + version.encode('utf8'))
        request.setRawHeader(b'Accept', cons.GITHUB_API_VERSION)

        self.api_reply = self.qnam.get(request)
        self.api_reply.finished.connect(self.find_build_finished)
        self.api_reply.readyRead.connect(self.find_build_ready_read)

    def find_build_finished(self):
        redirect = self.api_reply.attribute(
            QNetworkRequest.RedirectionTargetAttribute)
        if redirect is not None:
            redirected_url = urljoin(
                self.api_reply.request().url().toString(),
                redirect.toString())

            self.api_response_content = BytesIO()

            request = QNetworkRequest(QUrl(redirected_url))
            request.setRawHeader(b'User-Agent',
                b'CDDA-Game-Launcher/' + version.encode('utf8'))
            request.setRawHeader(b'Accept', cons.GITHUB_API_VERSION)

            self.api_reply = self.qnam.get(request)
            self.api_reply.finished.connect(self.find_build_finished)
            self.api_reply.readyRead.connect(self.find_build_ready_read)
            return
        
        requests_remaining = None
        if self.api_reply.hasRawHeader(cons.GITHUB_XRL_REMAINING):
            requests_remaining = self.api_reply.rawHeader(cons.GITHUB_XRL_REMAINING)
            requests_remaining = tryint(requests_remaining)

        reset_dt = None
        if self.api_reply.hasRawHeader(cons.GITHUB_XRL_RESET):
            reset_dt = self.api_reply.rawHeader(cons.GITHUB_XRL_RESET)
            reset_dt = tryint(reset_dt)
            reset_dt = arrow.get(reset_dt)

        if requests_remaining is not None and requests_remaining <= 10:
            self.warn_rate_limit(requests_remaining, reset_dt)
        
        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_code = self.api_reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            self.api_response_content = None

            build_number = self.find_build_value.text()
            build_number = build_number.strip()

            if self.find_build_count == 0:
                status_bar.showMessage(_('Build #{build} not found on GitHub'
                    ).format(build=build_number))
                return
            elif self.find_build_count == 1:
                self.find_build()
                return

        self.api_response_content.seek(0)
        try:
            release = json.loads(TextIOWrapper(self.api_response_content, encoding='utf8'
                ).read())
        except json.decoder.JSONDecodeError:
            release = None
        self.api_response_content = None

        if release is None:
            return
        
        builds = self.builds

        asset_platform = self.base_asset['Platform']
        asset_graphics = self.base_asset['Graphics']

        target_regex = re.compile(r'cataclysmdda-(?P<major>.+)-' +
            re.escape(asset_platform) + r'-' +
            re.escape(asset_graphics) + r'-' +
            r'b?(?P<build>\d+)\.zip'
            )
        
        new_asset_platform = self.new_base_asset['Platform']
        new_asset_graphics = self.new_base_asset['Graphics']

        new_target_regex = re.compile(
            r'cdda-windows-' +
            re.escape(new_asset_graphics) + r'-' +
            re.escape(new_asset_platform) + r'-msvc-' +
            r'b?(?P<build>[0-9\-]+)\.zip'
            )

        build_regex = re.compile(r'[Bb]uild #?(?P<build>[0-9\-]+)')

        if any(x not in release for x in ('name', 'created_at')):
            return

        build_match = build_regex.search(release['name'])
        build_number = None
        if build_match is not None:
            asset = None
            if 'assets' in release:
                asset_iter = (
                    x for x in release['assets']
                    if 'browser_download_url' in x
                        and 'name' in x
                        and (
                            target_regex.search(x['name']) is not None or
                            new_target_regex.search(x['name']) is not None )
                )
                asset = next(asset_iter, None)

            build = {
                'url': asset['browser_download_url'] if asset is not None
                                                        else None,
                'name': asset['name'] if asset is not None else None,
                'number': build_match.group('build'),
                'date': arrow.get(release['created_at']).datetime
            }
            build_number = build['number']

            self.find_build_value.setText('')

            for existing_build in builds:
                if existing_build['number'] == build_number:
                    status_bar.showMessage(
                        _('Build #{build} is already in the available builds list'
                        ).format(build=build_number))
                    return

            builds.append(build)

            status_bar.showMessage(_('Build #{build} found and added to the available builds list'
                ).format(build=build_number))
        else:
            return

        if len(builds) > 0:
            builds.sort(key=lambda x: (x['date'], x['number']), reverse=True)
            self.builds = builds

            self.builds_combo.clear()
            for build in builds:
                if build['date'] is not None:
                    build_date = arrow.get(build['date'], 'UTC')
                    human_delta = safe_humanize(build_date, arrow.utcnow(),
                        locale=self.app_locale)
                else:
                    human_delta = _('Unknown')

                self.builds_combo.addItem(
                    '{number} ({delta})'.format(number=build['number'], delta=human_delta),
                    userData=build
                )

            combo_model = self.builds_combo.model()
            default_set = False
            for x in range(combo_model.rowCount()):
                if combo_model.item(x).data(Qt.UserRole)['url'] is None:
                    combo_model.item(x).setEnabled(False)
                    combo_model.item(x).setText(combo_model.item(x).text() +
                        _(' - build unavailable'))
                elif not default_set:
                    default_set = True
                    combo_model.item(x).setText(combo_model.item(x).text() +
                        _(' - latest build available'))

                if (combo_model.item(x).data(Qt.UserRole)['number'] == build_number and
                    combo_model.item(x).isEnabled()):
                    self.builds_combo.setCurrentIndex(x)
            self.find_build_count = 0
        elif self.find_build_count == 1:
            self.find_build()

    def find_build_ready_read(self):
        self.api_response_content.write(self.api_reply.readAll())

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
                    subdir_name = 'cdda'
                    subdir = os.path.join(game_dir, subdir_name)

                    while os.path.exists(subdir):
                        subdir_name = 'cdda-{0}'.format('%08x' % random.randrange(16**8))
                        subdir = os.path.join(game_dir, subdir_name)

                    new_subdirectory_msgbox = QMessageBox()
                    new_subdirectory_msgbox.setWindowTitle(_('Install directory is not empty'))
                    new_subdirectory_msgbox.setText(_('You cannot install the game in a directory '
                        'that is not empty. We can quickly proceed with a new subdirectory.'
                        ))
                    new_subdirectory_msgbox.setInformativeText(_('Can we create a new empty '
                        'subdirectory to proceed?'))
                    new_subdirectory_msgbox.addButton(_('Create the {name} subdirectory and '
                        'proceed').format(name=subdir_name),
                        QMessageBox.YesRole)
                    new_subdirectory_msgbox.addButton(_('I will choose or create a different '
                        'directory'), QMessageBox.NoRole)
                    new_subdirectory_msgbox.setIcon(QMessageBox.Question)

                    if new_subdirectory_msgbox.exec() == 1:
                        return
                    
                    os.makedirs(subdir)
                    game_dir = subdir
                    game_dir_group_box.set_dir_combo_value(subdir)

            if config_true(get_config_value('backup_before_update', 'False')):
                backups_tab = main_tab.get_backups_tab()

                backups_tab.prune_auto_backups()

                name = '{auto}_{name}'.format(auto=_('auto'),
                    name=_('before_update'))

                backups_tab.after_backup = self.update_game_process
                backups_tab.backup_saves(name)
            else:
                self.update_game_process()

        else:
            # We are currently updating, try to cancel

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

    def update_game_process(self):
        main_tab = self.get_main_tab()
        game_dir_group_box = main_tab.game_dir_group_box
        game_dir = game_dir_group_box.dir_combo.currentText()
        
        logger.info(
            'Updating CDDA...\n'
            'CDDAGL Directory: {}\n'
            'CDDA Directory: {}'
            .format(get_cddagl_path(), game_dir)
        )

        self.updating = True
        self.download_aborted = False
        self.clearing_previous_dir = False
        self.backing_up_game = False
        self.extracting_new_build = False
        self.analysing_new_build = False
        self.in_post_extraction = False

        self.selected_build = self.builds[self.builds_combo.currentIndex()]

        selected_branch = self.branch_button_group.checkedButton()
        experimental_selected = selected_branch is self.experimental_radio_button

        latest_build = self.builds[0]
        if experimental_selected and game_dir_group_box.current_build == latest_build['number']:
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
        self.stable_radio_button.setEnabled(False)
        self.experimental_radio_button.setEnabled(False)

        self.x64_radio_button.setEnabled(False)
        self.x86_radio_button.setEnabled(False)

        self.previous_bc_enabled = self.builds_combo.isEnabled()
        self.builds_combo.setEnabled(False)
        self.refresh_builds_button.setEnabled(False)
        self.find_build_value.setEnabled(False)
        self.find_build_button.setEnabled(False)

        self.previous_ub_enabled = self.update_button.isEnabled()
        if update_button:
            self.update_button.setEnabled(False)

    def enable_controls(self, builds_combo=False):
        self.stable_radio_button.setEnabled(True)
        self.experimental_radio_button.setEnabled(True)

        if is_64_windows():
            self.x64_radio_button.setEnabled(True)
        self.x86_radio_button.setEnabled(True)

        self.refresh_builds_button.setEnabled(True)
        self.find_build_value.setEnabled(True)
        self.find_build_button.setEnabled(True)

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

    def preserve_custom_fonts(self):
        """
        Copy over any files in the previous font directory
        that don't already exist in the current font directory.

        This assumes that fonts distributed with CDDA have already
        been extracted into the current font directory.
        """
        status_bar = self.get_main_window().statusBar()

        join_parts = lambda parts: Path(os.path.join(*parts))

        font_locations = [
            [self.game_dir, 'font'],        # User fonts
            [self.game_dir, 'data', 'font'] # Game fonts
        ]

        prev_font_locations = [
            [base, 'previous_version'] + parts for base, *parts in font_locations
        ]

        # A list of tuples with the shape (CURRENT_FONT_DIR, PREV_FONT_DIR)
        font_paths = list(tuple(
            zip(
                map(join_parts, font_locations),
                map(join_parts, prev_font_locations)
            )
        ))

        if (any(font_paths) and self.in_post_extraction):
            status_bar.showMessage(_('Restoring custom fonts'))

            for font_dir, prev_font_dir in font_paths:
                # Skip the dir if we have nothing to restore
                if not prev_font_dir.exists() or not prev_font_dir.is_dir():
                    continue

                # Determine if the current version includes any bundled fonts
                if font_dir.is_dir():
                    with os.scandir(font_dir) as entries:
                        current_set = set(entries)
                else:
                    # Create a new font directory if it doesn't already exist
                    font_dir.mkdir(exist_ok=True)
                    current_set = set()

                with os.scandir(prev_font_dir) as entries:
                    previous_set = set(entries)

                # Determine what font files need to be restored
                delta = previous_set - current_set

                for entry in delta:
                    source = prev_font_dir.joinpath(entry.name)
                    target =      font_dir.joinpath(entry.name)

                    if entry.is_file():
                        shutil.copy2(source, target)
                    elif entry.is_dir():
                        shutil.copytree(source, target)

            status_bar.clearMessage()

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
        user_default_mods_file = os.path.join(mods_dir, 'user-default-mods.json')
        previous_user_default_mods_file = os.path.join(previous_mods_dir, 'user-default-mods.json')

        if (not os.path.exists(user_default_mods_file)
            and os.path.isfile(previous_user_default_mods_file)):
            status_bar.showMessage(_('Restoring {0}').format('user-default-mods.json'))

            shutil.copy2(previous_user_default_mods_file,
                user_default_mods_file)

            status_bar.clearMessage()

        self.preserve_custom_fonts()

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

        self.downloading_size_label.setText(
            '{bytes_read}/{total_bytes}'
            .format(bytes_read=sizeof_fmt(bytes_read), total_bytes=sizeof_fmt(total_bytes))
        )

        if self.download_speed_count % 5 == 0:
            delta_bytes = bytes_read - self.download_last_bytes_read
            delta_time = datetime.utcnow() - self.download_last_read

            bytes_secs = delta_bytes / delta_time.total_seconds()
            self.dowloading_speed_label.setText(_('{bytes_sec}/s').format(
                bytes_sec=sizeof_fmt(bytes_secs)))

            self.download_last_bytes_read = bytes_read
            self.download_last_read = datetime.utcnow()

    def start_lb_request(self, base_asset, new_base_asset):
        self.disable_controls(True)
        self.refresh_warning_label.hide()
        self.find_build_warning_label.hide()

        main_window = self.get_main_window()

        status_bar = main_window.statusBar()
        status_bar.clearMessage()

        status_bar.busy += 1

        self.builds_combo.clear()
        self.builds_combo.addItem(_('Fetching remote builds'))

        url = cons.GITHUB_REST_API_URL + cons.CDDA_RELEASES
        self.base_asset = base_asset
        self.new_base_asset = new_base_asset

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

    def warn_rate_limit(self, requests_remaining, reset_dt):
        # Warn about remaining requests on GitHub API
        reset_dt_display = _('Unknown')
        if reset_dt is not None:
            reset_dt_local = reset_dt.astimezone(tz=None)
            reset_dt_display = format_datetime(reset_dt_local,
                format='long', locale=self.app_locale)

        message = _('You have {remaining} '
        'request(s) remaining for accessing GitHub API.\nYou will have to '
        'wait until {datetime} to get more requests.\nThose requests are '
        'needed to get the available builds.\nIf you keep running low on '
        'those remaining requests, avoid quickly refreshing often\n for the '
        'available builds. For more information, search GitHub API rate '
        'limiting.').format(
            remaining=requests_remaining,
            datetime=reset_dt_display
        )

        self.refresh_warning_label.show()
        self.refresh_warning_label.setToolTip(message)
        self.find_build_warning_label.setToolTip(message)

        selected_branch = self.branch_button_group.checkedButton()
        if selected_branch == self.experimental_radio_button:
            self.find_build_warning_label.show()

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
            self.warn_rate_limit(requests_remaining, reset_dt)

        status_code = self.http_reply.attribute(
            QNetworkRequest.HttpStatusCodeAttribute)
        if status_code != 200:
            reason = self.http_reply.attribute(
                QNetworkRequest.HttpReasonPhraseAttribute)
            url = self.http_reply.request().url().toString()
            msg = (
                _('Could not find launcher latest release when requesting {url}. Error: {error}')
                .format(url=url, error=f'[HTTP {status_code}] ({reason})')
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
            r'b?(?P<build>\d+)\.zip'
            )
        
        new_asset_platform = self.new_base_asset['Platform']
        new_asset_graphics = self.new_base_asset['Graphics']

        new_target_regex = re.compile(
            r'cdda-windows-' +
            re.escape(new_asset_graphics) + r'-' +
            re.escape(new_asset_platform) + r'-msvc-' +
            r'b?(?P<build>[0-9\-]+)\.zip'
            )

        build_regex = re.compile(r'[Bb]uild #?(?P<build>[0-9\-]+)')

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
                           and (
                               target_regex.search(x['name']) is not None or
                               new_target_regex.search(x['name']) is not None)
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
            builds.sort(key=lambda x: (x['date'], x['number']), reverse=True)
            self.builds = builds

            self.builds_combo.clear()
            for build in builds:
                if build['date'] is not None:
                    build_date = arrow.get(build['date'], 'UTC')
                    human_delta = safe_humanize(build_date, arrow.utcnow(),
                        locale=self.app_locale)
                else:
                    human_delta = _('Unknown')

                self.builds_combo.addItem(
                    '{number} ({delta})'.format(number=build['number'], delta=human_delta),
                    userData=build
                )

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
            else:
                self.previous_bc_enabled = True

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

    def show_hide_find_build(self):
        selected_branch = self.branch_button_group.checkedButton()

        widgets = (
            self.find_build_label,
            self.find_build_value,
            self.find_build_button
            )

        if selected_branch is self.stable_radio_button:
            for widget in widgets:
                widget.hide()
            self.find_build_warning_label.hide()
        elif selected_branch is self.experimental_radio_button:
            for widget in widgets:
                widget.show()
            if self.refresh_warning_label.isVisible():
                self.find_build_warning_label.show()

    def refresh_builds(self):
        selected_branch = self.branch_button_group.checkedButton()

        selected_platform = self.platform_button_group.checkedButton()

        if selected_platform is self.x64_radio_button:
            selected_platform = 'x64'
        elif selected_platform is self.x86_radio_button:
            selected_platform = 'x86'

        if selected_branch is self.stable_radio_button:
            # Populate stable builds and stable changelog

            # Add stable builds

            builds = []

            for stable_version in cons.STABLE_ASSETS:
                version_details = cons.STABLE_ASSETS[stable_version]

                build = {
                    'url': version_details['Tiles'][selected_platform],
                    'name': version_details['name'],
                    'number': version_details['number'],
                    'date': arrow.get(version_details['released_on']).datetime
                }
                builds.append(build)
            
            builds.sort(key=lambda x: (x['date'], x['number']), reverse=True)
            self.builds = builds

            self.builds_combo.clear()

            for build in builds:
                if build['date'] is not None:
                    build_date = arrow.get(build['date'], 'UTC')
                    human_delta = safe_humanize(build_date, arrow.utcnow(),
                        locale=self.app_locale)
                else:
                    human_delta = _('Unknown')

                self.builds_combo.addItem(
                    '{name} ({delta}) [{number}]'.format(name=build['name'], delta=human_delta,
                        number=build['number']), userData=build)
            
            main_tab = self.get_main_tab()
            game_dir_group_box = main_tab.game_dir_group_box

            if not game_dir_group_box.game_started:
                self.builds_combo.setEnabled(True)
            else:
                self.previous_bc_enabled = True

            if game_dir_group_box.exe_path is not None:
                self.update_button.setText(_('Update game'))
            else:
                self.update_button.setText(_('Install game'))

            # Populate stable changelog

            self.changelog_content.setHtml(cons.STABLE_CHANGELOG)

            
        elif selected_branch is self.experimental_radio_button:
            release_asset = cons.BASE_ASSETS['Tiles'][selected_platform]
            release_new_asset = cons.NEW_BASE_ASSETS['Tiles'][selected_platform]

            self.start_lb_request(release_asset, release_new_asset)
            self.refresh_changelog()

    def refresh_changelog(self):
        self.changelog_content.setHtml(_('<h3>Changelog is not available for experimental</h3>'))

    def branch_clicked(self, button):
        if button is self.stable_radio_button:
            config_value = cons.CONFIG_BRANCH_STABLE
        if button is self.experimental_radio_button:
            config_value = cons.CONFIG_BRANCH_EXPERIMENTAL
        
        set_config_value(cons.CONFIG_BRANCH_KEY, config_value)

        self.branch_changed()
    
    def branch_changed(self):
        # Perform branch change

        self.show_hide_find_build()

        # Change available builds and changelog
        self.refresh_builds()

    def platform_clicked(self, button):
        if button is self.x64_radio_button:
            config_value = 'x64'
        elif button is self.x86_radio_button:
            config_value = 'x86'

        set_config_value('platform', config_value)

        self.refresh_builds()


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
                                '{bytes_read}/{total_bytes}'
                                .format(bytes_read=sizeof_fmt(0),
                                        total_bytes=sizeof_fmt(self.total_copy_size))
                            )
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
                            '{bytes_read}/{total_bytes}'
                            .format(bytes_read=sizeof_fmt(self.copied_size),
                                    total_bytes=sizeof_fmt(self.total_copy_size))
                        )

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
