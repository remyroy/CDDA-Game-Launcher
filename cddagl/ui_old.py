import logging
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from cddagl.constants import get_locale_path, get_resource_path
from cddagl.i18n import load_gettext_locale
from cddagl.ui.views.dialogs import ExceptionWindow
from cddagl.ui.views.tabbed import TabbedWindow

logger = logging.getLogger('cddagl')


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
