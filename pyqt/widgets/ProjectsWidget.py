import asyncio
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListView, QPushButton, QMessageBox, QInputDialog, QComboBox, QHBoxLayout, QDialog,
    QDialogButtonBox, QSpinBox, QLineEdit
)
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtCore import Qt, QSize
from pymodbus.client import ModbusSerialClient
from qasync import asyncSlot
from sqlalchemy import select

from config import resource_path
from models.Project import Project


class ProjectsWidget(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window
        self.db_session = main_window.db_session
        self.isAdmin = main_window.isAdmin

        self.layout = QVBoxLayout(self)

        self.projects_label = QLabel("Проєкти", self)
        self.projects_label.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.projects_label)

        self.projects_list = QListView(self)
        self.layout.addWidget(self.projects_list)

        self.projects_model = QStandardItemModel()
        self.projects_list.setModel(self.projects_model)

        self.projects_list.doubleClicked.connect(self.on_project_double_click)

        self.add_project_button = QPushButton("Додати новий проєкт", self)
        self.add_project_button.setStyleSheet("font-size: 18px;")
        self.layout.addWidget(self.add_project_button)

        if not self.isAdmin:
            self.add_project_button.setDisabled(True)

        self.add_project_button.clicked.connect(self.add_new_project)

        asyncio.create_task(self.load_projects())

    def on_project_double_click(self, index):
        """Синхронна функція для обробки подвійного кліку на проекті."""
        asyncio.create_task(self.open_project_details(index))

    async def update_connection_status(self, project, label):
        if await self.check_project_connection(project):
            label.setText("✅ З'єднання успішне | Порт:")
            label.setStyleSheet("color: green; font-size: 14px; alignment: right; margin: 0px; padding: 0px; border: 0px solid #cccccc;")
        else:
            label.setText("❌ Немає з'єднання | Порт:")
            label.setStyleSheet("color: red; font-size: 14px; alignment: right; margin: 0px; padding: 0px; border: 0px solid #cccccc;")

    async def load_projects(self):
        """Асинхронне завантаження проєктів з бази даних та оновлення таблиці"""
        self.projects_model.clear()

        available_ports = [f"COM{i}" for i in range(1, 256)]

        async with self.db_session() as session:
            async with session.begin():
                projects = await session.execute(select(Project))
                projects = projects.scalars().all()

        for index, project in enumerate(projects, start=1):
            item = QStandardItem()
            item.setData(project.name, Qt.UserRole)
            cell_height = 60
            item.setSizeHint(QSize(0, cell_height))
            self.projects_model.appendRow(item)

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_widget.setStyleSheet("border: 1px solid #cccccc;")

            # Порядковий номер
            number_label = QLabel(f"{index}")
            number_label.setStyleSheet("font-size: 14px; color: #666666; border: 0px solid #cccccc;")
            number_label.setFixedWidth(40)
            number_label.setAlignment(Qt.AlignCenter)
            item_layout.addWidget(number_label)

            name_label = QLabel(project.name)
            name_label.setStyleSheet("font-size: 18px; border: 0px solid #cccccc;")
            item_layout.addWidget(name_label)

            port_combo = QComboBox()
            port_combo.addItems(available_ports)

            port_value = f"COM{project.port}" if project.port is not None else ""
            if port_value in available_ports:
                port_combo.setCurrentText(port_value)
            else:
                port_combo.setCurrentText("")

            port_combo.setFixedWidth(100)
            port_combo.setStyleSheet("font-size: 14px; border: 0px solid #cccccc;")
            port_combo.currentIndexChanged.connect(
                lambda _, p=project, combo=port_combo: asyncio.create_task(
                    self.change_project_port(p, combo.currentText())
                )
            )

            connection_label = QLabel()
            await self.update_connection_status(project, connection_label)
            connection_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            connection_label.setFixedWidth(200)
            item_layout.addWidget(connection_label)

            item_layout.addWidget(port_combo)

            edit_button = QPushButton()
            edit_button.setIcon(QIcon(resource_path("pyqt/icons/edit.png")))
            edit_button.setStyleSheet("margin: 0px;")
            edit_button.setFixedSize(24, 24)
            edit_button.setIconSize(QSize(22, 22))
            edit_button.clicked.connect(lambda _, p=project: asyncio.create_task(self.edit_project(p)))

            item_layout.addWidget(edit_button)

            delete_button = QPushButton()
            delete_button.setIcon(QIcon(resource_path("pyqt/icons/delete.png")))
            delete_button.setFixedSize(24, 24)
            delete_button.setStyleSheet("margin: 0px;")
            delete_button.setIconSize(QSize(22, 22))
            delete_button.clicked.connect(lambda _, p=project: asyncio.create_task(self.delete_project(p)))

            item_layout.addWidget(delete_button)

            self.projects_list.setIndexWidget(self.projects_model.indexFromItem(item), item_widget)

    async def change_project_port(self, project, new_port):
        """Асинхронна зміна порту проєкту"""
        if new_port:
            try:
                port_number = int(new_port.replace('COM', ''))
                async with self.db_session() as session:
                    async with session.begin():
                        project.port = port_number
                        session.add(project)
                    await session.commit()
                print(f"Project {project.name} port updated to COM{port_number}")

                await self.update_table()

            except ValueError:
                print(f"Invalid port value: {new_port}")

    async def update_table(self):
        """Метод для оновлення таблиці проєктів"""
        await self.load_projects()

    async def check_project_connection(self, project):
        """Перевірка з'єднання проєкту"""
        client = ModbusSerialClient(
            port=f"COM{project.port}",
            baudrate=project.baudrate,
            parity=project.parity,
            stopbits=project.stopbits,
            bytesize=project.bytesize,
            timeout=0.1
        )
        try:
            if client.connect():
                return True
            else:
                return False
        except Exception as e:
            print(e)
            return False

    @asyncSlot()
    async def add_new_project(self):
        """Асинхронне додавання нового проекту"""
        project_name, ok = QInputDialog.getText(self, "Додати новий проект", "Введіть назву проекту:")

        if ok and project_name:
            async with self.db_session() as session:
                async with session.begin():
                    # Перевіряємо, чи існує проект із такою назвою
                    result = await session.execute(select(Project).where(Project.name == project_name))
                    existing_project = result.scalar_one_or_none()

                    if existing_project:  # Якщо проект вже існує
                        QMessageBox.warning(self, "Помилка", "Проект з такою назвою вже існує")
                        return

                    # Якщо проект не знайдений, створюємо новий
                    new_project = Project(name=project_name, port=1)
                    session.add(new_project)
                    await session.commit()

            await self.load_projects()

    @asyncSlot()
    async def delete_project(self, project):
        """Видалення проєкту."""
        reply = QMessageBox.question(
            self,
            "Підтвердження видалення",
            f"Ви впевнені, що хочете видалити проєкт '{project.name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            async with self.db_session() as session:
                async with session.begin():
                    await session.delete(project)
            await self.load_projects()

    @asyncSlot()
    async def edit_project(self, project):
        """Редагування проєкту."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Редагувати проєкт")
        layout = QVBoxLayout(dialog)

        info_label = QLabel(
            "Усі параметри проєкту мають збігатися з налаштуваннями на пристроях і з налаштуваннями "
            "серійного порту Вашого ПК до якого підключений перетворювач."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        def open_device_manager():
            import os
            import platform
            if platform.system() == "Windows":
                os.system("start devmgmt.msc")
            else:
                QMessageBox.information(self, "Недоступно", "Функція доступна лише на Windows.")

        open_settings_button = QPushButton("Подивитися налаштування порту")
        open_settings_button.clicked.connect(open_device_manager)
        layout.addWidget(open_settings_button)

        # Поля редагування
        name_label = QLabel("Назва проєкту:")
        name_edit = QLineEdit(project.name)
        layout.addWidget(name_label)
        layout.addWidget(name_edit)

        description_label = QLabel("Опис:")
        description_edit = QLineEdit(project.description or "")
        layout.addWidget(description_label)
        layout.addWidget(description_edit)

        baudrate_label = QLabel("Baudrate:")
        baudrate_edit = QComboBox()
        baudrate_options = [1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200]
        baudrate_edit.addItems(map(str, baudrate_options))
        baudrate_edit.setCurrentText(str(project.baudrate))
        layout.addWidget(baudrate_label)
        layout.addWidget(baudrate_edit)

        bytesize_label = QLabel("Bytesize:")
        bytesize_edit = QSpinBox()
        bytesize_edit.setRange(5, 8)
        bytesize_edit.setValue(project.bytesize)
        layout.addWidget(bytesize_label)
        layout.addWidget(bytesize_edit)

        stopbits_label = QLabel("Stopbits:")
        stopbits_edit = QComboBox()
        stopbits_edit.addItems(["1", "1.5", "2"])
        stopbits_edit.setCurrentText(str(project.stopbits))
        layout.addWidget(stopbits_label)
        layout.addWidget(stopbits_edit)

        parity_label = QLabel("Parity:")
        parity_edit = QComboBox()
        parity_edit.addItems(["N", "E", "O"])
        parity_edit.setCurrentText(project.parity)
        layout.addWidget(parity_label)
        layout.addWidget(parity_edit)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(button_box)

        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)

        if dialog.exec_() == QDialog.Accepted:
            new_name = name_edit.text().strip()
            new_description = description_edit.text().strip()
            new_baudrate = int(baudrate_edit.currentText())
            new_bytesize = bytesize_edit.value()
            new_stopbits = float(stopbits_edit.currentText())
            new_parity = parity_edit.currentText()

            async with self.db_session() as session:
                async with session.begin():
                    if new_name != project.name:
                        existing_project = await session.execute(
                            select(Project).filter_by(name=new_name)
                        )
                        if existing_project.scalar():
                            QMessageBox.warning(self, "Помилка", "Проєкт з такою назвою вже існує.")
                            return

                    project.name = new_name
                    project.description = new_description
                    project.baudrate = new_baudrate
                    project.bytesize = new_bytesize
                    project.stopbits = new_stopbits
                    project.parity = new_parity

                    session.add(project)
            await self.load_projects()

    async def open_project_details(self, index):
        """Відкриття деталей проєкту."""
        project_name = self.projects_model.itemFromIndex(index).data(Qt.UserRole)
        async with self.db_session() as session:
            async with session.begin():
                project = await session.execute(select(Project).filter_by(name=project_name))
                project = project.scalar()
                if project:
                    self.main_window.open_project_details(project)
                else:
                    print("Couldn't find project")
