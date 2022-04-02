# SPDX-FileCopyrightText: 2015-2021 Rémy Roy
#
# SPDX-License-Identifier: MIT

import html
import logging
import os
import platform
import traceback
from io import StringIO
from urllib.parse import urlencode

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QGridLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QToolButton,
    QDialog, QTextBrowser, QMessageBox, QHBoxLayout, QTextEdit
)

import cddagl.constants as cons
from cddagl import __version__ as version
from cddagl.constants import get_resource_path
from cddagl.functions import clean_qt_path, bitness
from cddagl.i18n import proxy_gettext as _
from cddagl.win32 import get_downloads_directory

import markdown2

logger = logging.getLogger('cddagl')


class BrowserDownloadDialog(QDialog):
    def __init__(self, name, url, expected_filename):
        super(BrowserDownloadDialog, self).__init__()

        self.name = name
        self.url = url
        self.expected_filename = expected_filename
        self.downloaded_path = None

        layout = QGridLayout()

        info_label = QLabel()
        info_label.setText(_('This {name} cannot be directly downloaded by the '
            'launcher. You have to use your browser to download it.').format(
            name=name))
        layout.addWidget(info_label, 0, 0, 1, 2)
        self.info_label = info_label

        step1_label = QLabel()
        step1_label.setText(_('1. Open the URL in your browser.'))
        layout.addWidget(step1_label, 1, 0, 1, 2)
        self.step1_label = step1_label

        url_tb = QTextBrowser()
        url_tb.setText('<a href="{url}">{url}</a>'.format(url=html.escape(url)))
        url_tb.setReadOnly(True)
        url_tb.setOpenExternalLinks(True)
        url_tb.setMaximumHeight(23)
        url_tb.setLineWrapMode(QTextEdit.NoWrap)
        url_tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        layout.addWidget(url_tb, 2, 0, 1, 2)
        self.url_tb = url_tb

        step2_label = QLabel()
        step2_label.setText(_('2. Download the {name} on that page and wait '
            'for the download to complete.').format(name=name))
        layout.addWidget(step2_label, 3, 0, 1, 2)
        self.step2_label = step2_label

        step3_label = QLabel()
        step3_label.setText(_('3. Select the downloaded archive.'))
        layout.addWidget(step3_label, 4, 0, 1, 2)
        self.step3_label = step3_label

        path = get_downloads_directory()
        if expected_filename is not None:
            path = os.path.join(path, expected_filename)

        download_path_le = QLineEdit()
        download_path_le.setText(path)
        layout.addWidget(download_path_le, 5, 0)
        self.download_path_le = download_path_le

        download_path_button = QToolButton()
        download_path_button.setText('...')
        download_path_button.clicked.connect(self.set_download_path)
        layout.addWidget(download_path_button, 5, 1)
        self.download_path_button = download_path_button

        buttons_container = QWidget()
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_container.setLayout(buttons_layout)

        install_button = QPushButton()
        install_button.setText(_('Install this {name}').format(name=name))
        install_button.clicked.connect(self.install_clicked)
        buttons_layout.addWidget(install_button)
        self.install_button = install_button

        do_not_install_button = QPushButton()
        do_not_install_button.setText(_('Do not install'))
        do_not_install_button.clicked.connect(self.do_not_install_clicked)
        buttons_layout.addWidget(do_not_install_button)
        self.do_not_install_button = do_not_install_button

        layout.addWidget(buttons_container, 6, 0, 1, 2, Qt.AlignRight)
        self.buttons_container = buttons_container
        self.buttons_layout = buttons_layout

        self.setLayout(layout)

        self.setWindowTitle(_('Browser download'))

    def set_download_path(self):
        options = QFileDialog.DontResolveSymlinks
        selected_file, selected_filter = QFileDialog.getOpenFileName(self,
            _('Downloaded archive'), self.download_path_le.text(),
            _('Archive files {formats}').format(formats='(*.zip *.rar *.7z)'),
            options=options)
        if selected_file:
            self.download_path_le.setText(clean_qt_path(selected_file))

    def install_clicked(self):
        choosen_file = self.download_path_le.text()
        if not os.path.isfile(choosen_file):
            filenotfound_msgbox = QMessageBox()
            filenotfound_msgbox.setWindowTitle(_('File not found'))

            text = (_('{filepath} is not an existing file on your system. '
                'Make sure to download the archive with your browser. Make '
                'sure to select the downloaded archive afterwards.')).format(
                    filepath=choosen_file
                )

            filenotfound_msgbox.setText(text)
            filenotfound_msgbox.addButton(_('I will try again'),
                QMessageBox.AcceptRole)
            filenotfound_msgbox.setIcon(QMessageBox.Warning)
            filenotfound_msgbox.exec()

            return

        self.downloaded_path = choosen_file
        self.done(1)

    def do_not_install_clicked(self):
        self.done(0)


class FaqDialog(QDialog):
    def __init__(self, parent=0, f=0):
        super(FaqDialog, self).__init__(parent, f)

        layout = QGridLayout()

        text_content = QTextBrowser()
        text_content.setReadOnly(True)
        text_content.setOpenExternalLinks(True)

        layout.addWidget(text_content, 0, 0)
        self.text_content = text_content

        ok_button = QPushButton()
        ok_button.clicked.connect(self.done)
        layout.addWidget(ok_button, 1, 0, Qt.AlignRight)
        self.ok_button = ok_button

        layout.setRowStretch(0, 100)

        self.setMinimumSize(640, 450)

        self.setLayout(layout)
        self.set_text()
    
    def set_text(self):
        self.setWindowTitle(_('Frequently asked questions (FAQ)'))
        self.ok_button.setText(_('OK'))

        m = _('<h2>CDDA Game Launcher Frequently asked questions (FAQ)</h2>')

        html_faq = markdown2.markdown(_('''
### Where is my previous version?

Is it stored in the `previous_version` directory inside your game directory.

### How does the launcher update my game?

* The launcher downloads the archive for the new version.
* If the `previous_version` subdirectory exists, the launcher moves it in the recycle bin.
* The launcher moves everything from the game directory in the `previous_version` subdirectory.
* The launcher extracts the downloaded archive in the game directory.
* The launcher inspect what is in the `previous_version` directory and it copies the saves, the mods, the tilesets, the soundpacks and a bunch of others useful files from the `previous_version` directory that are missing from the downloaded archive to the real game directory. It will assume that mods that are included in the downloaded archive are the newest and latest version and it will keep those by comparing their unique ident value.

### I think the launcher just deleted my files. What can I do?

The launcher goes to great lengths not to delete any file that could be important to you. With the default and recommended settings, the launcher will always move files instead of deleting them. If you think you lost files during an update, check out the `previous_version` subdirectory. That is where you should be able to find your previous game version. You can also check for files in your recycle bin. Those are the main 2 places where files are moved and where you should be able to find them.

### My antivirus product detected the launcher as a threat. What can I do?

Poor antivirus products are known to detect the launcher as a threat and block its execution or delete the launcher. A simple workaround is to add the launcher binary in your antivirus whitelist or select the action to trust this binary when detected.

If you are paranoid, you can always inspect the source code yourself and build the launcher from the source code. You are still likely to get false positives. There is little productive efforts we can do as software developers with these. We have [a nice building guide](https://github.com/DazedNConfused-/CDDA-Game-Launcher/blob/master/BUILDING.md) for those who want to build the launcher from the source code.

Many people are dying to know why antivirus products are identifying the launcher as a threat. There has been many wild speculations to try to pinpoint the root cause for this. The best way to find out would be to ask those antivirus product developers. Unfortunatly, they are unlikely to respond for many good reasons. We could also speculate on this for days on end. Our current best speculation is because we use a component called PyInstaller [that is commonly flagged as a threat](https://github.com/pyinstaller/pyinstaller/issues/4633). Now, if you want see how deep the rabbit hole goes, you can keep on searching or speculating on why PyInstaller itself is commonly flagged as a threat. This research is left as an exercise to the reader.

Many people are also asking why not simply report the launcher as a false positive to those antivirus products. We welcome anyone who wants to take the time to do it, but we believe it is mostly unproductive. Those processes are often time-consuming and ignored. Someone would also have to do them all over again each time we make a new release or when one of the component we use is updated or changed. The current state of threat detection on PC is quite messy and sad especially for everyone using *free* antivirus products.

### I found an issue with the game itself or I would like to make a suggestion for the game itself. What should I do?

You should [contact the game developpers](https://cataclysmdda.org/#ive-found-a-bug--i-would-like-to-make-a-suggestion-what-should-i-do) about this. We are mainly providing a tool to help with the game. We cannot provide support for the game itself.

### How do I update to a new version of the game launcher?

The launcher will automatically check for updated version on start. If it finds one, the launcher will prompt you to update. You can always download [the latest version on github](https://github.com/DazedNConfused-/CDDA-Game-Launcher/releases). Those using the portable version will have to manually download and manually update the launcher. From the help menu, you can also check for new updates.

### The launcher keeps crashing when I start it. What can I do?

You might need to delete your configs file to work around this issue. That filename is `configs.db` and it is located in `%LOCALAPPDATA%\CDDA Game Launcher\`. Some users have reported and encountered unrelated starting issues. In some cases, running a debug version of the launcher to get more logs might help to locate the issue. [Creating an issue about this](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues) is probably the way to go.

### I just installed the game and it already has a big list of mods. Is there something wrong?

The base game is bundled with a good number of mods. You can view them more like modules that you can activate or ignore when creating a new world in game. These mods or modules can provide a different game experience by adding new items, buildings, mobs, by disabling some game mechanics or by changing how you play the game. They are a simple way of having a distinctive playthrough using the same game engine. The game is quite enjoyable without any of these additional mods or by using the default mods when creating a new world. You should probably avoid using additional mods if you are new to the game for your first playthrough to get familiar with the game mechanics. Once you are comfortable, after one or a few playthroughs, I suggest you check back the base game mods or even some external mods for your next world.

### A mod in the repository is broken or is crashing my game when enabled. What can I do? ###

It is frequent for game updates to break mods especially on the experimental branch. You could try to see if there is an update for that mod. You could try updating that mod by removing it and installing it again. You could try to contact the mod author and ask him to update his mod.

Maintaining external mods can be a difficult task for an ever expanding and changing base game. The only sure and *official* way to have good working mods is to have them included in the base game. If you are concerned about having a reliable gaming experience, you should consider using the base game mods exclusivly and you should consider using the stable branch.

If you find out a mod in the repository is clearly abandonned and not working anymore, please [open an issue](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues) about it so it can be removed.

### Will you make a Linux or macOS version?

Most likely not. You can check [the linux issue](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/329) and [the mac issue](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/73) for more information.

### It does not work? Can you help me?

Submit your issues [on Github](https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues). Try to [report bugs effectively](http://www.chiark.greenend.org.uk/~sgtatham/bugs.html).
'''))

        m += html_faq

        self.text_content.setHtml(m)

class AboutDialog(QDialog):
    def __init__(self, parent=0, f=0):
        super(AboutDialog, self).__init__(parent, f)

        layout = QGridLayout()

        text_content = QTextBrowser()
        text_content.setReadOnly(True)
        text_content.setOpenExternalLinks(True)

        text_content.setSearchPaths([get_resource_path()])
        layout.addWidget(text_content, 0, 0)
        self.text_content = text_content

        ok_button = QPushButton()
        ok_button.clicked.connect(self.done)
        layout.addWidget(ok_button, 1, 0, Qt.AlignRight)
        self.ok_button = ok_button

        layout.setRowStretch(0, 100)

        self.setMinimumSize(640, 450)

        self.setLayout(layout)
        self.set_text()

    def set_text(self):
        self.setWindowTitle(_('About CDDA Game Launcher'))
        self.ok_button.setText(_('OK'))
        m = _('<p>CDDA Game Launcher version {version}</p>').format(version=version)
        m += _('<p>Get the latest release'
               ' <a href="https://github.com/DazedNConfused-/CDDA-Game-Launcher/releases">on GitHub</a>.'
               '</p>')
        m += _('<p>Please report any issue'
               ' <a href="https://github.com/DazedNConfused-/CDDA-Game-Launcher/issues/new">on GitHub</a>.'
               '</p>')
        m += _('<p>Thanks to the following people for their efforts in'
               ' translating the CDDA Game Launcher</p>'
               '<ul>'
               '<li>Russian: Daniel from <a href="http://cataclysmdda.ru/">cataclysmdda.ru</a>'
               ' and Night_Pryanik'
               '</li>'
               '<li>Italian: Rettiliano Verace from'
               ' <a href="http://emigrantebestemmiante.blogspot.com">Emigrante Bestemmiante</a>'
               '</li>'
               '<li>French: Rémy Roy</li>'
               '<li>Spanish: KurzedMetal</li>'
               '</ul>')
        m += _('<p>Thanks to <a href="http://mattahan.deviantart.com/">Paul Davey aka Mattahan</a>'
               ' for the permission to use his artwork for the launcher icon.</p>')
        m += _('<p>This software is distributed under the MIT License. That means this is'
               ' 100&#37; free software, completely free to use, modify and/or distribute.'
               ' If you like more details check the following boring legal stuff...</p>')
        m += '<p>Copyright (c) 2015-2021 Rémy Roy</p>'
        m += '<p>Copy<i>cat</i> (c) 2022-2022 Gonzalo López</p>'
        m += ('<p>Permission is hereby granted, free of charge, to any person obtaining a copy'
              ' of this software and associated documentation files (the "Software"), to deal'
              ' in the Software without restriction, including without limitation the rights'
              ' to use, copy, modify, merge, publish, distribute, sublicense, and/or sell'
              ' copies of the Software, and to permit persons to whom the Software is'
              ' furnished to do so, subject to the following conditions:</p>'
              '<p>The above copyright notice and this permission notice shall be included in'
              ' all copies or substantial portions of the Software.</p>'
              '<p>THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR'
              ' IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,'
              ' FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE'
              ' AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER'
              ' LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,'
              ' OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE'
              ' SOFTWARE.</p>')
        self.text_content.setHtml(m)


class ExceptionWindow(QWidget):
    def __init__(self, app, extype, value, tb):
        super(ExceptionWindow, self).__init__()

        self.app = app

        layout = QGridLayout()

        information_label = QLabel()
        information_label.setText(_('The CDDA Game Launcher just crashed. An '
            'unhandled exception was raised. Here are the details.'))
        layout.addWidget(information_label, 0, 0)
        self.information_label = information_label

        tb_io = StringIO()
        traceback.print_tb(tb, file=tb_io)
        traceback_content = html.escape(tb_io.getvalue()).replace('\n', '<br>')

        text_content = QTextBrowser()
        text_content.setReadOnly(True)
        text_content.setOpenExternalLinks(True)
        text_content.setHtml(_('''
<p>CDDA Game Launcher version: {version}</p>
<p>OS: {os} ({bitness})</p>
<p>Type: {extype}</p>
<p>Value: {value}</p>
<p>Traceback:</p>
<code>{traceback}</code>
''').format(version=html.escape(version), extype=html.escape(str(extype)),
    value=html.escape(str(value)), os=html.escape(platform.platform()),
    traceback=traceback_content, bitness=html.escape(bitness())))

        layout.addWidget(text_content, 1, 0)
        self.text_content = text_content

        report_url = cons.NEW_ISSUE_URL + '?' + urlencode({
            'title': _('Unhandled exception: [Enter a title]'),
            'body': _('''* Description: [Enter what you did and what happened]
* Version: {version}
* OS: {os} ({bitness})
* Type: `{extype}`
* Value: {value}
* Traceback:
```
{traceback}
```
''').format(version=version, extype=str(extype), value=str(value),
    traceback=tb_io.getvalue(), os=platform.platform(), bitness=bitness())
        })

        report_label = QLabel()
        report_label.setOpenExternalLinks(True)
        report_label.setText(_('Please help us make a better launcher '
            '<a href="{url}">by reporting this issue on GitHub</a>.').format(
                url=html.escape(report_url)))
        layout.addWidget(report_label, 2, 0)
        self.report_label = report_label

        exit_button = QPushButton()
        exit_button.setText(_('Exit'))
        exit_button.clicked.connect(lambda: self.app.exit(-100))
        layout.addWidget(exit_button, 3, 0, Qt.AlignRight)
        self.exit_button = exit_button

        self.setLayout(layout)
        self.setWindowTitle(_('Something went wrong'))
        self.setMinimumSize(350, 0)
