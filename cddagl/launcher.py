from PyQt5.QtWidgets import (
    QApplication, QWidget, QStatusBar, QGridLayout, QGroupBox, QMainWindow,
    QVBoxLayout, QLabel)

from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest


class MainWindow(QMainWindow):
    def __init__(self, title):
        super(MainWindow, self).__init__()

        self.setMinimumSize(400, 400)
        
        self.createStatusBar()
        self.createCentralWidget()

        self.setWindowTitle(title)

    def createStatusBar(self):
        statusBar = self.statusBar()

        statusBar.showMessage('Ready')

    def createCentralWidget(self):
        centralWidget = CentralWidget()
        self.setCentralWidget(centralWidget)


class CentralWidget(QWidget):
    def __init__(self):
        super(CentralWidget, self).__init__()

        self.createGameDirGroupBox()

        layout = QVBoxLayout()
        layout.addWidget(self.gameDirGroupBox)
        self.setLayout(layout)

    def createGameDirGroupBox(self):
        gameDirGroupBox = QGroupBox()

        layout = QGridLayout()

        dirLabel = QLabel()

        layout.addWidget
        gameDirGroupBox.setLayout(layout)

        gameDirGroupBox.setTitle('Game directory')

        self.gameDirGroupBox = gameDirGroupBox


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    mainWin = MainWindow('CDDA Game Launcher')
    mainWin.show()
    sys.exit(app.exec_())
