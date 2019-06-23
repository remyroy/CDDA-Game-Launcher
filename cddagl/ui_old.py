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
from cddagl.ui.views.dialogs import AboutDialog, BrowserDownloadDialog, ExceptionWindow
from cddagl.ui.views.settings import SettingsTab
from cddagl.ui.views.backups import BackupsTab
from cddagl.ui.views.fonts import FontsTab
from cddagl.ui.views.tilesets import TilesetsTab
from cddagl.ui.views.main import MainTab
from cddagl.ui.views.tabbed import TabbedWindow

import cddagl
version = cddagl.__version__


logger = logging.getLogger('cddagl')

if getattr(sys, 'frozen', False):
    rarfile.UNRAR_TOOL = get_cddagl_path('UnRAR.exe')


def start_ui(locale, single_instance):
    load_gettext_locale(get_locale_path(), locale)

    main_app = QApplication(sys.argv)
    main_app.setWindowIcon(QIcon(get_resource_path('launcher.ico')))

    main_win = TabbedWindow('CDDA Game Launcher')
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
