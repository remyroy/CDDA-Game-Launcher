import os

from PyQt5.QtCore import Qt

from PyQt5.QtWidgets import (
    QApplication, QWidget, QStatusBar, QGridLayout, QGroupBox, QMainWindow,
    QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QToolButton,
    QProgressBar)

from PyQt5.QtGui import QIcon

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest

READ_BUFFER_SIZE = 16384

def clean_qt_path(path):
    return path.replace('/', '\\')

class MainWindow(QMainWindow):
    def __init__(self, title):
        super(MainWindow, self).__init__()

        self.setMinimumSize(400, 0)
        
        self.createStatusBar()
        self.createCentralWidget()

        self.setWindowTitle(title)

    def createStatusBar(self):
        status_bar = self.statusBar()

        status_bar.showMessage('Ready')

    def createCentralWidget(self):
        central_widget = CentralWidget()
        self.setCentralWidget(central_widget)


class CentralWidget(QWidget):
    def __init__(self):
        super(CentralWidget, self).__init__()

        self.createGameDirGroupBox()

        layout = QVBoxLayout()
        layout.addWidget(self.game_dir_group_box)
        self.setLayout(layout)

    def getMainWindow(self):
        return self.parentWidget()

    def createGameDirGroupBox(self):
        game_dir_group_box = QGroupBox()

        layout = QGridLayout()

        dir_label = QLabel()
        dir_label.setText('Directory:')
        layout.addWidget(dir_label, 0, 0, Qt.AlignRight)
        self.dir_label = dir_label

        dir_edit = QLineEdit()
        dir_edit.editingFinished.connect(self.gameDirectoryChanged)
        layout.addWidget(dir_edit, 0, 1)
        self.dir_edit = dir_edit

        dir_change_button = QToolButton()
        dir_change_button.setText('...')
        dir_change_button.clicked.connect(self.setGameDirectory)
        layout.addWidget(dir_change_button, 0, 2)
        self.dir_change_button = dir_change_button

        version_label = QLabel()
        version_label.setText('Version:')
        layout.addWidget(version_label, 1, 0, Qt.AlignRight)
        self.version_label = version_label

        version_value_label = QLabel()
        layout.addWidget(version_value_label, 1, 1)
        self.version_value_label = version_value_label

        game_dir_group_box.setLayout(layout)
        game_dir_group_box.setTitle('Game directory')

        self.game_dir_group_box = game_dir_group_box

    def setGameDirectory(self):
        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self,
                "QFileDialog.getExistingDirectory()",
                self.dir_edit.text(), options=options)
        if directory:
            self.dir_edit.setText(clean_qt_path(directory))
            self.gameDirectoryChanged()

    def gameDirectoryChanged(self):
        directory = self.dir_edit.text()
        
        if not os.path.isdir(directory):
            self.version_value_label.setText('Not a valid directory')
        else:
            # Find the executable

            console_exe = os.path.join(directory, 'cataclysm.exe')
            tiles_exe = os.path.join(directory, 'cataclysm-tiles.exe')

            exe_path = None
            version_type = None
            if os.path.isfile(console_exe):
                version_type = 'console'
                exe_path = console_exe
            elif os.path.isfile(tiles_exe):
                version_type = 'tiles'
                exe_path = tiles_exe

            if version_type is None:
                self.version_value_label.setText('Not a CDDA directory')
            else:
                self.version_value_label.setText(
                    'Version type: {0}'.format(version_type))

                main_window = self.getMainWindow()

                status_bar = main_window.statusBar()
                status_bar.clearMessage()

                reading_label = QLabel()
                reading_label.setText('Reading: {0}'.format(exe_path))
                status_bar.addWidget(reading_label, 100)

                progress_bar = QProgressBar()
                status_bar.addWidget(progress_bar)

                exe_size = os.path.getsize(exe_path)

                with open(exe_path, 'rb') as f:
                    pass
                    '''from PyQt5.QtCore import pyqtRemoveInputHook, pyqtRestoreInputHook
                    pyqtRemoveInputHook()
                    import pdb; pdb.set_trace()
                    pyqtRestoreInputHook()'''

                status_bar.removeWidget(reading_label)
                status_bar.removeWidget(progress_bar)

                status_bar.showMessage('Ready')


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    mainWin = MainWindow('CDDA Game Launcher')
    mainWin.show()
    sys.exit(app.exec_())
