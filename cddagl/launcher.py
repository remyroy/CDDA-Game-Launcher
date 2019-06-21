import sys
import os
import traceback

import logging
from logging.handlers import RotatingFileHandler

from io import StringIO

from babel.core import Locale

try:
    from os import scandir
except ImportError:
    from scandir import scandir

import cddagl.constants as cons
from cddagl.i18n import load_gettext_no_locale, proxy_gettext as _
from cddagl.sql.functions import init_config, get_config_value, config_true
from cddagl.ui import start_ui, ui_exception

from cddagl.win32 import get_ui_locale, SingleInstance, write_named_pipe

import cddagl
version = cddagl.__version__


def get_basedir():
    if getattr(sys, 'frozen', False):
        # we are running in a bundle
        return sys._MEIPASS
    else:
        # we are running in a normal Python environment
        return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_locale_path():
    return os.path.join(get_basedir(), 'cddagl', 'locale')


def init_single_instance():
    if not config_true(get_config_value('allow_multiple_instances', 'False')):
        single_instance = SingleInstance()

        if single_instance.aleradyrunning():
            write_named_pipe('cddagl_instance', b'dupe')
            sys.exit(0)

        return single_instance

    return None


def get_available_locales(locale_dir):
    available_locales = []
    if os.path.isdir(locale_dir):
        entries = scandir(locale_dir)
        for entry in entries:
            if entry.is_dir():
                available_locales.append(entry.name)

    available_locales.sort(key=lambda x: 0 if x == 'en' else 1)
    return available_locales


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
    logger = logging.getLogger('cddagl')
    logger.setLevel(logging.INFO)

    local_app_data = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA'))
    if local_app_data is None or not os.path.isdir(local_app_data):
        local_app_data = ''

    logging_dir = os.path.join(local_app_data, 'CDDA Game Launcher')
    if not os.path.isdir(logging_dir):
        os.makedirs(logging_dir)

    logging_file = os.path.join(logging_dir, 'app.log')

    handler = RotatingFileHandler(logging_file,maxBytes=cons.MAX_LOG_SIZE,
                                  backupCount=cons.MAX_LOG_FILES, encoding='utf8')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    if not getattr(sys, 'frozen', False):
        handler = logging.StreamHandler()
        logger.addHandler(handler)
    else:
        '''class LoggerWriter:
            def __init__(self, logger, level, imp=None):
                self.logger = logger
                self.level = level
                self.imp = imp

            def __getattr__(self, attr):
                return getattr(self.imp, attr)

            def write(self, message):
                if message != '\n':
                    self.logger.log(self.level, message)


        sys._stdout = sys.stdout
        sys._stderr = sys.stderr

        sys.stdout = LoggerWriter(logger, logging.INFO, sys._stdout)
        sys.stderr = LoggerWriter(logger, logging.ERROR, sys._stderr)'''

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


def init_exception_catcher():
    sys.excepthook = handle_exception


if __name__ == '__main__':
    load_gettext_no_locale()
    init_logging()
    init_exception_catcher()

    init_config(get_basedir())

    available_locales = get_available_locales(get_locale_path())
    start_ui(get_basedir(),
             get_preferred_locale(available_locales),
             available_locales,
             init_single_instance())
