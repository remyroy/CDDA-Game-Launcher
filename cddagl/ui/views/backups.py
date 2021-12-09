# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import html
import json
import logging
import os
import random
import zipfile
from collections import deque
from datetime import datetime, timedelta
from os import scandir

import arrow
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, QItemSelectionModel, QItemSelection
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QGroupBox, QLabel, QLineEdit, QPushButton,
    QProgressBar, QTabWidget, QCheckBox, QMessageBox, QStyle, QHBoxLayout, QSpinBox,
    QAbstractItemView, QSizePolicy, QTableWidget, QTableWidgetItem
)
from babel.dates import format_datetime
from babel.numbers import format_percent

import cddagl.constants as cons
from cddagl.functions import sizeof_fmt, safe_filename, alphanum_key, delete_path, safe_humanize
from cddagl.i18n import proxy_gettext as _
from cddagl.sql.functions import get_config_value, set_config_value, config_true
from cddagl.win32 import find_process_with_file_handle

logger = logging.getLogger('cddagl')


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

        backup_before_update_cb = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'backup_before_update', 'False')) else Qt.Unchecked)
        backup_before_update_cb.setCheckState(check_state)
        backup_before_update_cb.stateChanged.connect(self.bbu_changed)
        automatic_backups_layout.addWidget(backup_before_update_cb, 2, 0)
        self.backup_before_update_cb = backup_before_update_cb

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
        automatic_backups_layout.addWidget(mab_group, 3, 0, 1, 2)
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
        self.backup_before_update_cb.setText(_('Backup saves before updating'))

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
    
    def bbu_changed(self, state):
        set_config_value('backup_before_update', str(state != Qt.Unchecked))

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
            '{bytes_read}/{total_bytes}'
            .format(bytes_read=sizeof_fmt(0), total_bytes=sizeof_fmt(self.total_extract_size))
        )
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
                '{bytes_read}/{total_bytes}'
                .format(bytes_read=sizeof_fmt(self.extract_size),
                        total_bytes=sizeof_fmt(self.total_extract_size))
            )

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
        if self.game_dir is None:
            return
        
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

        if self.game_dir is None:
            status_bar.showMessage(_('Game directory not found'))
            if self.after_backup is not None:
                self.after_backup()
                self.after_backup = None
            return

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
                            '{bytes_read}/{total_bytes}'
                            .format(bytes_read=sizeof_fmt(0),
                                    total_bytes=sizeof_fmt(self.total_backup_size))
                        )
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
                '{bytes_read}/{total_bytes}'
                .format(bytes_read=sizeof_fmt(self.comp_size),
                        total_bytes=sizeof_fmt(self.total_backup_size))
            )

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
                    human_delta = safe_humanize(arrow_date, arrow.utcnow(),
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
