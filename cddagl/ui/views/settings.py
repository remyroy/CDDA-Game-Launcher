# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import logging

from PyQt5.QtCore import (
    Qt, QTimer)
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QGroupBox, QVBoxLayout, QLabel, QLineEdit,
    QFileDialog, QToolButton, QComboBox, QCheckBox, QHBoxLayout, QSpinBox, QSizePolicy
)
from babel.core import Locale

import cddagl.constants as cons
from cddagl.constants import get_locale_path, get_cdda_uld_path
from cddagl.functions import clean_qt_path
from cddagl.i18n import load_gettext_locale, get_available_locales, proxy_gettext as _
from cddagl.sql.functions import get_config_value, set_config_value, config_true
from cddagl.win32 import get_ui_locale

logger = logging.getLogger('cddagl')


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

    def set_text(self):
        self.launcher_settings_group_box.set_text()
        self.update_settings_group_box.set_text()

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab

    def disable_tab(self):
        self.launcher_settings_group_box.disable_controls()
        self.update_settings_group_box.disable_controls()

    def enable_tab(self):
        self.launcher_settings_group_box.enable_controls()
        self.update_settings_group_box.enable_controls()


class LauncherSettingsGroupBox(QGroupBox):
    def __init__(self):
        super(LauncherSettingsGroupBox, self).__init__()

        layout = QGridLayout()

        command_line_parameters_label = QLabel()
        layout.addWidget(command_line_parameters_label, 0, 0, Qt.AlignRight)
        self.command_line_parameters_label = command_line_parameters_label

        command_line_parameters_edit = QLineEdit()
        command_line_parameters_edit.setText(get_config_value('command.params',
            ''))
        command_line_parameters_edit.editingFinished.connect(
            self.clp_changed)
        layout.addWidget(command_line_parameters_edit, 0, 1)
        self.command_line_parameters_edit = command_line_parameters_edit

        keep_launcher_open_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'keep_launcher_open', 'False')) else Qt.Unchecked)
        keep_launcher_open_checkbox.setCheckState(check_state)
        keep_launcher_open_checkbox.stateChanged.connect(self.klo_changed)
        layout.addWidget(keep_launcher_open_checkbox, 1, 0, 1, 2)
        self.keep_launcher_open_checkbox = keep_launcher_open_checkbox

        locale_group = QWidget()
        locale_group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        locale_layout = QHBoxLayout()
        locale_layout.setContentsMargins(0, 0, 0, 0)

        locale_label = QLabel()
        locale_layout.addWidget(locale_label)
        self.locale_label = locale_label

        current_locale = get_config_value('locale', None)

        locale_combo = QComboBox()
        locale_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        locale_combo.addItem(_('System language or best match ({locale})'
            ).format(locale=get_ui_locale()), None)
        selected_index = 0
        for index, locale in enumerate(get_available_locales(get_locale_path())):
            if locale == current_locale:
                selected_index = index + 1
            locale = Locale.parse(locale)
            locale_name = locale.display_name
            english_name = locale.english_name
            if locale_name != english_name:
                formatted_name = f'{locale_name} - {english_name}'
            else:
                formatted_name = locale_name
            locale_combo.addItem(formatted_name, str(locale))
        locale_combo.setCurrentIndex(selected_index)
        locale_combo.currentIndexChanged.connect(self.locale_combo_changed)
        locale_layout.addWidget(locale_combo)
        self.locale_combo = locale_combo

        locale_group.setLayout(locale_layout)
        layout.addWidget(locale_group, 2, 0, 1, 2)
        self.locale_group = locale_group
        self.locale_layout = locale_layout

        allow_mul_insts_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'allow_multiple_instances', 'False')) else Qt.Unchecked)
        allow_mul_insts_checkbox.setCheckState(check_state)
        allow_mul_insts_checkbox.stateChanged.connect(self.ami_changed)
        layout.addWidget(allow_mul_insts_checkbox, 3, 0, 1, 2)
        self.allow_mul_insts_checkbox = allow_mul_insts_checkbox

        no_launcher_version_check_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'prevent_version_check_launch', 'False'))
            else Qt.Unchecked)
        no_launcher_version_check_checkbox.setCheckState(
            check_state)
        no_launcher_version_check_checkbox.stateChanged.connect(
            self.nlvcc_changed)
        layout.addWidget(no_launcher_version_check_checkbox, 4, 0, 1, 2)
        self.no_launcher_version_check_checkbox = (
            no_launcher_version_check_checkbox)

        self.setLayout(layout)
        self.set_text()

    def get_main_tab(self):
        return self.parentWidget().get_main_tab()

    def set_text(self):
        self.command_line_parameters_label.setText(
            _('Command line parameters:'))
        self.keep_launcher_open_checkbox.setText(
            _('Keep the launcher opened after launching the game'))
        self.locale_label.setText(_('Language:'))
        self.locale_combo.setItemText(0,
            _('System language or best match ({locale})').format(
                locale=get_ui_locale()))
        self.allow_mul_insts_checkbox.setText(_('Allow multiple instances of '
            'the launcher to be started'))
        self.no_launcher_version_check_checkbox.setText(_('Do not check '
            'for new version of the CDDA Game Launcher on launch'))
        self.setTitle(_('Launcher'))

    @property
    def app_locale(self):
        return QApplication.instance().app_locale

    @app_locale.setter
    def app_locale(self, locale):
        QApplication.instance().app_locale = locale

    def locale_combo_changed(self, index):
        selected_locale = self.locale_combo.currentData()
        locale_to_change = str(selected_locale)
        set_config_value('locale', locale_to_change)

        if selected_locale is None:
            preferred_locales = []

            system_locale = get_ui_locale()
            if system_locale is not None:
                preferred_locales.append(system_locale)

            negotiated_locale = Locale.negotiate(preferred_locales,
                                                 get_available_locales(get_locale_path()))
            if negotiated_locale is None:
                locale_to_change = 'en'
            else:
                locale_to_change = str(negotiated_locale)

        self.app_locale = locale_to_change
        load_gettext_locale(get_locale_path(), locale_to_change)

        main_app = QApplication.instance()
        main_app.main_win.set_text()
        central_widget = main_app.main_win.central_widget
        main_tab = central_widget.main_tab
        game_dir_group_box = main_tab.game_dir_group_box
        update_group_box = main_tab.update_group_box

        game_dir_group_box.last_game_directory = None
        game_dir_group_box.game_directory_changed()

        update_group_box.refresh_builds()

    def nlvcc_changed(self, state):
        set_config_value('prevent_version_check_launch',
            str(state != Qt.Unchecked))

    def klo_changed(self, state):
        checked = state != Qt.Unchecked

        set_config_value('keep_launcher_open', str(checked))

        backup_on_end = (Qt.Checked if config_true(get_config_value(
            'backup_on_end', 'False')) else Qt.Unchecked)

        backups_tab = self.get_main_tab().get_backups_tab()

        if not (backup_on_end and not checked):
            backups_tab.backup_on_end_warning_label.hide()
        else:
            backups_tab.backup_on_end_warning_label.show()

    def clp_changed(self):
        set_config_value('command.params',
            self.command_line_parameters_edit.text())

    def ami_changed(self, state):
        checked = state != Qt.Unchecked
        set_config_value('allow_multiple_instances', str(checked))

    def disable_controls(self):
        self.locale_combo.setEnabled(False)

    def enable_controls(self):
        self.locale_combo.setEnabled(True)


class UpdateSettingsGroupBox(QGroupBox):
    def __init__(self):
        super(UpdateSettingsGroupBox, self).__init__()

        layout = QGridLayout()

        prevent_save_move_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'prevent_save_move', 'False')) else Qt.Unchecked)
        prevent_save_move_checkbox.setCheckState(check_state)
        prevent_save_move_checkbox.stateChanged.connect(self.psmc_changed)
        layout.addWidget(prevent_save_move_checkbox, 0, 0, 1, 3)
        self.prevent_save_move_checkbox = prevent_save_move_checkbox

        keep_archive_copy_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'keep_archive_copy', 'False')) else Qt.Unchecked)
        keep_archive_copy_checkbox.setCheckState(check_state)
        keep_archive_copy_checkbox.stateChanged.connect(self.kacc_changed)
        layout.addWidget(keep_archive_copy_checkbox, 1, 0)
        self.keep_archive_copy_checkbox = keep_archive_copy_checkbox

        keep_archive_directory_line = QLineEdit()
        keep_archive_directory_line.setText(get_config_value(
            'archive_directory', ''))
        keep_archive_directory_line.editingFinished.connect(
            self.ka_directory_changed)
        layout.addWidget(keep_archive_directory_line, 1, 1)
        self.keep_archive_directory_line = keep_archive_directory_line

        ka_dir_change_button = QToolButton()
        ka_dir_change_button.setText('...')
        ka_dir_change_button.clicked.connect(self.set_ka_directory)
        layout.addWidget(ka_dir_change_button, 1, 2)
        self.ka_dir_change_button = ka_dir_change_button

        arb_timer = QTimer()
        arb_timer.setInterval(int(get_config_value(
            'auto_refresh_builds_minutes', '30')) * 1000 * 60)
        arb_timer.timeout.connect(self.arb_timeout)
        self.arb_timer = arb_timer
        if config_true(get_config_value('auto_refresh_builds', 'False')):
            arb_timer.start()

        arb_group = QWidget()
        arb_group.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        arb_layout = QHBoxLayout()
        arb_layout.setContentsMargins(0, 0, 0, 0)

        auto_refresh_builds_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'auto_refresh_builds', 'False')) else Qt.Unchecked)
        auto_refresh_builds_checkbox.setCheckState(check_state)
        auto_refresh_builds_checkbox.stateChanged.connect(self.arbc_changed)
        arb_layout.addWidget(auto_refresh_builds_checkbox)
        self.auto_refresh_builds_checkbox = auto_refresh_builds_checkbox

        arb_min_spinbox = QSpinBox()
        arb_min_spinbox.setMinimum(5)
        arb_min_spinbox.setValue(int(get_config_value(
            'auto_refresh_builds_minutes', '30')))
        arb_min_spinbox.valueChanged.connect(self.ams_changed)
        arb_layout.addWidget(arb_min_spinbox)
        self.arb_min_spinbox = arb_min_spinbox

        arb_min_label = QLabel()
        arb_layout.addWidget(arb_min_label)
        self.arb_min_label = arb_min_label

        arb_group.setLayout(arb_layout)
        layout.addWidget(arb_group, 2, 0, 1, 3)
        self.arb_group = arb_group
        self.arb_layout = arb_layout

        remove_previous_version_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'remove_previous_version', 'False')) else Qt.Unchecked)
        remove_previous_version_checkbox.setCheckState(check_state)
        remove_previous_version_checkbox.stateChanged.connect(self.rpvc_changed)
        layout.addWidget(remove_previous_version_checkbox, 3, 0, 1, 3)
        self.remove_previous_version_checkbox = (
            remove_previous_version_checkbox)

        permanently_delete_files_checkbox = QCheckBox()
        check_state = (Qt.Checked if config_true(get_config_value(
            'permanently_delete_files', 'False')) else Qt.Unchecked)
        permanently_delete_files_checkbox.setCheckState(check_state)
        permanently_delete_files_checkbox.stateChanged.connect(
                self.prfc_changed)
        layout.addWidget(permanently_delete_files_checkbox, 4, 0, 1, 3)
        self.permanently_delete_files_checkbox = (
            permanently_delete_files_checkbox)

        self.setLayout(layout)
        self.set_text()

    def set_text(self):
        self.prevent_save_move_checkbox.setText(
            _('Do not copy or move the save directory'))
        self.prevent_save_move_checkbox.setToolTip(
            _('If your save directory size is '
            'large, it might take a long time to copy it during the update '
            'process.\nThis option might help you speed the whole thing but '
            'your previous version will lack the save directory.'))
        self.keep_archive_copy_checkbox.setText(
            _('Keep a copy of the downloaded '
            'archive in the following directory:'))
        self.auto_refresh_builds_checkbox.setText(
            _('Automatically refresh builds list every'))
        self.arb_min_label.setText(_('minutes'))
        self.remove_previous_version_checkbox.setText(_(
            'Remove previous version after update (not recommended)'))
        self.permanently_delete_files_checkbox.setText(_(
            'Permanently delete files instead of moving them in the recycle '
            'bin (not recommended)'))
        self.setTitle(_('Update/Installation'))

    def get_settings_tab(self):
        return self.parentWidget()

    def get_main_tab(self):
        return self.get_settings_tab().get_main_tab()

    def arb_timeout(self):
        main_tab = self.get_main_tab()
        update_group_box = main_tab.update_group_box
        refresh_builds_button = update_group_box.refresh_builds_button

        if refresh_builds_button.isEnabled():
            update_group_box.refresh_builds()

    def ams_changed(self, value):
        set_config_value('auto_refresh_builds_minutes', value)
        self.arb_timer.setInterval(value * 1000 * 60)

    def arbc_changed(self, state):
        set_config_value('auto_refresh_builds', str(state != Qt.Unchecked))
        if state != Qt.Unchecked:
            self.arb_timer.start()
        else:
            self.arb_timer.stop()

    def psmc_changed(self, state):
        set_config_value('prevent_save_move', str(state != Qt.Unchecked))
        game_dir_group_box = self.get_main_tab().game_dir_group_box
        saves_warning_label = game_dir_group_box.saves_warning_label

        if state != Qt.Unchecked:
            saves_warning_label.hide()
        else:
            if game_dir_group_box.saves_size > cons.SAVES_WARNING_SIZE:
                saves_warning_label.show()
            else:
                saves_warning_label.hide()

    def rpvc_changed(self, state):
        set_config_value('remove_previous_version', str(state != Qt.Unchecked))

    def prfc_changed(self, state):
        set_config_value('permanently_delete_files', str(state != Qt.Unchecked))

    def kacc_changed(self, state):
        set_config_value('keep_archive_copy', str(state != Qt.Unchecked))

    def set_ka_directory(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self,
                _('Archive directory'), self.keep_archive_directory_line.text(),
                options=options)
        if directory:
            self.keep_archive_directory_line.setText(clean_qt_path(directory))
            self.ka_directory_changed()

    def ka_directory_changed(self):
        set_config_value('archive_directory',
            self.keep_archive_directory_line.text())

    def disable_controls(self):
        pass

    def enable_controls(self):
        pass
