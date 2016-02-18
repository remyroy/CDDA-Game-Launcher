import sys
import os
import traceback

import logging
from logging.handlers import RotatingFileHandler

import gettext
_ = gettext.gettext

from io import StringIO

if getattr(sys, 'frozen', False):
    # we are running in a bundle
    basedir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(basedir)

from cddagl.config import init_config
from cddagl.ui import start_ui, ui_exception

from cddagl.__version__ import version

MAX_LOG_SIZE = 1024 * 1024
MAX_LOG_FILES = 5

def init_gettext():
    pass

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

    logger.info(_('Launcher started: {version}').format(version=version))

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
    init_gettext()
    init_logging()
    init_exception_catcher()

    init_config(basedir)
    start_ui(basedir)
