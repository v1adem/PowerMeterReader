from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel, QListView, QInputDialog, QMessageBox, \
    QHBoxLayout
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import Qt, QSize
from models.Project import Project


class ProjectsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window
        self.db_session = main_window.db_session
        self.isAdmin = main_window.isAdmin
        self.setWindowTitle("Список проєктів")

        self.layout = QVBoxLayout(self)

        self.projects_label = QLabel("Проєкти", self)
        self.layout.addWidget(self.projects_label)

        self.projects_list = QListView(self)
        self.layout.addWidget(self.projects_list)

        self.projects_model = QStandardItemModel()
        self.projects_list.setModel(self.projects_model)

        self.projects_list.doubleClicked.connect(self.open_project_details)

        self.load_projects()

        self.add_project_button = QPushButton("Додати новий проєкт", self)
        self.layout.addWidget(self.add_project_button)

        if not self.isAdmin:
            self.add_project_button.setDisabled(True)

        self.add_project_button.clicked.connect(self.add_new_project)

    def load_projects(self):
        self.projects_model.clear()
        projects = self.db_session.query(Project).all()

        for project in projects:
            item = QStandardItem()
            item.setData(project.name, Qt.UserRole)
            item.setSizeHint(QSize(0, 36))
            self.projects_model.appendRow(item)

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.addWidget(QLabel(project.name))

            edit_button = QPushButton()
            edit_button.setIcon(QIcon("pyqt/icons/edit.png"))
            edit_button.setFixedSize(24, 24)
            edit_button.clicked.connect(lambda _, p=project: self.edit_project(p))

            delete_button = QPushButton()
            delete_button.setIcon(QIcon("pyqt/icons/delete.png"))
            delete_button.setFixedSize(24, 24)
            delete_button.clicked.connect(lambda _, p=project: self.delete_project(p))

            item_layout.addWidget(edit_button)
            item_layout.addWidget(delete_button)
            item_layout.setContentsMargins(0, 0, 0, 0)

            self.projects_list.setIndexWidget(item.index(), item_widget)


    def add_new_project(self):
        project_name, ok = QInputDialog.getText(self, "Додати новий проєкт", "Введіть назву проєкту:")

        if ok and project_name:
            existing_project = self.db_session.query(Project).filter_by(name=project_name).first()
            if existing_project:
                QMessageBox.warning(self, "Помилка", "Проєкт з такою назвою вже існує.")
                return

            new_project = Project(name=project_name)
            self.db_session.add(new_project)
            self.db_session.commit()

            self.load_projects()

    def delete_project(self, project):
        reply = QMessageBox.question(self, "Підтвердження видалення",
                                     f"Ви впевнені, що хочете видалити проєкт '{project.name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_session.delete(project)
            self.db_session.commit()
            self.load_projects()

    def edit_project(self, project):
        new_name, ok = QInputDialog.getText(self, "Редагувати проєкт", "Введіть нову назву:", text=project.name)
        if ok and new_name:
            existing_project = self.db_session.query(Project).filter_by(name=new_name).first()
            if existing_project:
                QMessageBox.warning(self, "Помилка", "Проєкт з такою назвою вже існує.")
                return
            project.name = new_name
            self.db_session.commit()
            self.load_projects()

    def open_project_details(self, index):
        project_name = self.projects_model.itemFromIndex(index).data(Qt.UserRole)
        project = self.db_session.query(Project).filter_by(name=project_name).first()
        if project:
            self.main_window.open_project_details(project)
        else:
            print("AAAAAAAAAAAAAAAAAAAAAAAA")
