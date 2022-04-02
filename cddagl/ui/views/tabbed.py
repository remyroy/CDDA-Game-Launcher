# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import html
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from distutils.version import LooseVersion
from io import BytesIO, TextIOWrapper
from urllib.parse import urljoin

import markdown2
from PyQt5.QtCore import Qt, QUrl, pyqtSignal, QByteArray, QThread
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWidgets import (
    QGridLayout, QMainWindow, QLabel, QLineEdit, QPushButton, QProgressBar,
    QAction, QDialog, QTabWidget, QCheckBox, QMessageBox, QMenu
)
from PyQt5.QtGui import QDesktopServices
from pywintypes import error as PyWinError

import cddagl.constants as cons
from cddagl import __version__ as version
from cddagl.functions import sizeof_fmt, delete_path
from cddagl.i18n import proxy_gettext as _
from cddagl.sql.functions import get_config_value, set_config_value, config_true
from cddagl.ui.views.backups import BackupsTab
from cddagl.ui.views.dialogs import AboutDialog, FaqDialog
from cddagl.ui.views.fonts import FontsTab
from cddagl.ui.views.main import MainTab
from cddagl.ui.views.mods import ModsTab
from cddagl.ui.views.settings import SettingsTab
from cddagl.ui.views.soundpacks import SoundpacksTab
from cddagl.ui.views.tilesets import TilesetsTab
from cddagl.ui.views.statistics import StatisticsTab
from cddagl.win32 import SimpleNamedPipe

logger = logging.getLogger('cddagl')


class TabbedWindow(QMainWindow):
    def __init__(self, title):
        super(TabbedWindow, self).__init__()

        self.setMinimumSize(440, 540)

        self.create_status_bar()
        self.create_central_widget()
        self.create_menu()

        self.shown = False
        self.qnam = QNetworkAccessManager()
        self.http_reply = None
        self.in_manual_update_check = False

        self.faq_dialog = None
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
        self.faq_action.setText(_('&Frequently asked questions (FAQ)'))
        self.game_issue_action.setText(_('&Game issue'))
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

        faq_action = QAction(_('&Frequently asked questions (FAQ)'), self,
            triggered=self.show_faq_dialog)
        self.faq_action = faq_action
        self.help_menu.addAction(faq_action)

        self.help_menu.addSeparator()

        game_issue_action = QAction(_('&Game issue'), self,
            triggered=self.open_game_issue_url)
        self.game_issue_action = game_issue_action
        self.help_menu.addAction(game_issue_action)

        self.help_menu.addSeparator()

        update_action = QAction(_('&Check for update'), self,
            triggered=self.manual_update_check)
        self.update_action = update_action
        self.help_menu.addAction(update_action)

        about_action = QAction(_('&About CDDA Game Launcher'), self,
            triggered=self.show_about_dialog)
        self.about_action = about_action
        self.help_menu.addAction(about_action)

    def open_game_issue_url(self):
        QDesktopServices.openUrl(QUrl(cons.GAME_ISSUE_URL))

    def show_faq_dialog(self):
        if self.faq_dialog is None:
            faq_dialog = FaqDialog(self, Qt.WindowTitleHint |
                Qt.WindowCloseButtonHint)
            self.faq_dialog = faq_dialog

        self.faq_dialog.exec()

    def show_about_dialog(self):
        if self.about_dialog is None:
            about_dialog = AboutDialog(self, Qt.WindowTitleHint |
                Qt.WindowCloseButtonHint)
            self.about_dialog = about_dialog

        self.about_dialog.exec()

    def check_new_launcher_version(self):
        logger.info("Checking for new launcher version")
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
            logger.warning(
                _('Could not find launcher latest release when requesting {url}. Error: {error}')
                .format(url=url, error=f'[HTTP {status_code}] ({reason})')
            )

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

            html_desc = markdown2.markdown(markdown_desc)

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
        self.create_statistics_tab()

    def set_text(self):
        self.setTabText(self.indexOf(self.main_tab), _('Main'))
        self.setTabText(self.indexOf(self.backups_tab), _('Backups'))
        self.setTabText(self.indexOf(self.mods_tab), _('Mods'))
        #self.setTabText(self.indexOf(self.tilesets_tab), _('Tilesets'))
        self.setTabText(self.indexOf(self.soundpacks_tab), _('Soundpacks'))
        #self.setTabText(self.indexOf(self.fonts_tab), _('Fonts'))
        self.setTabText(self.indexOf(self.settings_tab), _('Settings'))
        self.setTabText(self.indexOf(self.statistics_tab), _('Statistics'))

        self.main_tab.set_text()
        self.backups_tab.set_text()
        self.mods_tab.set_text()
        #self.tilesets_tab.set_text()
        self.soundpacks_tab.set_text()
        #self.fonts_tab.set_text()
        self.settings_tab.set_text()
        self.statistics_tab.set_text()

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

    def create_statistics_tab(self):
        statistics_tab = StatisticsTab()
        self.addTab(statistics_tab, _('Statistics'))
        self.statistics_tab = statistics_tab


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
                subprocess.Popen([self.downloaded_file])

                self.updated = True
                self.done(0)

    def http_ready_read(self):
        self.downloading_file.write(self.http_reply.readAll())

    def dl_progress(self, bytes_read, total_bytes):
        self.progress_bar.setMaximum(total_bytes)
        self.progress_bar.setValue(bytes_read)

        self.download_speed_count += 1

        self.size_value_label.setText(
            '{bytes_read}/{total_bytes}'
            .format(bytes_read=sizeof_fmt(bytes_read), total_bytes=sizeof_fmt(total_bytes))
        )

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
