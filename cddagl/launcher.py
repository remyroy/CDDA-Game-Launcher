# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import logging
import os
import sys
import traceback
from io import StringIO
from logging.handlers import RotatingFileHandler

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication
from babel.core import Locale

### to avoid import errors when not setting PYTHONPATH
if not getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import cddagl.constants as cons
from cddagl import __version__ as version
from cddagl.constants import get_cddagl_path, get_locale_path, get_resource_path
from cddagl.i18n import (
    load_gettext_locale, load_gettext_no_locale,
    proxy_gettext as _, get_available_locales
)
from cddagl.sql.functions import init_config, get_config_value, config_true
from cddagl.ui.views.dialogs import ExceptionWindow
from cddagl.ui.views.tabbed import TabbedWindow
from cddagl.win32 import get_ui_locale, SingleInstance, write_named_pipe

logger = logging.getLogger('cddagl')


def init_single_instance():
    if not config_true(get_config_value('allow_multiple_instances', 'False')):
        single_instance = SingleInstance()

        if single_instance.aleradyrunning():
            write_named_pipe('cddagl_instance', b'dupe')
            sys.exit(0)

        return single_instance

    return None


def get_preferred_locale(available_locales):
    preferred_locales = []

    selected_locale = get_config_value('locale', None)
    if selected_locale == 'None':
        selected_locale = None
    if selected_locale is not None:
        preferred_locales.append(selected_locale)

    system_locale = get_ui_locale()
    if system_locale is not None:
        preferred_locales.append(system_locale)

    app_locale = Locale.negotiate(preferred_locales, available_locales)
    if app_locale is None:
        app_locale = 'en'
    else:
        app_locale = str(app_locale)

    return app_locale


def init_logging():
    # get root logger
    logger = logging.getLogger('cddagl')
    logger.setLevel(logging.DEBUG)

    # setup directory for written-to-file logs
    local_app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA'))
    if local_app_data is None or not os.path.isdir(local_app_data):
        local_app_data = ''

    logging_dir = os.path.join(local_app_data, 'CDDA Game Launcher')
    if not os.path.isdir(logging_dir):
        os.makedirs(logging_dir)

    logging_file = os.path.join(logging_dir, 'app.log')

    # setup logging formatter
    log_formatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")

    # setup file logger
    file_handler = RotatingFileHandler(
        logging_file, encoding='utf8',
        maxBytes=cons.MAX_LOG_SIZE, backupCount=cons.MAX_LOG_FILES
    )
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)

    # setup consoler logger
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    # initialize
    logger.info(_('CDDA Game Launcher started: {version}').format(version=version))


def handle_exception(extype, value, tb):
    logger = logging.getLogger('cddagl')

    tb_io = StringIO()
    traceback.print_tb(tb, file=tb_io)

    logger.critical(
        _('Global error:\n'
          'Launcher version: {version}\n'
          'Type: {extype}\n'
          'Value: {value}\n'
          'Traceback:\n{traceback}')
        .format(version=version, extype=str(extype), value=str(value),traceback=tb_io.getvalue())
    )
    ui_exception(extype, value, tb)


def start_ui(locale, single_instance):
    load_gettext_locale(get_locale_path(), locale)

    main_app = QApplication(sys.argv)
    main_app.setWindowIcon(QIcon(get_resource_path('launcher.ico')))

    main_app.single_instance = single_instance
    main_app.app_locale = locale

    main_win = TabbedWindow('CDDA Game Launcher')
    main_win.show()

    main_app.main_win = main_win

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


def init_exception_catcher():
    sys.excepthook = handle_exception


def run_cddagl():
    load_gettext_no_locale()
    init_logging()
    init_exception_catcher()

    init_config(get_cddagl_path())

    start_ui(get_preferred_locale(get_available_locales(get_locale_path())),
             init_single_instance())


if __name__ == '__main__':
    run_cddagl()
