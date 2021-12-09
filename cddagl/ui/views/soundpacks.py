# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import html
import json
import logging
import os
import random
import shutil
import tempfile
import zipfile
from collections import deque
from datetime import datetime
from os import scandir
from urllib.parse import urljoin, urlencode

import rarfile
from PyQt5.QtCore import Qt, QTimer, QUrl, QFileInfo, QStringListModel
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QGroupBox, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTextBrowser, QTabWidget, QMessageBox, QHBoxLayout,
    QListView, QAbstractItemView, QTextEdit
)
from py7zlib import Archive7z, NoPasswordGivenError, FormatError

import cddagl.constants as cons
from cddagl import __version__ as version
from cddagl.constants import get_data_path, get_cddagl_path
from cddagl.functions import sizeof_fmt, delete_path
from cddagl.i18n import proxy_gettext as _
from cddagl.ui.views.dialogs import BrowserDownloadDialog

logger = logging.getLogger('cddagl')

rarfile.UNRAR_TOOL = get_cddagl_path('UnRAR.exe')


class SoundpacksTab(QTabWidget):
    def __init__(self):
        super(SoundpacksTab, self).__init__()

        self.tab_disabled = False

        self.qnam = QNetworkAccessManager()

        self.http_reply = None
        self.download_http_reply = None
        self.current_repo_info = None

        self.soundpacks = []
        self.soundpacks_model = None

        self.installing_new_soundpack = False
        self.downloading_new_soundpack = False
        self.extracting_new_soundpack = False

        self.close_after_install = False

        self.game_dir = None
        self.soundpacks_dir = None

        layout = QVBoxLayout()

        top_part = QWidget()
        tp_layout = QHBoxLayout()
        tp_layout.setContentsMargins(0, 0, 0, 0)
        self.tp_layout = tp_layout

        installed_gb = QGroupBox()
        tp_layout.addWidget(installed_gb)
        self.installed_gb = installed_gb

        installed_gb_layout = QVBoxLayout()
        installed_gb.setLayout(installed_gb_layout)
        self.installed_gb_layout = installed_gb_layout

        installed_lv = QListView()
        installed_lv.clicked.connect(self.installed_clicked)
        installed_lv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        installed_gb_layout.addWidget(installed_lv)
        self.installed_lv = installed_lv

        installed_buttons = QWidget()
        ib_layout = QHBoxLayout()
        installed_buttons.setLayout(ib_layout)
        ib_layout.setContentsMargins(0, 0, 0, 0)
        self.ib_layout = ib_layout
        self.installed_buttons = installed_buttons
        installed_gb_layout.addWidget(installed_buttons)

        disable_existing_button = QPushButton()
        disable_existing_button.clicked.connect(self.disable_existing)
        disable_existing_button.setEnabled(False)
        ib_layout.addWidget(disable_existing_button)
        self.disable_existing_button = disable_existing_button

        delete_existing_button = QPushButton()
        delete_existing_button.clicked.connect(self.delete_existing)
        delete_existing_button.setEnabled(False)
        ib_layout.addWidget(delete_existing_button)
        self.delete_existing_button = delete_existing_button

        repository_gb = QGroupBox()
        tp_layout.addWidget(repository_gb)
        self.repository_gb = repository_gb

        repository_gb_layout = QVBoxLayout()
        repository_gb.setLayout(repository_gb_layout)
        self.repository_gb_layout = repository_gb_layout

        repository_lv = QListView()
        repository_lv.clicked.connect(self.repository_clicked)
        repository_lv.setEditTriggers(QAbstractItemView.NoEditTriggers)
        repository_gb_layout.addWidget(repository_lv)
        self.repository_lv = repository_lv

        suggest_new_label = QLabel()
        suggest_new_label.setOpenExternalLinks(True)
        repository_gb_layout.addWidget(suggest_new_label)
        self.suggest_new_label = suggest_new_label

        install_new_button = QPushButton()
        install_new_button.clicked.connect(self.install_new)
        install_new_button.setEnabled(False)
        repository_gb_layout.addWidget(install_new_button)
        self.install_new_button = install_new_button

        top_part.setLayout(tp_layout)
        layout.addWidget(top_part)
        self.top_part = top_part

        details_gb = QGroupBox()
        layout.addWidget(details_gb)
        self.details_gb = details_gb

        details_gb_layout = QGridLayout()

        viewname_label = QLabel()
        details_gb_layout.addWidget(viewname_label, 0, 0, Qt.AlignRight)
        self.viewname_label = viewname_label

        viewname_le = QLineEdit()
        viewname_le.setReadOnly(True)
        details_gb_layout.addWidget(viewname_le, 0, 1)
        self.viewname_le = viewname_le

        name_label = QLabel()
        details_gb_layout.addWidget(name_label, 1, 0, Qt.AlignRight)
        self.name_label = name_label

        name_le = QLineEdit()
        name_le.setReadOnly(True)
        details_gb_layout.addWidget(name_le, 1, 1)
        self.name_le = name_le

        path_label = QLabel()
        details_gb_layout.addWidget(path_label, 2, 0, Qt.AlignRight)
        self.path_label = path_label

        path_le = QLineEdit()
        path_le.setReadOnly(True)
        details_gb_layout.addWidget(path_le, 2, 1)
        self.path_le = path_le

        size_label = QLabel()
        details_gb_layout.addWidget(size_label, 3, 0, Qt.AlignRight)
        self.size_label = size_label

        size_le = QLineEdit()
        size_le.setReadOnly(True)
        details_gb_layout.addWidget(size_le, 3, 1)
        self.size_le = size_le

        homepage_label = QLabel()
        details_gb_layout.addWidget(homepage_label, 4, 0, Qt.AlignRight)
        self.homepage_label = homepage_label

        homepage_tb = QTextBrowser()
        homepage_tb.setReadOnly(True)
        homepage_tb.setOpenExternalLinks(True)
        homepage_tb.setMaximumHeight(23)
        homepage_tb.setLineWrapMode(QTextEdit.NoWrap)
        homepage_tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        details_gb_layout.addWidget(homepage_tb, 4, 1)
        self.homepage_tb = homepage_tb

        details_gb.setLayout(details_gb_layout)
        self.details_gb_layout = details_gb_layout

        self.setLayout(layout)

        self.load_repository()
        self.set_text()

    def set_text(self):
        self.installed_gb.setTitle(_('Installed'))
        self.disable_existing_button.setText(_('Disable'))
        self.delete_existing_button.setText(_('Delete'))
        self.repository_gb.setTitle(_('Repository'))
        suggest_url = cons.NEW_ISSUE_URL + '?' + urlencode({
            'title': _('Add this new soundpack to the repository'),
            'body': _('''* Name: [Enter the name of the soundpack]
* Url: [Enter the Url where we can find the soundpack]
* Author: [Enter the name of the author]
* Homepage: [Enter the Url of the author website or where the soundpack was published]
* Soundpack not found in version: {version}
''').format(version=version)
        })
        self.suggest_new_label.setText(
            _('<a href="{url}">Suggest a new soundpack '
            'on GitHub</a>').format(url=suggest_url))
        self.install_new_button.setText(_('Install this soundpack'))
        self.details_gb.setTitle(_('Details'))
        self.viewname_label.setText(_('View name:'))
        self.name_label.setText(_('Name:'))

        selection_model = self.repository_lv.selectionModel()
        if selection_model is not None and selection_model.hasSelection():
            self.path_label.setText(_('Url:'))
        else:
            self.path_label.setText(_('Path:'))

        self.size_label.setText(_('Size:'))
        self.homepage_label.setText(_('Home page:'))

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab

    def get_mods_tab(self):
        return self.get_main_tab().get_mods_tab()

    def get_settings_tab(self):
        return self.get_main_tab().get_settings_tab()

    def get_backups_tab(self):
        return self.get_main_tab().get_backups_tab()

    def disable_tab(self):
        self.tab_disabled = True

        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)

        self.install_new_button.setEnabled(False)

        installed_selection = self.installed_lv.selectionModel()
        if installed_selection is not None:
            installed_selection.clearSelection()

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()

    def enable_tab(self):
        self.tab_disabled = False

        installed_selection = self.installed_lv.selectionModel()
        if installed_selection is None:
            installed_selected = False
        else:
            installed_selected = installed_selection.hasSelection()

        self.disable_existing_button.setEnabled(installed_selected)
        self.delete_existing_button.setEnabled(installed_selected)

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is None:
            repository_selected = False
        else:
            repository_selected = repository_selection.hasSelection()

        self.install_new_button.setEnabled(repository_selected)

    def load_repository(self):
        self.repo_soundpacks = []

        self.install_new_button.setEnabled(False)

        self.repo_soundpacks_model = QStringListModel()
        self.repository_lv.setModel(self.repo_soundpacks_model)
        self.repository_lv.selectionModel().currentChanged.connect(
            self.repository_selection)

        json_file = get_data_path('soundpacks.json')

        if os.path.isfile(json_file):
            with open(json_file, 'r', encoding='utf8') as f:
                try:
                    values = json.load(f)
                    if isinstance(values, list):
                        values.sort(key=lambda x: x['name'])
                        self.repo_soundpacks = values

                        self.repo_soundpacks_model.insertRows(
                            self.repo_soundpacks_model.rowCount(),
                            len(self.repo_soundpacks))
                        for index, soundpack_info in enumerate(
                            self.repo_soundpacks):
                            self.repo_soundpacks_model.setData(
                                self.repo_soundpacks_model.index(index),
                                soundpack_info['viewname'])
                except ValueError:
                    pass

    def install_new(self):
        if not self.installing_new_soundpack:
            selection_model = self.repository_lv.selectionModel()
            if selection_model is None or not selection_model.hasSelection():
                return

            selected = selection_model.currentIndex()
            selected_info = self.repo_soundpacks[selected.row()]

            # Is it already installed?
            for soundpack in self.soundpacks:
                if soundpack['NAME'] == selected_info['name']:
                    confirm_msgbox = QMessageBox()
                    confirm_msgbox.setWindowTitle(_('Soundpack already present'
                        ))
                    confirm_msgbox.setText(_('It seems this soundpack is '
                        'already installed. The launcher will not overwrite '
                        'the soundpack if it has the same directory name. You '
                        'might want to delete the soundpack first if you want '
                        'to update it. Also, there can only be a single '
                        'soundpack with the same name value available in the '
                        'game.'))
                    confirm_msgbox.setInformativeText(_('Are you sure you want '
                        'to install the {view} soundpack?').format(
                            view=selected_info['viewname']))
                    confirm_msgbox.addButton(_('Install the soundpack'),
                        QMessageBox.YesRole)
                    confirm_msgbox.addButton(_('Do not install again'),
                        QMessageBox.NoRole)
                    confirm_msgbox.setIcon(QMessageBox.Warning)

                    if confirm_msgbox.exec() == 1:
                        return
                    break

            self.install_type = selected_info['type']

            if selected_info['type'] == 'direct_download':
                if self.http_reply is not None and self.http_reply.isRunning():
                    self.http_reply_aborted = True
                    self.http_reply.abort()

                self.installing_new_soundpack = True
                self.download_aborted = False

                download_dir = tempfile.mkdtemp(prefix=cons.TEMP_PREFIX)

                download_url = selected_info['url']

                url = QUrl(download_url)
                file_info = QFileInfo(url.path())
                file_name = file_info.fileName()

                self.downloaded_file = os.path.join(download_dir, file_name)
                self.downloading_file = open(self.downloaded_file, 'wb')

                main_window = self.get_main_window()

                status_bar = main_window.statusBar()
                status_bar.clearMessage()

                status_bar.busy += 1

                downloading_label = QLabel()
                downloading_label.setText(_('Downloading: {0}').format(
                    selected_info['url']))
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

                self.downloading_new_soundpack = True

                request = QNetworkRequest(QUrl(url))
                request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

                self.download_http_reply = self.qnam.get(request)
                self.download_http_reply.finished.connect(
                    self.download_http_finished)
                self.download_http_reply.readyRead.connect(
                    self.download_http_ready_read)
                self.download_http_reply.downloadProgress.connect(
                    self.download_dl_progress)

                self.install_new_button.setText(_('Cancel soundpack '
                    'installation'))
                self.installed_lv.setEnabled(False)
                self.repository_lv.setEnabled(False)

                self.get_main_tab().disable_tab()
                self.get_mods_tab().disable_tab()
                self.get_settings_tab().disable_tab()
                self.get_backups_tab().disable_tab()
            elif selected_info['type'] == 'browser_download':
                bd_dialog = BrowserDownloadDialog('soundpack',
                    selected_info['url'], selected_info.get('expected_filename',
                        None))
                bd_dialog.exec()

                if bd_dialog.downloaded_path is not None:
                    self.installing_new_soundpack = True
                    self.downloaded_file = bd_dialog.downloaded_path

                    self.install_new_button.setText(_('Cancel soundpack '
                        'installation'))
                    self.installed_lv.setEnabled(False)
                    self.repository_lv.setEnabled(False)

                    self.get_main_tab().disable_tab()
                    self.get_mods_tab().disable_tab()
                    self.get_settings_tab().disable_tab()
                    self.get_backups_tab().disable_tab()

                    main_window = self.get_main_window()
                    status_bar = main_window.statusBar()

                    # Test downloaded file
                    status_bar.showMessage(_('Testing downloaded file archive'))

                    if self.downloaded_file.lower().endswith('.7z'):
                        try:
                            with open(self.downloaded_file, 'rb') as f:
                                archive = Archive7z(f)
                        except FormatError:
                            status_bar.clearMessage()
                            status_bar.showMessage(_('Selected file is a '
                                'bad archive file'))

                            self.finish_install_new_soundpack()
                            return
                        except NoPasswordGivenError:
                            status_bar.clearMessage()
                            status_bar.showMessage(_('Selected file is a '
                                'password protected archive file'))

                            self.finish_install_new_soundpack()
                            return
                    else:
                        archive_exception = None
                        if self.downloaded_file.lower().endswith('.zip'):
                            archive_class = zipfile.ZipFile
                            archive_exception = zipfile.BadZipFile
                            test_method = 'testzip'
                        elif self.downloaded_file.lower().endswith('.rar'):
                            archive_class = rarfile.RarFile
                            archive_exception = rarfile.Error
                            test_method = 'testrar'
                        else:
                            extension = os.path.splitext(self.downloaded_file
                                )[1]
                            status_bar.clearMessage()
                            status_bar.showMessage(
                                _('Unknown downloaded archive format '
                                '({extension})').format(extension=extension))

                            self.finish_install_new_soundpack()
                            return

                        try:
                            with archive_class(self.downloaded_file) as z:
                                test = getattr(z, test_method)
                                if test() is not None:
                                    status_bar.clearMessage()
                                    status_bar.showMessage(
                                        _('Downloaded archive is invalid'))

                                    self.finish_install_new_soundpack()
                                    return
                        except archive_exception:
                            status_bar.clearMessage()
                            status_bar.showMessage(_('Selected file is a '
                                'bad archive file'))

                            self.finish_install_new_soundpack()
                            return

                    status_bar.clearMessage()
                    self.extract_new_soundpack()

        else:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            # Cancel installation
            if self.downloading_new_soundpack:
                self.download_aborted = True
                self.download_http_reply.abort()
            elif self.extracting_new_soundpack:
                self.extracting_timer.stop()

                status_bar.removeWidget(self.extracting_label)
                status_bar.removeWidget(self.extracting_progress_bar)

                status_bar.busy -= 1

                self.extracting_new_soundpack = False

                self.extracting_zipfile.close()

                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)

                if os.path.isdir(self.extract_dir):
                    delete_path(self.extract_dir)

            status_bar.showMessage(_('Soundpack installation cancelled'))

            self.finish_install_new_soundpack()

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

            self.downloading_new_soundpack = False
        else:
            redirect = self.download_http_reply.attribute(
                QNetworkRequest.RedirectionTargetAttribute)
            if redirect is not None:
                download_dir = os.path.dirname(self.downloaded_file)
                delete_path(download_dir)
                os.makedirs(download_dir)

                self.downloading_file = open(self.downloaded_file, 'wb')

                status_bar.busy += 1

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

                progress_bar.setValue(0)

                request = QNetworkRequest(QUrl(redirected_url))
                request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

                self.download_http_reply = self.qnam.get(request)
                self.download_http_reply.finished.connect(
                    self.download_http_finished)
                self.download_http_reply.readyRead.connect(
                    self.download_http_ready_read)
                self.download_http_reply.downloadProgress.connect(
                    self.download_dl_progress)
            else:
                # Test downloaded file
                status_bar.showMessage(_('Testing downloaded file archive'))

                if self.downloaded_file.lower().endswith('.7z'):
                    try:
                        with open(self.downloaded_file, 'rb') as f:
                            archive = Archive7z(f)
                    except FormatError:
                        status_bar.clearMessage()
                        status_bar.showMessage(_('Selected file is a '
                            'bad archive file'))

                        self.finish_install_new_soundpack()
                        return
                    except NoPasswordGivenError:
                        status_bar.clearMessage()
                        status_bar.showMessage(_('Selected file is a '
                            'password protected archive file'))

                        self.finish_install_new_soundpack()
                        return
                else:
                    archive_exception = None
                    if self.downloaded_file.lower().endswith('.zip'):
                        archive_class = zipfile.ZipFile
                        archive_exception = zipfile.BadZipFile
                        test_method = 'testzip'
                    elif self.downloaded_file.lower().endswith('.rar'):
                        archive_class = rarfile.RarFile
                        archive_exception = rarfile.Error
                        test_method = 'testrar'
                    else:
                        extension = os.path.splitext(self.downloaded_file)[1]
                        status_bar.clearMessage()
                        status_bar.showMessage(
                            _('Unknown downloaded archive format ({extension})'
                            ).format(extension=extension))

                        self.finish_install_new_soundpack()
                        return

                    try:
                        with archive_class(self.downloaded_file) as z:
                            test = getattr(z, test_method)
                            if test() is not None:
                                status_bar.clearMessage()
                                status_bar.showMessage(
                                    _('Downloaded archive is invalid'))

                                self.finish_install_new_soundpack()
                                return
                    except archive_exception:
                        status_bar.clearMessage()
                        status_bar.showMessage(_('Selected file is a '
                            'bad archive file'))

                        self.finish_install_new_soundpack()
                        return

                status_bar.clearMessage()
                self.downloading_new_soundpack = False
                self.extract_new_soundpack()

    def finish_install_new_soundpack(self):
        self.installing_new_soundpack = False

        self.installed_lv.setEnabled(True)
        self.repository_lv.setEnabled(True)

        self.install_new_button.setText(_('Install this soundpack'))

        self.get_main_tab().enable_tab()
        self.get_mods_tab().enable_tab()
        self.get_settings_tab().enable_tab()
        self.get_backups_tab().enable_tab()

        if self.close_after_install:
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

    def extract_new_soundpack(self):
        self.extracting_new_soundpack = True

        if self.downloaded_file.lower().endswith('.7z'):
            self.extracting_zipfile = open(self.downloaded_file, 'rb')
            self.extracting_archive = Archive7z(self.extracting_zipfile)

            self.extracting_infolist = self.extracting_archive.getmembers()
        else:
            if self.downloaded_file.lower().endswith('.zip'):
                archive_class = zipfile.ZipFile
            elif self.downloaded_file.lower().endswith('.rar'):
                archive_class = rarfile.RarFile

            z = archive_class(self.downloaded_file)
            self.extracting_zipfile = z

            self.extracting_infolist = z.infolist()

        self.extract_dir = os.path.join(self.game_dir, 'newsoundpack')
        while os.path.exists(self.extract_dir):
            self.extract_dir = os.path.join(self.game_dir,
                'newsoundpack-{0}'.format('%08x' % random.randrange(16**8)))
        os.makedirs(self.extract_dir)

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

                self.extracting_new_soundpack = False

                self.extracting_zipfile.close()
                self.extracting_zipfile = None

                if self.downloaded_file.lower().endswith('.7z'):
                    self.extracting_archive = None

                if self.install_type == 'direct_download':
                    download_dir = os.path.dirname(self.downloaded_file)
                    delete_path(download_dir)

                self.move_new_soundpack()

            else:
                extracting_element = self.extracting_infolist[
                    self.extracting_index]

                self.extracting_label.setText(_('Extracting {0}').format(
                    extracting_element.filename))

                if self.downloaded_file.lower().endswith('.7z'):
                    destination = os.path.join(self.extract_dir,
                        *extracting_element.filename.split('/'))
                    dest_dir = os.path.dirname(destination)
                    if not os.path.isdir(dest_dir):
                        os.makedirs(dest_dir)
                    with open(destination, 'wb') as f:
                        f.write(extracting_element.read())
                else:
                    self.extracting_zipfile.extract(extracting_element,
                        self.extract_dir)

                self.extracting_index += 1

        timer.timeout.connect(timeout)
        timer.start(0)

    def move_new_soundpack(self):
        # Find the soundpack in the self.extract_dir
        # Move the soundpack from that location into self.soundpacks_dir

        self.moving_new_soundpack = True

        main_window = self.get_main_window()
        status_bar = main_window.statusBar()

        status_bar.showMessage(_('Finding the soundpack'))

        next_scans = deque()
        current_scan = scandir(self.extract_dir)

        soundpack_dir = None

        while True:
            try:
                entry = next(current_scan)
                if entry.is_dir():
                    next_scans.append(entry.path)
                elif entry.is_file():
                    dirname, basename = os.path.split(entry.path)
                    if basename == 'soundpack.txt':
                        soundpack_dir = dirname
                        entry = None
                        break
            except StopIteration:
                if len(next_scans) > 0:
                    current_scan = scandir(next_scans.popleft())
                else:
                    break

        for item in current_scan:
            pass

        if soundpack_dir is None:
            status_bar.showMessage(_('Soundpack installation cancelled - There '
                'is no soundpack in the downloaded archive'))
            delete_path(self.extract_dir)
            self.moving_new_soundpack = False

            self.finish_install_new_soundpack()
        else:
            soundpack_dir_name = os.path.basename(soundpack_dir)
            target_dir = os.path.join(self.soundpacks_dir, soundpack_dir_name)
            if os.path.exists(target_dir):
                status_bar.showMessage(_('Soundpack installation cancelled - '
                    'There is already a {basename} directory in '
                    '{soundpacks_dir}').format(basename=soundpack_dir_name,
                        soundpacks_dir=self.soundpacks_dir))
            else:
                shutil.move(soundpack_dir, self.soundpacks_dir)
                status_bar.showMessage(_('Soundpack installation completed'))

            delete_path(self.extract_dir)
            self.moving_new_soundpack = False

            self.game_dir_changed(self.game_dir)
            self.finish_install_new_soundpack()

    def disable_existing(self):
        selection_model = self.installed_lv.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            return

        selected = selection_model.currentIndex()
        selected_info = self.soundpacks[selected.row()]

        if selected_info['enabled']:
            config_file = os.path.join(selected_info['path'], 'soundpack.txt')
            new_config_file = os.path.join(selected_info['path'],
                'soundpack.txt.disabled')
            try:
                shutil.move(config_file, new_config_file)
                selected_info['enabled'] = False
                self.soundpacks_model.setData(selected, selected_info['VIEW'] +
                    _(' (Disabled)'))
                self.disable_existing_button.setText(_('Enable'))
            except OSError as e:
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(str(e))
        else:
            config_file = os.path.join(selected_info['path'],
                'soundpack.txt.disabled')
            new_config_file = os.path.join(selected_info['path'],
                'soundpack.txt')
            try:
                shutil.move(config_file, new_config_file)
                selected_info['enabled'] = True
                self.soundpacks_model.setData(selected, selected_info['VIEW'])
                self.disable_existing_button.setText(_('Disable'))
            except OSError as e:
                main_window = self.get_main_window()
                status_bar = main_window.statusBar()

                status_bar.showMessage(str(e))

    def delete_existing(self):
        selection_model = self.installed_lv.selectionModel()
        if selection_model is None or not selection_model.hasSelection():
            return

        selected = selection_model.currentIndex()
        selected_info = self.soundpacks[selected.row()]

        confirm_msgbox = QMessageBox()
        confirm_msgbox.setWindowTitle(_('Delete soundpack'))
        confirm_msgbox.setText(_('This will delete the soundpack directory. It '
            'cannot be undone.'))
        confirm_msgbox.setInformativeText(_('Are you sure you want to '
            'delete the {view} soundpack?').format(view=selected_info['VIEW']))
        confirm_msgbox.addButton(_('Delete the soundpack'),
            QMessageBox.YesRole)
        confirm_msgbox.addButton(_('I want to keep the soundpack'),
            QMessageBox.NoRole)
        confirm_msgbox.setIcon(QMessageBox.Warning)

        if confirm_msgbox.exec() == 0:
            main_window = self.get_main_window()
            status_bar = main_window.statusBar()

            if not delete_path(selected_info['path']):
                status_bar.showMessage(_('Soundpack deletion cancelled'))
            else:
                self.soundpacks_model.removeRows(selected.row(), 1)
                self.soundpacks.remove(selected_info)

                status_bar.showMessage(_('Soundpack deleted'))

    def installed_selection(self, selected, previous):
        self.installed_clicked()

    def installed_clicked(self):
        selection_model = self.installed_lv.selectionModel()
        if selection_model is not None and selection_model.hasSelection():
            selected = selection_model.currentIndex()
            selected_info = self.soundpacks[selected.row()]

            self.viewname_le.setText(selected_info['VIEW'])
            self.name_le.setText(selected_info['NAME'])
            self.path_label.setText(_('Path:'))
            self.path_le.setText(selected_info['path'])
            self.size_le.setText(sizeof_fmt(selected_info['size']))
            self.homepage_tb.setText('')

            if selected_info['enabled']:
                self.disable_existing_button.setText(_('Disable'))
            else:
                self.disable_existing_button.setText(_('Enable'))

        if not self.tab_disabled:
            self.disable_existing_button.setEnabled(True)
            self.delete_existing_button.setEnabled(True)

        self.install_new_button.setEnabled(False)

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()

    def repository_selection(self, selected, previous):
        self.repository_clicked()

    def repository_clicked(self):
        selection_model = self.repository_lv.selectionModel()
        if selection_model is not None and selection_model.hasSelection():
            selected = selection_model.currentIndex()
            selected_info = self.repo_soundpacks[selected.row()]

            self.viewname_le.setText(selected_info['viewname'])
            self.name_le.setText(selected_info['name'])

            if selected_info['type'] == 'direct_download':
                self.path_label.setText(_('Url:'))
                self.path_le.setText(selected_info['url'])
                self.homepage_tb.setText('<a href="{url}">{url}</a>'.format(
                    url=html.escape(selected_info['homepage'])))
                if 'size' not in selected_info:
                    if not (self.current_repo_info is not None
                        and self.http_reply is not None
                        and self.http_reply.isRunning()
                        and self.current_repo_info is selected_info):
                        if (self.http_reply is not None
                            and self.http_reply.isRunning()):
                            self.http_reply_aborted = True
                            self.http_reply.abort()

                        self.http_reply_aborted = False
                        self.size_le.setText(_('Getting remote size'))
                        self.current_repo_info = selected_info

                        request = QNetworkRequest(QUrl(selected_info['url']))
                        request.setRawHeader(b'User-Agent', cons.FAKE_USER_AGENT)

                        self.http_reply = self.qnam.head(request)
                        self.http_reply.finished.connect(
                            self.size_query_finished)
                else:
                    self.size_le.setText(sizeof_fmt(selected_info['size']))
            elif selected_info['type'] == 'browser_download':
                self.path_label.setText(_('Url:'))
                self.path_le.setText(selected_info['url'])
                self.homepage_tb.setText('<a href="{url}">{url}</a>'.format(
                    url=html.escape(selected_info['homepage'])))
                if 'size' in selected_info:
                    self.size_le.setText(sizeof_fmt(selected_info['size']))
                else:
                    self.size_le.setText(_('Unknown'))

        if (self.soundpacks_dir is not None
            and os.path.isdir(self.soundpacks_dir)
            and not self.tab_disabled):
            self.install_new_button.setEnabled(True)
        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)

        installed_selection = self.installed_lv.selectionModel()
        if installed_selection is not None:
            installed_selection.clearSelection()

    def size_query_finished(self):
        if (not self.http_reply_aborted
            and self.http_reply.attribute(
                QNetworkRequest.HttpStatusCodeAttribute) == 200
            and self.http_reply.hasRawHeader(b'Content-Length')):

            content_length = int(self.http_reply.rawHeader(b'Content-Length'))
            self.current_repo_info['size'] = content_length

            selection_model = self.repository_lv.selectionModel()
            if selection_model is not None and selection_model.hasSelection():
                selected = selection_model.currentIndex()
                selected_info = self.repo_soundpacks[selected.row()]

                if selected_info is self.current_repo_info:
                    self.size_le.setText(sizeof_fmt(content_length))
        else:
            selection_model = self.repository_lv.selectionModel()
            if selection_model is not None and selection_model.hasSelection():
                selected = selection_model.currentIndex()
                selected_info = self.repo_soundpacks[selected.row()]

                if selected_info is self.current_repo_info:
                    self.size_le.setText(_('Unknown'))

    def config_info(self, config_file):
        val = {}
        try:
            with open(config_file, 'r', encoding='latin1') as f:
                for line in f:
                    if line.startswith('NAME'):
                        space_index = line.find(' ')
                        name = line[space_index:].strip().replace(
                            ',', '')
                        val['NAME'] = name
                    elif line.startswith('VIEW'):
                        space_index = line.find(' ')
                        view = line[space_index:].strip()
                        val['VIEW'] = view

                    if 'NAME' in val and 'VIEW' in val:
                        break
        except FileNotFoundError:
            return val
        return val

    def scan_size(self, soundpack_info):
        next_scans = deque()
        current_scan = scandir(soundpack_info['path'])

        total_size = 0

        while True:
            try:
                entry = next(current_scan)
                if entry.is_dir():
                    next_scans.append(entry.path)
                elif entry.is_file():
                    total_size += entry.stat().st_size
            except StopIteration:
                if len(next_scans) > 0:
                    current_scan = scandir(next_scans.popleft())
                else:
                    break

        return total_size

    def add_soundpack(self, soundpack_info):
        index = self.soundpacks_model.rowCount()
        self.soundpacks_model.insertRows(self.soundpacks_model.rowCount(), 1)
        disabled_text = ''
        if not soundpack_info['enabled']:
            disabled_text = _(' (Disabled)')
        self.soundpacks_model.setData(self.soundpacks_model.index(index),
            soundpack_info['VIEW'] + disabled_text)

    def clear_soundpacks(self):
        self.game_dir = None
        self.soundpacks = []

        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)
        self.install_new_button.setEnabled(False)

        if self.soundpacks_model is not None:
            self.soundpacks_model.setStringList([])
        self.soundpacks_model = None

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()

        self.viewname_le.setText('')
        self.name_le.setText('')
        self.path_le.setText('')
        self.size_le.setText('')
        self.homepage_tb.setText('')

    def game_dir_changed(self, new_dir):
        self.game_dir = new_dir
        self.soundpacks = []

        self.disable_existing_button.setEnabled(False)
        self.delete_existing_button.setEnabled(False)

        self.soundpacks_model = QStringListModel()
        self.installed_lv.setModel(self.soundpacks_model)
        self.installed_lv.selectionModel().currentChanged.connect(
            self.installed_selection)

        repository_selection = self.repository_lv.selectionModel()
        if repository_selection is not None:
            repository_selection.clearSelection()
        self.install_new_button.setEnabled(False)

        self.viewname_le.setText('')
        self.name_le.setText('')
        self.path_le.setText('')
        self.size_le.setText('')
        self.homepage_tb.setText('')

        soundpacks_dir = os.path.join(new_dir, 'data', 'sound')
        if os.path.isdir(soundpacks_dir):
            self.soundpacks_dir = soundpacks_dir

            dir_scan = scandir(soundpacks_dir)

            while True:
                try:
                    entry = next(dir_scan)
                    if entry.is_dir():
                        soundpack_path = entry.path
                        config_file = os.path.join(soundpack_path,
                            'soundpack.txt')
                        if os.path.isfile(config_file):
                            info = self.config_info(config_file)
                            if 'NAME' in info and 'VIEW' in info:
                                soundpack_info = {
                                    'path': soundpack_path,
                                    'enabled': True
                                }
                                soundpack_info.update(info)

                                self.soundpacks.append(soundpack_info)
                                soundpack_info['size'] = (
                                    self.scan_size(soundpack_info))
                                self.add_soundpack(soundpack_info)
                                continue
                        disabled_config_file = os.path.join(soundpack_path,
                            'soundpack.txt.disabled')
                        if os.path.isfile(disabled_config_file):
                            info = self.config_info(disabled_config_file)
                            if 'NAME' in info and 'VIEW' in info:
                                soundpack_info = {
                                    'path': soundpack_path,
                                    'enabled': False
                                }
                                soundpack_info.update(info)

                                self.soundpacks.append(soundpack_info)
                                soundpack_info['size'] = (
                                    self.scan_size(soundpack_info))
                                self.add_soundpack(soundpack_info)

                except StopIteration:
                    break
        else:
            self.soundpacks_dir = None
