from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QLabel, QWidget, QSplitter, QTableView
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from sqlalchemy import desc

from models.Report import SDM120Report, SDM630Report


class DeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session
        self.main_window = main_window
        self.main_window.set_big_window()

        layout = QVBoxLayout(self)

        # Створення QSplitter для горизонтального поділу
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(0)  # Вимикаємо зміну ширини
        layout.addWidget(splitter)

        # Ліва половина з усіма елементами
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.label = QLabel(f"Ім'я пристрою: {device.name} | Модель пристрою: {device.model}")
        table_layout.addWidget(self.label)

        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon("pyqt/icons/refresh.png"))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_report_data)
        table_layout.addWidget(refresh_button)

        self.report_table = QTableView(self)
        table_layout.addWidget(self.report_table)

        left_layout.addWidget(table_widget)
        splitter.addWidget(left_widget)

        # Права частина залишиться пустою
        right_widget = QWidget()
        splitter.addWidget(right_widget)

        self.load_report_data()

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

    def load_report_data(self):
        if self.device.model == "SDM120":
            report_data = self.db_session.query(SDM120Report).filter_by(device_id=self.device.id).order_by(
                desc(SDM120Report.timestamp)).all()
        elif self.device.model == "SDM630":
            report_data = self.db_session.query(SDM630Report).filter_by(device_id=self.device.id).order_by(
                desc(SDM630Report.timestamp)).all()
        else:
            report_data = []

        model = self.create_table_model(report_data, self.device)

        proxy_model = QSortFilterProxyModel()
        proxy_model.setSourceModel(model)
        proxy_model.setSortCaseSensitivity(Qt.CaseInsensitive)

        self.report_table.setModel(proxy_model)

        # Установлюємо сортування за полем timestamp (від найновішого до найстарішого)
        self.report_table.sortByColumn(0, Qt.AscendingOrder)  # 0 - індекс стовпця з timestamp

        self.report_table.setSortingEnabled(True)
        self.report_table.resizeColumnsToContents()

        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
