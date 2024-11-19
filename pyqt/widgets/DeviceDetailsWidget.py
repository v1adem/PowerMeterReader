from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon, QStandardItem, QStandardItemModel, QFont
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QLabel, QWidget, QSplitter, QTableView, QCalendarWidget, \
    QHBoxLayout, QDialog, QLCDNumber
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from sqlalchemy import desc

from models.Report import SDM120Report, SDM630Report

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure


class DeviceDetailsWidget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session
        self.main_window = main_window
        self.main_window.set_big_window()

        layout = QVBoxLayout(self)

        # Основний горизонтальний QSplitter
        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)  # Забороняємо колапс секцій
        layout.addWidget(main_splitter)

        # Ліва частина
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
        main_splitter.addWidget(left_widget)

        # Права частина з вертикальною поділкою
        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)  # Забороняємо колапс секцій
        main_splitter.addWidget(right_splitter)

        # Верхня частина правого спліттера (графіки)
        top_right_widget = QWidget()
        top_right_layout = QVBoxLayout(top_right_widget)

        # Кнопка "Обрати проміжок"
        self.select_range_button = QPushButton("Обрати проміжок")
        self.select_range_button.clicked.connect(self.open_date_range_dialog)
        top_right_layout.addWidget(self.select_range_button)

        # Графіки
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        top_right_layout.addWidget(self.canvas)

        right_splitter.addWidget(top_right_widget)

        # Нижня частина правого спліттера
        bottom_right_widget = QWidget()
        bottom_right_layout = QHBoxLayout(
            bottom_right_widget)  # Змінено на QHBoxLayout для розташування індикаторів в ряд

        # Створюємо індикатори
        self.voltage_lcd = QLCDNumber()
        self.voltage_lcd.setSegmentStyle(QLCDNumber.Flat)
        #self.voltage_lcd.setFixedHeight(50)  # Задаємо фіксовану висоту

        self.current_lcd = QLCDNumber()
        self.current_lcd.setSegmentStyle(QLCDNumber.Flat)
        #self.current_lcd.setFixedHeight(50)

        self.energy_lcd = QLCDNumber()
        self.energy_lcd.setSegmentStyle(QLCDNumber.Flat)
        #self.energy_lcd.setFixedHeight(50)

        # Підписи до індикаторів
        voltage_label = QLabel("Напруга (V)")
        voltage_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        current_label = QLabel("Струм (A)")
        current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        energy_label = QLabel("Енергія (kWh)")
        energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        # Додаємо індикатори і підписи в розмітку
        voltage_layout = QVBoxLayout()
        voltage_layout.addWidget(voltage_label)
        voltage_layout.addWidget(self.voltage_lcd)

        current_layout = QVBoxLayout()
        current_layout.addWidget(current_label)
        current_layout.addWidget(self.current_lcd)

        energy_layout = QVBoxLayout()
        energy_layout.addWidget(energy_label)
        energy_layout.addWidget(self.energy_lcd)

        bottom_right_layout.addLayout(voltage_layout)
        bottom_right_layout.addLayout(current_layout)
        bottom_right_layout.addLayout(energy_layout)

        right_splitter.addWidget(bottom_right_widget)

        # Встановлюємо рівний поділ для головного сплітера
        self.set_splitter_fixed_ratios(main_splitter, [1, 1])

        # Встановлюємо пропорцію 2:1 для правого вертикального сплітера
        self.set_splitter_fixed_ratios(right_splitter, [3, 1])

        self.load_report_data()
        self.plot_graphs()

    def set_splitter_fixed_ratios(self, splitter, ratios):
        """
        Встановлює фіксовані розміри для секцій сплітера на основі вказаних співвідношень.
        """
        total = sum(ratios)
        sizes = [int(ratio / total * splitter.size().width()) for ratio in ratios]
        splitter.setSizes(sizes)
        splitter.handle(1).setEnabled(False)  # Забороняємо рух ручки

    def update_indicators(self):
        """Оновлює значення індикаторів на основі останнього репорту."""
        if self.device.model == "SDM120":
            last_report = self.db_session.query(SDM120Report).filter_by(device_id=self.device.id).order_by(
                desc(SDM120Report.timestamp)).first()
        elif self.device.model == "SDM630":
            last_report = self.db_session.query(SDM630Report).filter_by(device_id=self.device.id).order_by(
                desc(SDM630Report.timestamp)).first()
        else:
            last_report = None

        if last_report:
            # Виводимо значення в індикатори
            self.voltage_lcd.display(getattr(last_report, 'voltage', 0))
            self.current_lcd.display(getattr(last_report, 'current', 0))
            self.energy_lcd.display(getattr(last_report, 'total_active_energy', 0))

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
        self.report_table.sortByColumn(4, Qt.AscendingOrder)  # 0 - індекс стовпця з timestamp

        self.report_table.setSortingEnabled(True)
        self.report_table.resizeColumnsToContents()

        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.update_indicators()

    def plot_graphs(self, start_date=None, end_date=None):
        """Малює графіки для вибраного проміжку або всіх даних."""
        # Отримуємо дані для графіків з таблиці
        report_data = self.db_session.query(SDM120Report).filter_by(device_id=self.device.id).order_by(
            desc(SDM120Report.timestamp)).all()

        timestamps = []
        voltages = []
        currents = []
        energies = []

        for report in report_data:
            timestamp = getattr(report, 'timestamp')  # timestamp є datetime.datetime
            if start_date and end_date:
                # Порівнюємо тільки дати
                if not (start_date <= timestamp.date() <= end_date):
                    continue
            timestamps.append(timestamp)
            voltages.append(getattr(report, 'voltage', 0))
            currents.append(getattr(report, 'current', 0))
            energies.append(getattr(report, 'total_active_energy', 0))

        # Очищення попередніх графіків
        self.figure.clear()

        # Налаштування параметрів для графіків
        small_fontsize = 8
        ax1 = self.figure.add_subplot(311)
        ax2 = self.figure.add_subplot(312)
        ax3 = self.figure.add_subplot(313)

        # Налаштування графіків
        ax1.plot(timestamps, voltages, label="Напруга (V)")
        ax1.set_ylabel("Напруга (V)", fontsize=small_fontsize)
        ax1.legend(fontsize=small_fontsize)

        ax2.plot(timestamps, currents, label="Струм (A)", color="orange")
        ax2.set_ylabel("Струм (A)", fontsize=small_fontsize)
        ax2.legend(fontsize=small_fontsize)

        ax3.plot(timestamps, energies, label="Повна Активна Енергія (kWh)", color="green")
        ax3.set_ylabel("Енергія (kWh)", fontsize=small_fontsize)
        ax3.legend(fontsize=small_fontsize)

        # Зменшення розміру полів
        self.figure.tight_layout(pad=1.0, h_pad=0.5, w_pad=0.5)

        # Малювання графіків
        self.canvas.draw()

    def open_date_range_dialog(self):
        """Відкриває діалог для вибору діапазону дат."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Обрати проміжок")
        dialog.setFixedSize(500, 500)

        layout = QVBoxLayout(dialog)

        self.start_calendar = QCalendarWidget()
        self.start_calendar.setGridVisible(True)
        layout.addWidget(QLabel("Початкова дата:"))
        layout.addWidget(self.start_calendar)

        self.end_calendar = QCalendarWidget()
        self.end_calendar.setGridVisible(True)
        layout.addWidget(QLabel("Кінцева дата:"))
        layout.addWidget(self.end_calendar)

        button_layout = QHBoxLayout()
        confirm_button = QPushButton("Підтвердити")
        confirm_button.clicked.connect(lambda: self.apply_date_range(dialog))
        cancel_button = QPushButton("Скасувати")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        dialog.exec_()

    def apply_date_range(self, dialog):
        """Застосовує вибраний діапазон дат."""
        start_date = self.start_calendar.selectedDate().toPyDate()
        end_date = self.end_calendar.selectedDate().toPyDate()
        self.plot_graphs(start_date=start_date, end_date=end_date)
        dialog.accept()