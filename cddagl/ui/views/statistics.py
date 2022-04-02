# SPDX-FileCopyrightText: 2022 Gonzalo López <glopezvigliante@gmail.com>
#
# SPDX-License-Identifier: MIT

import logging
from datetime import datetime
from cddagl.functions import strfdelta
from cddagl.constants import DURATION_FORMAT

from PyQt5.QtCore import (
    Qt, QTimer
    )
from PyQt5.QtWidgets import (
    QTabWidget, QGroupBox, QGridLayout, QLabel, QVBoxLayout, QPushButton
    )
from cddagl.sql.functions import get_config_value, set_config_value

logger = logging.getLogger('cddagl')

class StatisticsTab(QTabWidget):
    def __init__(self):
        super(StatisticsTab, self).__init__()
        
        self.game_start_time = None
        self.last_game_duration = get_config_value('last_played', 0)

        current_played_group_box = CurrentPlayedGroupBox()
        self.current_played_group_box = current_played_group_box
        self.reset_current_button = current_played_group_box.reset_current_button

        total_game_duration_group_box = TotalPlayedGroupBox()
        self.total_game_duration_group_box = total_game_duration_group_box
        self.reset_total_button = total_game_duration_group_box.reset_total_button

        layout = QVBoxLayout()
        layout.addWidget(current_played_group_box)
        layout.addWidget(total_game_duration_group_box)
        self.setLayout(layout)

    def set_text(self):
        self.current_played_group_box.set_text()
        self.current_played_group_box.set_label_text()
        self.total_game_duration_group_box.set_text()

    def get_main_window(self):
        return self.parentWidget().parentWidget().parentWidget()

    def get_main_tab(self):
        return self.parentWidget().parentWidget().main_tab

    def game_started(self):
        self.game_start_time = datetime.now()
        game_timer = QTimer()
        game_timer.setInterval(1000)
        game_timer.timeout.connect(self.game_tick)
        self.game_timer = game_timer
        game_timer.start()
        self.reset_current_button.setEnabled(False)
        self.reset_total_button.setEnabled(False)

    def game_ended(self):
        total_game_duration = int(get_config_value('total_played',0))
        total_game_duration += self.last_game_duration
        set_config_value('last_played', self.last_game_duration)        
        set_config_value('total_played', total_game_duration)
        self.game_start_time = None
        self.game_timer.stop()
        self.reset_current_button.setEnabled(True)
        self.reset_total_button.setEnabled(True)

    def game_tick(self):
        elapsed = int(datetime.now().timestamp() - self.game_start_time.timestamp())
        self.last_game_duration = elapsed 
        self.current_played_group_box.set_label_text()
        self.total_game_duration_group_box.set_label_text()

class CurrentPlayedGroupBox(QGroupBox):
    def __init__(self):
        super(CurrentPlayedGroupBox, self).__init__()

        layout = QGridLayout()

        current_played_label = QLabel()
        current_played_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(current_played_label, 0, 0, Qt.AlignHCenter)
        self.current_played_label = current_played_label

        reset_current_button = QPushButton()
        reset_current_button.setStyleSheet("font-size: 20px;")
        reset_current_button.clicked.connect(self.reset_current)
        layout.addWidget(reset_current_button, 1, 0, Qt.AlignHCenter)
        self.reset_current_button = reset_current_button

        self.setLayout(layout)
        self.set_text()

    def reset_current(self):
        self.parentWidget().last_game_duration = 0
        set_config_value('last_played', 0)
        self.set_label_text()        

    def get_main_tab(self):
        return self.parentWidget().get_main_tab()

    def set_text(self):
        self.reset_current_button.setText(_('RESET'))
        last_game_duration = int(get_config_value('last_played', 0))
        fmt_last_game_duration = strfdelta(last_game_duration, _(DURATION_FORMAT), inputtype='s')
        self.current_played_label.setText(fmt_last_game_duration)
        self.setTitle(_('Last game duration:'))
    
    def set_label_text(self):
        last_game_duration = self.parentWidget().last_game_duration
        fmt_last_game_duration = strfdelta(last_game_duration, _(DURATION_FORMAT), inputtype='s')
        self.current_played_label.setText(fmt_last_game_duration)


class TotalPlayedGroupBox(QGroupBox):
    def __init__(self):
        super(TotalPlayedGroupBox, self).__init__()

        layout = QGridLayout()

        total_game_duration_label = QLabel()
        total_game_duration_label.setStyleSheet("font-size: 32px;")
        layout.addWidget(total_game_duration_label, 0, 0, Qt.AlignHCenter)
        self.total_game_duration_label = total_game_duration_label

        reset_total_button = QPushButton()
        reset_total_button.setStyleSheet("font-size: 20px;")
        reset_total_button.clicked.connect(self.reset_total)
        layout.addWidget(reset_total_button, 1, 0, Qt.AlignHCenter)
        self.reset_total_button = reset_total_button        

        self.setLayout(layout)
        self.set_text()

    def reset_total(self):
        set_config_value('total_played', 0)
        self.set_label_text()          

    def get_main_tab(self):
        return self.parentWidget().get_main_tab()

    def set_text(self):
        self.reset_total_button.setText(_('RESET'))
        total_game_duration = int(get_config_value('total_played', 0))
        fmt_total_game_duration = strfdelta(total_game_duration, _(DURATION_FORMAT), inputtype='s')    
        self.total_game_duration_label.setText(fmt_total_game_duration)
        self.setTitle(_('Total time in game:'))
    
    def set_label_text(self):
        total_game_duration = int(get_config_value('total_played', 0)) + int(self.parentWidget().last_game_duration)
        fmt_total_game_duration = strfdelta(total_game_duration, _(DURATION_FORMAT), inputtype='s')    
        self.total_game_duration_label.setText(fmt_total_game_duration)
