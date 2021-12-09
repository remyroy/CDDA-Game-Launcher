# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import logging

from PyQt5.QtWidgets import QTabWidget

logger = logging.getLogger('cddagl')


class TilesetsTab(QTabWidget):
    def __init__(self):
        super(TilesetsTab, self).__init__()

    def set_text(self):
        pass

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab
