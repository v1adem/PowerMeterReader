from PyQt5 import QtWidgets
from PyQt5.QtCore import QSortFilterProxyModel, Qt, QTimer
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView, QPushButton, QHBoxLayout, QDialog
from sqlalchemy import desc

from models.Admin import Admin
from models.Report import SDM120Report, SDM630Report
from rtu.DataCollector import get_data_from_device


class DeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session
        self.main_screen = main_window

        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.label = QLabel(f"Ім'я пристрою: {device.name} | Модель пристрою: {device.model}")
        top_layout.addWidget(self.label)

        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon("pyqt/icons/refresh.png"))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_report_data)
        top_layout.addWidget(refresh_button)

        request_button = QPushButton("Моніторинг")
        request_button.setFixedSize(120, 36)
        request_button.clicked.connect(self.show_current_data_dialog)
        top_layout.addWidget(request_button)

        layout.addLayout(top_layout)

        self.report_table = QTableView(self)
        layout.addWidget(self.report_table)

        self.load_report_data()

    def load_report_data(self):
        if self.device.model == "SDM120":
            report_data = self.db_session.query(SDM120Report).filter_by(device_id=self.device.id).order_by(
                desc(SDM120Report.id)).all()
        elif self.device.model == "SDM630":
            report_data = self.db_session.query(SDM630Report).filter_by(device_id=self.device.id).order_by(
                desc(SDM630Report.id)).all()
        else:
            report_data = []

        model = self.create_table_model(report_data, self.device)

        # Створення і налаштування сортувального проксі
        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        self.report_table.setModel(proxy_model)

        # Дозволяє сортувати за будь-якою колонкою
        self.report_table.setSortingEnabled(True)

        self.report_table.resizeColumnsToContents()
        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

    def create_table_model(self, report_data, device):
        columns = set()
        parameter_units = {}
        if device.parameters:
            for param in device.parameters.split(','):
                param_name, unit = param.split(':')
                parameter_units[param_name.strip()] = unit.strip()

        for report in report_data:
            for column_name in report.__table__.columns.keys():
                if column_name not in ['id', 'device_id'] and getattr(report, column_name) is not None:
                    columns.add(column_name)

        columns = sorted(columns)

        model = QStandardItemModel(len(report_data), len(columns))

        header_labels = []
        for column in columns:
            unit = parameter_units.get(column, "")
            header_labels.append(f"{column} ({unit})" if unit else column)

        model.setHorizontalHeaderLabels(header_labels)

        for row, report in enumerate(report_data):
            for col, column in enumerate(columns):
                value = getattr(report, column)
                model.setItem(row, col, QStandardItem(str(value) if value is not None else ""))

        return model

    def show_current_data_dialog(self):
        # Функція для отримання та оновлення даних
        def update_data():
            data = get_data_from_device(self.device, self.db_session.query(Admin).first().port,
                                        self.device.get_parameter_names())

            # Оновлення значень у таблиці без очищення моделі
            for row, (key, value) in enumerate(data.items()):
                model.setItem(row, 1, QStandardItem(str(value) if value is not None else ""))
                unit = parameter_units.get(key, "")
                model.setItem(row, 2, QStandardItem(unit))

            # Оновлення ширини колонок (можна прибрати, якщо не потрібно)
            data_table.resizeColumnsToContents()

        # Створення діалогового вікна
        parameter_units = {}
        if self.device.parameters:
            for param in self.device.parameters.split(','):
                param_name, unit = param.split(':')
                parameter_units[param_name.strip()] = unit.strip()

        dialog = QDialog(self)
        dialog.setWindowTitle("Поточні дані")
        dialog_layout = QVBoxLayout(dialog)

        data_table = QTableView(dialog)
        parameter_names = self.device.get_parameter_names()  # Отримуємо назви параметрів

        # Створення моделі з початковим розміром, відповідним до кількості параметрів
        model = QStandardItemModel(len(parameter_names), 3)
        model.setHorizontalHeaderLabels(["Параметр", "Значення", "Од. вим"])

        # Заповнення імен параметрів і одиниць вимірювання
        for row, key in enumerate(parameter_names):
            model.setItem(row, 0, QStandardItem(key))
            model.setItem(row, 1, QStandardItem(""))
            model.setItem(row, 2, QStandardItem(parameter_units.get(key, "")))

        data_table.setModel(model)
        header = data_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        dialog_layout.addWidget(data_table)

        # Налаштування таймера для періодичного оновлення
        timer = QTimer(dialog)
        timer.timeout.connect(update_data)
        timer.start(1000)  # Оновлення кожну секунду

        # Перший виклик оновлення даних
        update_data()

        # Зупинка таймера при закритті діалогу
        dialog.finished.connect(timer.stop)

        dialog.exec()
