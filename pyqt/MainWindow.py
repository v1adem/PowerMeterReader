from PyQt5.QtWidgets import QMainWindow, QStackedWidget, QAction

from pyqt.dialogs.SettingsDialog import SettingsDialog
from pyqt.widgets.StatisticsWidget import StatisticsWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setFixedWidth(800)
        self.setFixedHeight(600)


        self.setWindowTitle("Ergon EMS")

        self.central_widget = QStackedWidget()
        self.setCentralWidget(self.central_widget)

        self.statistics_widget = StatisticsWidget("ElNetPQ")
        self.central_widget.addWidget(self.statistics_widget)
        self.central_widget.setCurrentWidget(self.statistics_widget)

        self.setup_menu_bar()

    def setup_menu_bar(self):
        menubar = self.menuBar()

        file_action = QAction("File", self)
        menubar.addAction(file_action)

        account_action = QAction("Account", self)
        menubar.addAction(account_action)

        settings_action = QAction("Settings", self)
        settings_action.triggered.connect(self.open_settings_dialog)
        menubar.addAction(settings_action)

        update_data_action = QAction("Update Data", self)
        menubar.addAction(update_data_action)

        help_action = QAction("Help", self)
        menubar.addAction(help_action)

    def open_settings_dialog(self):
        dialog = SettingsDialog()
        if dialog.exec_():
            print("Settings applied")