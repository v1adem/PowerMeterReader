from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QListView, QPushButton, QInputDialog, QMessageBox, \
    QHBoxLayout, QDialog, QFormLayout, QComboBox, QLineEdit, QDialogButtonBox, QSpinBox
from PyQt5.QtCore import Qt, QSize
from models.Device import Device


class ProjectViewWidget(QWidget):
    def __init__(self, main_window, project):
        super().__init__(main_window)
        self.main_window = main_window
        self.project = project
        self.db_session = main_window.db_session
        self.isAdmin = main_window.isAdmin

        layout = QVBoxLayout(self)

        self.label = QLabel(f"Деталі проєкту: {project.name}")
        layout.addWidget(self.label)

        self.devices_list = QListView(self)
        layout.addWidget(self.devices_list)

        self.devices_model = QStandardItemModel()
        self.devices_list.setModel(self.devices_model)

        self.load_devices()

        self.add_device_button = QPushButton("Додати новий пристрій", self)
        layout.addWidget(self.add_device_button)
        if not self.isAdmin:
            self.add_device_button.setDisabled(True)
        self.add_device_button.clicked.connect(self.add_new_device)

        self.devices_list.doubleClicked.connect(self.open_device_details)

    def load_devices(self):
        self.devices_model.clear()
        devices = self.db_session.query(Device).filter_by(project_id=self.project.id).all()

        for device in devices:
            item = QStandardItem()
            item.setData(device.name, Qt.UserRole)
            item.setSizeHint(QSize(0, 36))
            self.devices_model.appendRow(item)

            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.addWidget(QLabel(device.name))

            edit_button = QPushButton()
            edit_button.setIcon(QIcon("pyqt/icons/edit.png"))
            edit_button.setFixedSize(24, 24)
            edit_button.clicked.connect(lambda _, d=device: self.edit_device(d))

            delete_button = QPushButton()
            delete_button.setIcon(QIcon("pyqt/icons/delete.png"))
            delete_button.setFixedSize(24, 24)
            delete_button.clicked.connect(lambda _, d=device: self.delete_device(d))

            item_layout.addWidget(edit_button)
            item_layout.addWidget(delete_button)
            item_layout.setContentsMargins(0, 0, 0, 0)

            self.devices_list.setIndexWidget(item.index(), item_widget)

    def add_new_device(self):
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
            device_address_input.setRange(1, 255)  # Обмежуємо діапазон від 1 до 255
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

                existing_device = self.db_session.query(Device).filter_by(name=device_name, project_id=self.project.id).first()
                if existing_device:
                    QMessageBox.warning(self, "Помилка", "Пристрій з такою назвою вже існує в проєкті.")
                    return

                existing_address = self.db_session.query(Device).filter_by(device_address=device_address, project_id=self.project.id).first()
                if existing_address:
                    QMessageBox.warning(self, "Помилка", "Пристрій з такою адресою вже існує в проєкті.")
                    return

                new_device = Device(name=device_name, manufacturer=manufacturer, model=model, device_address=device_address, project_id=self.project.id)
                self.db_session.add(new_device)
                self.db_session.commit()

                self.load_devices()
        except Exception as e:
            print(f"Помилка при додаванні пристрою: {e}")
            QMessageBox.critical(self, "Помилка", "Не вдалося додати пристрій.")

    def edit_device(self, device):
        """Редагує дані пристрою."""
        new_name, ok = QInputDialog.getText(self, "Редагувати пристрій", "Введіть нову назву:", text=device.name)
        if ok and new_name:
            device.name = new_name
            self.db_session.commit()
            self.load_devices()

    def delete_device(self, device):
        reply = QMessageBox.question(self, "Підтвердження видалення",
                                     f"Ви впевнені, що хочете видалити пристрій '{device.name}'?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db_session.delete(device)
            self.db_session.commit()
            self.load_devices()

    def open_device_details(self, index):
        device_name = self.devices_model.itemFromIndex(index).data(Qt.UserRole)
        device = self.db_session.query(Device).filter_by(name=device_name, project_id=self.project.id).first()
        if device:
            self.main_window.open_device_details(device)
        else:
            print("Пристрій не знайдено.")
