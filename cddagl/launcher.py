import sys
import os
import traceback

import logging
from logging.handlers import RotatingFileHandler

import gettext
_ = gettext.gettext

from io import StringIO

from babel.core import Locale

try:
    from os import scandir
except ImportError:
    from scandir import scandir

if getattr(sys, 'frozen', False):
    # we are running in a bundle
    basedir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(basedir)

from cddagl.config import init_config, get_config_value, config_true
from cddagl.ui import start_ui, ui_exception

from cddagl.win32 import get_ui_locale, SingleInstance

from cddagl.__version__ import version

MAX_LOG_SIZE = 1024 * 1024
MAX_LOG_FILES = 5

available_locales = []
app_locale = None

def init_single_instance():
    single_instance = SingleInstance()

    if single_instance.aleradyrunning():
        sys.exit(0)

    return single_instance

def init_gettext():
    locale_dir = os.path.join(basedir, 'cddagl', 'locale')
    preferred_locales = []

    selected_locale = get_config_value('locale', None)
    if selected_locale == 'None':
        selected_locale = None
    if selected_locale is not None:
        preferred_locales.append(selected_locale)

    system_locale = get_ui_locale()
    if system_locale is not None:
        preferred_locales.append(system_locale)

    if os.path.isdir(locale_dir):
        entries = scandir(locale_dir)
        for entry in entries:
            if entry.is_dir():
                available_locales.append(entry.name)

    available_locales.sort(key=lambda x: 0 if x == 'en' else 1)

    app_locale = Locale.negotiate(preferred_locales, available_locales)
    if app_locale is None:
        app_locale = 'en'
    else:
        app_locale = str(app_locale)

    try:
        t = gettext.translation('cddagl', localedir=locale_dir,
            languages=[app_locale])
        global _
        _ = t.gettext
    except FileNotFoundError as e:
        pass

    return app_locale

def init_logging():
    logger = logging.getLogger('cddagl')
    logger.setLevel(logging.INFO)

    local_app_data = os.environ['LOCALAPPDATA']
    if not os.path.isdir(local_app_data):
        local_app_data = sys.path

    logging_dir = os.path.join(local_app_data, 'CDDA Game Launcher')
    if not os.path.isdir(logging_dir):
        os.makedirs(logging_dir)

    logging_file = os.path.join(logging_dir, 'app.log')

    handler = RotatingFileHandler(logging_file, maxBytes=MAX_LOG_SIZE,
        backupCount=MAX_LOG_FILES, encoding='utf8')
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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

    logger.info(_('CDDA Game Launcher started: {version}').format(
        version=version))

def handle_exception(extype, value, tb):
    logger = logging.getLogger('cddagl')

    tb_io = StringIO()
    traceback.print_tb(tb, file=tb_io)

    logger.critical(_('Global error:\nLauncher version: {version}\nType: '
        '{extype}\nValue: {value}\nTraceback:\n{traceback}').format(
            version=version, extype=str(extype), value=str(value),
            traceback=tb_io.getvalue()))

    ui_exception(extype, value, tb)

def init_exception_catcher():
    sys.excepthook = handle_exception

if __name__ == '__main__':
    init_config(basedir)
    single_instance = init_single_instance()

    app_locale = init_gettext()
    init_logging()
    init_exception_catcher()

    start_ui(basedir, app_locale, available_locales, single_instance)
