from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, \
    QStackedWidget, QAction, QDialog

from pyqt.dialogs.ConnectionDialog import ConnectionDialog
from pyqt.dialogs.LanguageDialog import LanguageDialog
from pyqt.widgets.DeviceDetailsWidget import DeviceDetailsWidget
from pyqt.widgets.ProjectViewWidget import ProjectViewWidget
from pyqt.widgets.ProjectsWidget import ProjectsWidget
from pyqt.widgets.RegistrationLoginForm import RegistrationLoginForm


class MainWindow(QMainWindow):
    def __init__(self, db_session):
        super().__init__()

        self.db_session = db_session
        self.isAdmin = False

        self.setWindowTitle("Ergon EMS")
        self.setGeometry(100, 100, 800, 600)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.menu_bar = self.menuBar()

        back_action = QAction("Назад", self)
        self.menu_bar.addAction(back_action)
        back_action.triggered.connect(self.go_back)

        connection_menu = self.menu_bar.addMenu("З'єднання")
        connection_action = QAction("З'єднання", self)
        connection_action.triggered.connect(self.open_connection_dialog)
        connection_menu.addAction(connection_action)

        settings_menu = self.menu_bar.addMenu("Налаштування")
        language_action = QAction("Мова", self)
        settings_menu.addAction(language_action)
        language_action.triggered.connect(self.change_language)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.registration_widget = RegistrationLoginForm(self)
        self.stacked_widget.addWidget(self.registration_widget)

        self.stacked_widget.setCurrentIndex(0)

    def change_language(self):
        language_dialog = LanguageDialog(self)
        if language_dialog.exec_() == QDialog.Accepted:
            current_language = language_dialog.selected_language
            print(f"Мова змінена на: {current_language}")

    def open_connection_dialog(self):
        dialog = ConnectionDialog(self)
        dialog.exec_()

    def open_projects_list(self):
        projects_widget = ProjectsWidget(self)
        self.stacked_widget.addWidget(projects_widget)
        self.stacked_widget.setCurrentIndex(1)

    def open_project_details(self, project):
        project_view_widget = ProjectViewWidget(self, project)
        self.stacked_widget.addWidget(project_view_widget)
        self.stacked_widget.setCurrentIndex(2)

    def open_device_details(self, device):
        device_details_widget = DeviceDetailsWidget(self, device)
        self.stacked_widget.addWidget(device_details_widget)
        self.stacked_widget.setCurrentIndex(3)

    def go_back(self):
        current_index = self.stacked_widget.currentIndex()

        if current_index > 0:
            current_widget = self.stacked_widget.currentWidget()
            self.stacked_widget.removeWidget(current_widget)

            self.stacked_widget.setCurrentIndex(current_index - 1)

        if current_index == 1:
            print("Перехід на екран реєстрації/логіну. Очищення даних...")
            self.isAdmin = False

            self.stacked_widget.removeWidget(self.registration_widget)

            self.registration_widget = RegistrationLoginForm(self)
            self.stacked_widget.addWidget(self.registration_widget)

            self.stacked_widget.setCurrentIndex(0)
