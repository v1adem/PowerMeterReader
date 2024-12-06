import asyncio
from PyQt5.QtCore import Qt, QTimer, QSize
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListView, QPushButton, QMessageBox,
    QHBoxLayout, QDialog, QFormLayout,
    QLineEdit, QComboBox, QSpinBox, QDialogButtonBox
)
from sqlalchemy.future import select
from qasync import asyncSlot
from sqlalchemy.exc import SQLAlchemyError

from config import resource_path
from models.Device import Device

from sqlalchemy import text


class ProjectViewWidget(QWidget):
    def __init__(self, main_window, project):
        super().__init__(main_window)
        self.main_window = main_window
        self.project = project
        self.db_session = main_window.db_session
        self.isAdmin = main_window.isAdmin

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Деталі проєкту: {project.name}")
        self.label.setStyleSheet("font-size: 18px;")
        layout.addWidget(self.label)

        self.devices_list = QListView(self)
        layout.addWidget(self.devices_list)

        self.devices_model = QStandardItemModel()
        self.devices_list.setModel(self.devices_model)

        self.add_device_button = QPushButton("Додати новий пристрій", self)
        layout.addWidget(self.add_device_button)
        if not self.isAdmin:
            self.add_device_button.setDisabled(True)
        self.add_device_button.setStyleSheet("font-size: 18px;")
        self.add_device_button.clicked.connect(self.add_new_device)

        self.devices_list.doubleClicked.connect(self.on_device_double_clicked)

        # Завантажуємо пристрої
        asyncio.create_task(self.load_devices())

    @asyncSlot()
    async def on_device_double_clicked(self, index):
        """Обробка подвійного кліку по пристрою."""
        await self.open_device_details()

    async def load_devices(self):
        """Асинхронне завантаження пристроїв з бази даних."""
        try:
            async with self.db_session() as session:
                async with session.begin():
                    # Use SQLAlchemy ORM to query for Device instances
                    query = select(Device).filter(Device.project_id == self.project.id)
                    result = await session.execute(query)
                    devices = result.scalars().all()  # Get instances of Device

            self.devices_model.clear()

            for index, device in enumerate(devices, start=1):
                item = QStandardItem()
                item.setData(device.name, Qt.UserRole)
                item.setSizeHint(QSize(0, 60))
                self.devices_model.appendRow(item)

                item_widget = QWidget()
                item_layout = QHBoxLayout(item_widget)

                # Порядковий номер
                number_label = QLabel(f"{index}")
                number_label.setStyleSheet("font-size: 14px; color: #666666;")
                number_label.setFixedWidth(40)
                number_label.setAlignment(Qt.AlignCenter)
                item_layout.addWidget(number_label)

                name_label = QLabel(device.name)
                name_label.setStyleSheet("font-size: 18px;")
                item_layout.addWidget(name_label)

                # Check the reading status using the method on the Device object
                toggle_status_button = QPushButton(
                    "Увімкнути" if not device.get_reading_status() else "Вимкнути"
                )
                toggle_status_button.setFixedSize(100, 36)
                toggle_status_button.clicked.connect(
                    lambda _, d=device, btn=toggle_status_button: self.toggle_device_status(d, btn)
                )
                item_layout.addWidget(toggle_status_button)

                edit_button = QPushButton()
                edit_button.setFixedSize(36, 36)
                edit_button.clicked.connect(lambda _, d=device: self.edit_device(d))
                edit_button.setIcon(QIcon(resource_path("pyqt/icons/edit.png")))
                item_layout.addWidget(edit_button)

                delete_button = QPushButton()
                delete_button.setFixedSize(36, 36)
                delete_button.clicked.connect(lambda _, d=device: self.delete_device(d))
                delete_button.setIcon(QIcon(resource_path("pyqt/icons/delete.png")))
                item_layout.addWidget(delete_button)

                item_layout.setContentsMargins(0, 0, 0, 0)

                self.devices_list.setIndexWidget(item.index(), item_widget)

        except SQLAlchemyError as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося завантажити пристрої: {e}")

    @asyncSlot()
    async def update_device_statuses(self):
        """Асинхронне оновлення статусів пристроїв."""
        try:
            async with self.db_session() as session:  # Create an AsyncSession instance
                async with session.begin():
                    query = text("SELECT * FROM devices WHERE project_id = :project_id")

                    result = await session.execute(query, {'project_id': self.project.id})
                    devices = result.fetchall()

            for row in range(self.devices_model.rowCount()):
                item = self.devices_model.item(row)
                device_name = item.data(Qt.UserRole)
                device = next((d for d in devices if d.name == device_name), None)

                if device:
                    toggle_button = item.data(Qt.UserRole + 1)
                    if toggle_button:
                        new_status = "Увімкнути" if not device.get_reading_status() else "Вимкнути"
                        toggle_button.setText(new_status)
        except SQLAlchemyError as e:
            print(f"Error updating device statuses: {e}")

    @asyncSlot()
    async def toggle_device_status(self, device, button):
        """Асинхронне переключення статусу пристрою."""
        try:
            # Використовуємо асинхронну транзакцію для комітів
            async with self.db_session() as session:  # Забезпечуємо доступ до асинхронної сесії
                # Зміна статусу пристрою
                device.toggle_reading_status()
                session.add(device)  # Додаємо змінений об'єкт до сесії
                await session.commit()  # Використовуємо асинхронний commit
                button.setText("Увімкнути" if not device.get_reading_status() else "Вимкнути")
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося змінити статус пристрою: {e}")

    @asyncSlot()
    async def add_new_device(self):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Додати новий пристрій")
            form_layout = QFormLayout(dialog)

            device_name_input = QLineEdit(dialog)
            form_layout.addRow("Назва пристрою:", device_name_input)

            manufacturer_input = QComboBox(dialog)
            manufacturer_input.addItem("Eastron")
            form_layout.addRow("Виробник:", manufacturer_input)

            model_input = QComboBox(dialog)
            model_input.addItems(["SDM120", "SDM630"])
            form_layout.addRow("Модель:", model_input)

            device_address_input = QSpinBox(dialog)
            device_address_input.setRange(1, 255)
            form_layout.addRow("Адреса пристрою:", device_address_input)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            form_layout.addRow(buttons)

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() == QDialog.Accepted:
                device_name = device_name_input.text()
                manufacturer = manufacturer_input.currentText()
                model = model_input.currentText()
                device_address = device_address_input.value()

                async with self.db_session() as session:
                    async with session.begin():
                        existing_device = await session.execute(
                            select(Device).where(
                                Device.name == device_name,
                                Device.project_id == self.project.id
                            )
                        )
                        if existing_device.scalars().first():
                            QMessageBox.warning(self, "Помилка", "Пристрій з такою назвою вже існує в проєкті.")
                            return

                        existing_address = await session.execute(
                            select(Device).where(
                                Device.device_address == device_address,
                                Device.project_id == self.project.id
                            )
                        )
                        if existing_address.scalars().first():
                            QMessageBox.warning(self, "Помилка", "Пристрій з такою адресою вже існує в проєкті.")
                            return

                        new_device = Device(
                            name=device_name, manufacturer=manufacturer, model=model,
                            device_address=device_address, project_id=self.project.id
                        )
                        session.add(new_device)
                        await session.commit()
                        await self.load_devices()
                        await self.edit_device(new_device)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося додати пристрій: {e}")

    @asyncSlot()
    async def edit_device(self, device):
        try:
            dialog = QDialog(self)
            dialog.setWindowTitle("Редагувати пристрій")
            form_layout = QFormLayout(dialog)

            device_name_input = QLineEdit(dialog)
            device_name_input.setText(device.name)
            form_layout.addRow("Назва пристрою:", device_name_input)

            manufacturer_input = QComboBox(dialog)
            manufacturer_input.addItem("Eastron")
            manufacturer_input.setCurrentText(device.manufacturer)
            form_layout.addRow("Виробник:", manufacturer_input)

            model_input = QComboBox(dialog)
            model_input.addItems(["SDM120", "SDM630"])
            model_input.setCurrentText(device.model)
            form_layout.addRow("Модель:", model_input)

            device_address_input = QSpinBox(dialog)
            device_address_input.setRange(1, 255)
            device_address_input.setValue(device.device_address)
            form_layout.addRow("Адреса пристрою:", device_address_input)

            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, dialog)
            form_layout.addRow(buttons)

            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)

            if dialog.exec() == QDialog.Accepted:
                async with self.db_session() as session:
                    async with session.begin():
                        device.name = device_name_input.text()
                        device.manufacturer = manufacturer_input.currentText()
                        device.model = model_input.currentText()
                        device.device_address = device_address_input.value()
                        await session.commit()
                        await self.load_devices()
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося редагувати пристрій: {e}")

    @asyncSlot()
    async def delete_device(self, device):
        reply = QMessageBox.question(
            self, "Підтвердження видалення",
            f"Ви впевнені, що хочете видалити пристрій '{device.name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                async with self.db_session() as session:
                    async with session.begin():
                        await session.delete(device)
                        await session.commit()
                        await self.load_devices()
            except Exception as e:
                QMessageBox.critical(self, "Помилка", f"Не вдалося видалити пристрій: {e}")

    @asyncSlot()
    async def open_device_details(self, index):
        try:
            device_name = self.devices_model.itemFromIndex(index).data(Qt.UserRole)
            async with self.db_session() as session:
                async with session.begin():
                    device = await session.execute(
                        select(Device).where(
                            Device.name == device_name,
                            Device.project_id == self.project.id
                        )
                    )
                    device = device.scalars().first()
                    if device:
                        await self.main_window.open_device_details(device)
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося відкрити деталі пристрою: {e}")
