from PyQt5.QtGui import QStandardItemModel, QStandardItem
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableView

from models.Report import SDM120Report, SDM630Report


class DeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session

        layout = QVBoxLayout(self)
        self.setWindowTitle(f"Деталі пристрою: {device.name}")

        # Заголовок
        self.label = QLabel(f"Модель пристрою: {device.model}")
        layout.addWidget(self.label)

        # Таблиця звітів
        self.report_table = QTableView(self)
        layout.addWidget(self.report_table)

        # Завантаження даних
        self.load_report_data()

    def load_report_data(self):
        """Завантажує відповідні дані звіту для пристрою."""
        if self.device.model == "SDM120":
            report_data = self.db_session.query(SDM120Report).filter_by(device_id=self.device.id).all()
        elif self.device.model == "SDM630":
            report_data = self.db_session.query(SDM630Report).filter_by(device_id=self.device.id).all()
        else:
            report_data = []

        # Встановлюємо модель для таблиці з даними
        model = self.create_table_model(report_data)
        self.report_table.setModel(model)

    def create_table_model(self, report_data):
        columns = set()
        for report in report_data:
            for column_name in report.__table__.columns.keys():  # Використовуємо ключі для доступу до назв колонок
                # Пропускаємо колонки id та device_id
                if column_name not in ['id', 'device_id'] and getattr(report, column_name) is not None:
                    columns.add(column_name)

        # Сортуємо колонки
        columns = sorted(columns)

        # Створюємо модель для таблиці
        model = QStandardItemModel(len(report_data), len(columns))
        model.setHorizontalHeaderLabels(columns)

        # Заповнюємо таблицю
        for row, report in enumerate(report_data):
            for col, column in enumerate(columns):
                value = getattr(report, column)
                model.setItem(row, col, QStandardItem(str(value) if value is not None else ""))

        # Повертаємо модель
        return model

