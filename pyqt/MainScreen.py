from PyQt5.QtWidgets import QMainWindow, QLabel, QTableWidget, QListWidget, QGridLayout, QMenuBar, QMenu, \
    QWidget, QTextEdit


class MainScreen(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window size and title
        self.setGeometry(100, 100, 600, 400)
        self.setWindowTitle('ERGON EMS')

        # Create a menu bar
        menu_bar = QMenuBar()
        file_menu = QMenu('Account', self)
        menu_bar.addMenu(file_menu)
        view_menu = QMenu('View', self)
        menu_bar.addMenu(view_menu)
        settings_menu = QMenu('Settings', self)
        menu_bar.addMenu(settings_menu)
        help_menu = QMenu('Help', self)
        menu_bar.addMenu(help_menu)
        self.setMenuBar(menu_bar)

        # Central widget
        central_widget = QWidget()
        main_layout = QGridLayout(central_widget)


        # Device details
        device_params_label = QLabel("Device Details")
        param_table = QTableWidget(2, 2)
        param_table.setHorizontalHeaderLabels(['Parameter', 'Value'])
        main_layout.addWidget(device_params_label, 0, 0)
        main_layout.addWidget(param_table, 1, 0)

        # Device list
        device_list_label = QLabel("Device list")
        device_list = QListWidget()
        device_list.addItems(['Device 1', 'Device 2'])
        main_layout.addWidget(device_list_label, 0, 1)
        main_layout.addWidget(device_list, 1, 1)

        # Reports
        report_label = QLabel("Reports")
        report_list = QListWidget()
        report_list.addItems(['Report 1', 'Report 2'])
        main_layout.addWidget(report_label, 2, 0)
        main_layout.addWidget(report_list, 3, 0)

        # Log
        log_label = QLabel("Log")
        log_text_edit = QTextEdit()
        main_layout.addWidget(log_label, 2, 1)
        main_layout.addWidget(log_text_edit, 3, 1)

        self.setCentralWidget(central_widget)