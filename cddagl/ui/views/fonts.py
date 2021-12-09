# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import logging

from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtWidgets import QWidget, QGridLayout, QTabWidget

logger = logging.getLogger('cddagl')


class FontsTab(QTabWidget):
    def __init__(self):
        super(FontsTab, self).__init__()

        layout = QGridLayout()

        font_window = CataWindow(4, 4, QFont('Consolas'), 18, 9, 18, False)
        layout.addWidget(font_window, 0, 0)
        self.font_window = font_window

        self.setLayout(layout)

    def set_text(self):
        pass

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab


class CataWindow(QWidget):
    def __init__(self, terminalwidth, terminalheight, font, fontsize, fontwidth,
            fontheight, fontblending):
        super(CataWindow, self).__init__()

        self.terminalwidth = terminalwidth
        self.terminalheight = terminalheight

        self.cfont = font
        self.fontsize = fontsize
        self.cfont.setPixelSize(fontsize)
        self.cfont.setStyle(QFont.StyleNormal)
        self.fontwidth = fontwidth
        self.fontheight = fontheight
        self.fontblending = fontblending

        #self.text = '@@@\nBBB\n@@@\nCCC'
        self.text = '####\n####\n####\n####\n'

    def sizeHint(self):
        return QSize(self.terminalwidth * self.fontwidth,
            self.terminalheight * self.fontheight)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(0, 0, self.width(), self.height(), QColor(0, 0, 0))
        painter.setPen(QColor(99, 99, 99));
        painter.setFont(self.cfont)

        term_x = 0
        term_y = 0
        for char in self.text:
            if char == '\n':
                term_y += 1
                term_x = 0
                continue
            x = self.fontwidth * term_x
            y = self.fontheight * term_y

            rect = QRect(x, y, self.fontwidth, self.fontheight)
            painter.drawText(rect, 0, char)

            term_x += 1

        x = self.fontwidth * term_x
        y = self.fontheight * term_y

        rect = QRect(x, y, self.fontwidth, self.fontheight)

        painter.fillRect(rect, Qt.green)

