from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QMenu, QMenuBar

from pyqt.MainScreen import MainScreen
from pyqt.SettingsWidget import SettingsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setGeometry(100, 100, 800, 600)
        self.setWindowTitle("ERGON EMS")

        # Create a menu bar
        menu_bar = QMenuBar()
        file_menu = QMenu('Account', self)
        menu_bar.addMenu(file_menu)
        view_menu = QMenu('View', self)
        menu_bar.addMenu(view_menu)
        settings_menu = QMenu('Settings', self)
        settings_menu.addAction(self.set_widget(SettingsWidget()))
        menu_bar.addMenu(settings_menu)
        help_menu = QMenu('Help', self)
        menu_bar.addMenu(help_menu)
        self.setMenuBar(menu_bar)

        self.central_widget = MainScreen()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

    def set_widget(self, widget):
        self.layout.replaceWidget(widget, self.central_widget)
