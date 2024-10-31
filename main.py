import sys

from PyQt5.QtWidgets import QApplication

from pyqt.MainScreen import MainScreen

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainScreen()
    window.show()
    sys.exit(app.exec_())
