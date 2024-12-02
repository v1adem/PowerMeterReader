from datetime import datetime

import pyqtgraph as pg
import xlsxwriter

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QVBoxLayout, QPushButton, QLabel, QWidget, QSplitter, QTableView, QCalendarWidget, \
    QHBoxLayout, QDialog, QLCDNumber, QCheckBox, QDateEdit, QGridLayout, QInputDialog
from PyQt5.QtGui import QIcon, QStandardItemModel, QStandardItem, QFont
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QTime, QTimer, QDate
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from pyqtgraph import AxisItem

from sqlalchemy import desc
from models.Report import SDM120Report, SDM630Report, SDM120ReportTmp


class DateAxisItem(AxisItem):
    def tickStrings(self, values, scale, spacing):
        formatted_ticks = []
        for value in values:
            dt = datetime.fromtimestamp(value)

            if spacing < 3600:
                formatted_ticks.append(dt.strftime('%H:%M:%S'))
            elif spacing < 86400:
                formatted_ticks.append(dt.strftime('%d %B %H:%M'))
            else:
                formatted_ticks.append(dt.strftime('%d %B'))

        return formatted_ticks


class DeviceDetailsSDM120Widget(QWidget):
    def __init__(self, main_window, device):
        super().__init__(main_window)
        self.device = device
        self.db_session = main_window.db_session
        self.main_window = main_window

        layout = QVBoxLayout(self)

        main_splitter = QSplitter(Qt.Horizontal)
        main_splitter.setChildrenCollapsible(False)
        layout.addWidget(main_splitter)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        table_widget = QWidget()
        table_layout = QVBoxLayout(table_widget)
        self.label = QLabel(f"Ім'я пристрою: {device.name} | Модель пристрою: {device.model}")
        table_layout.addWidget(self.label)

        button_layout = QHBoxLayout()

        refresh_button = QPushButton()
        refresh_button.setIcon(QIcon("pyqt/icons/refresh.png"))
        refresh_button.setFixedSize(36, 36)
        refresh_button.clicked.connect(self.load_report_data)
        button_layout.addWidget(refresh_button)

        export_button = QPushButton("Експорт в Excel")
        export_button.setFixedHeight(36)
        export_button.clicked.connect(self.open_export_dialog)
        button_layout.addWidget(export_button)

        table_layout.addLayout(button_layout)

        self.report_table = QTableView(self)
        table_layout.addWidget(self.report_table)
        left_layout.addWidget(table_widget)
        main_splitter.addWidget(left_widget)

        right_splitter = QSplitter(Qt.Vertical)
        right_splitter.setChildrenCollapsible(False)
        main_splitter.addWidget(right_splitter)

        top_right_widget = QWidget()
        top_right_layout = QVBoxLayout(top_right_widget)

        self.select_range_button = QPushButton("Обрати проміжок")
        self.select_range_button.clicked.connect(self.open_date_range_dialog)
        top_right_layout.addWidget(self.select_range_button)

        self.voltage_graph_widget = pg.PlotWidget()
        self.current_graph_widget = pg.PlotWidget()
        self.energy_graph_widget = pg.PlotWidget()

        self.voltage_curve = self.voltage_graph_widget.plot(pen=pg.mkPen(color='b', width=2), name="Напруга")
        self.current_curve = self.current_graph_widget.plot(pen=pg.mkPen(color='r', width=2), name="Струм")

        self.energy_bar_item = pg.BarGraphItem(width=5, height=5, brush='g', x=1)
        self.energy_graph_widget.addItem(self.energy_bar_item)

        top_right_layout.addWidget(self.voltage_graph_widget)
        top_right_layout.addWidget(self.current_graph_widget)
        top_right_layout.addWidget(self.energy_graph_widget)

        self.auto_update_checkbox = QCheckBox("Автооновлення")
        self.auto_update_checkbox.setChecked(False)  # За замовчуванням увімкнено
        top_right_layout.addWidget(self.auto_update_checkbox)

        right_splitter.addWidget(top_right_widget)

        bottom_right_widget = QWidget()
        self.bottom_right_layout = QHBoxLayout(bottom_right_widget)

        # Ліва частина: Годинник
        self.left_layout = QVBoxLayout()

        # Заголовок "Поточний час"
        self.clock_title = QLabel("Поточний час")
        self.clock_title.setStyleSheet("font-size: 16pt; font-weight: bold;")
        self.clock_title.setAlignment(Qt.AlignCenter)  # Вирівнювання тексту по центру
        self.left_layout.addWidget(self.clock_title)

        # Годинник
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("font-size: 24pt;")  # Збільшений шрифт для годинника
        self.clock_label.setAlignment(Qt.AlignCenter)  # Вирівнювання по центру
        self.left_layout.addWidget(self.clock_label)

        self.left_layout.addStretch()

        # Права частина: Індикатори в сітці
        self.grid_layout = QGridLayout()

        # Індикатори
        self.voltage_lcd = QLCDNumber()
        self.voltage_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.current_lcd = QLCDNumber()
        self.current_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.power_lcd = QLCDNumber()
        self.power_lcd.setSegmentStyle(QLCDNumber.Flat)
        self.energy_lcd = QLCDNumber()
        self.energy_lcd.setSegmentStyle(QLCDNumber.Flat)

        # Підписи
        self.voltage_label = QLabel("Напруга (V)")
        self.voltage_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.current_label = QLabel("Струм (A)")
        self.current_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.power_label = QLabel("Потужність (W)")
        self.power_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        self.energy_label = QLabel("Спожито (kWh)")
        self.energy_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

        # Додавання до сітки
        self.grid_layout.addWidget(self.voltage_label, 0, 0)
        self.grid_layout.addWidget(self.voltage_lcd, 1, 0)
        self.grid_layout.addWidget(self.current_label, 0, 1)
        self.grid_layout.addWidget(self.current_lcd, 1, 1)
        self.grid_layout.addWidget(self.power_label, 2, 0)
        self.grid_layout.addWidget(self.power_lcd, 3, 0)
        self.grid_layout.addWidget(self.energy_label, 2, 1)
        self.grid_layout.addWidget(self.energy_lcd, 3, 1)

        # Додавання до головного компонувальника
        self.bottom_right_layout.addLayout(self.left_layout)  # Ліва частина
        self.bottom_right_layout.addLayout(self.grid_layout)  # Права частина (сітка)

        right_splitter.addWidget(bottom_right_widget)

        self.set_splitter_fixed_ratios(main_splitter, [1, 1])
        self.set_splitter_fixed_ratios(right_splitter, [3, 1])

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_ui)
        self.timer.setInterval(1000)
        self.timer.start()

        self.load_report_data()
        self.plot_graphs()
        self.set_light_theme()

    def set_splitter_fixed_ratios(self, splitter, ratios):
        total = sum(ratios)
        sizes = [int(ratio / total * splitter.size().width()) for ratio in ratios]
        splitter.setSizes(sizes)
        splitter.handle(1).setEnabled(False)

    def update_ui(self):
        self.update_clock()
        self.update_indicators()
        if self.auto_update_checkbox.isChecked():
            self.plot_graphs()

    def update_indicators(self):
        last_report = (self.db_session.query(SDM120ReportTmp)
                       .filter_by(device_id=self.device.id).order_by(desc(SDM120ReportTmp.timestamp)).first())
        if last_report:
            self.voltage_lcd.display(getattr(last_report, 'voltage', 0))
            self.current_lcd.display(getattr(last_report, 'current', 0))
            self.energy_lcd.display(getattr(last_report, 'total_active_energy', 0))
            self.power_lcd.display(getattr(last_report, 'active_power', 0))

    def update_clock(self):
        current_time = QTime.currentTime().toString("HH:mm:ss")
        self.clock_label.setText(f"{current_time}")

    def create_table_model(self, report_data, device):
        column_labels = {
            "timestamp": "Час",
            "total_active_energy": "Спожито",
            "voltage": "Напруга",
            "current": "Струм",
            "active_power": "Активна потужність",
            "apparent_power": "Повна потужність???",
            "reactive_power": "Реактивна потужність",
            "import_active_energy": "Вхідна активна енергія",
            "export_active_energy": "Вихідна активна енергія",
            "total_reactive_energy": "Загальна реактивна енергія",
            "frequency": "Частота",
        }

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
            custom_label = column_labels.get(column, column)
            unit = parameter_units.get(column, "")
            header_labels.append(f"{custom_label} ({unit})" if unit else custom_label)

        bold_font = QFont()
        bold_font.setBold(True)
        bold_font.setPointSize(12)

        for col_index, header in enumerate(header_labels):
            model.setHeaderData(col_index, Qt.Horizontal, header)
            model.setHeaderData(col_index, Qt.Horizontal, bold_font, Qt.FontRole)

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

        self.report_table.sortByColumn(3, Qt.DescendingOrder)

        self.report_table.setSortingEnabled(True)
        self.report_table.resizeColumnsToContents()

        header = self.report_table.horizontalHeader()
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)

        self.update_indicators()

    def plot_voltage(self, timestamps, voltages):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]

        self.voltage_graph_widget.clear()
        self.voltage_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})

        self.voltage_graph_widget.plot(
            timestamps_numeric,
            voltages,
            pen=pg.mkPen(color='b', width=2),
            name="Напруга"
        )
        self.voltage_graph_widget.setYRange(0, 400)

    def plot_current(self, timestamps, currents):
        timestamps_numeric = [ts.timestamp() for ts in timestamps]

        self.current_graph_widget.clear()
        self.current_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})

        self.current_graph_widget.plot(
            timestamps_numeric,
            currents,
            pen=pg.mkPen(color='r', width=2),
            name="Струм"
        )
        self.current_graph_widget.setYRange(0, 200)

    def plot_energy(self, hourly_timestamps, hourly_energy):
        hourly_timestamps_numeric = [ts.timestamp() for ts in hourly_timestamps]

        bar_x = []
        bar_heights = []

        for i in range(len(hourly_timestamps_numeric)):
            start_time = hourly_timestamps_numeric[i]
            end_time = hourly_timestamps_numeric[i] + 3600  # 3600 секунд = 1 година

            bar_x.append((start_time, end_time))
            bar_heights.append(hourly_energy[i])

        self.energy_graph_widget.clear()
        self.energy_graph_widget.setAxisItems({'bottom': DateAxisItem(orientation='bottom')})

        bar_item = pg.BarGraphItem(
            x=[x[0] for x in bar_x],
            height=bar_heights,
            width=1800,
            brush='g'
        )

        self.energy_graph_widget.addItem(bar_item)
        self.energy_graph_widget.setYRange(0, max(hourly_energy))

    def plot_graphs(self, start_date=None, end_date=None):
        query = self.db_session.query(SDM120Report).filter_by(device_id=self.device.id)
        if start_date and end_date:
            query = query.filter(SDM120Report.timestamp >= start_date, SDM120Report.timestamp <= end_date)
        report_data = query.order_by(desc(SDM120Report.timestamp)).all()

        if not report_data:
            QMessageBox.warning(self, "Попередження", "Дані відсутні для заданого періоду.")
            return

        timestamps = []
        voltages = []
        currents = []
        energies = []

        for report in report_data:
            timestamps.append(report.timestamp)
            voltages.append(report.voltage)
            currents.append(report.current)
            energies.append(report.total_active_energy)

        self.plot_voltage(timestamps, voltages)
        self.plot_current(timestamps, currents)

        hourly_energy = []
        hourly_timestamps = []

        last_energy = None
        current_hour_start = None
        current_hour_energy = 0.0

        for report in report_data:
            current_hour = report.timestamp.replace(minute=0, second=0, microsecond=0)

            if current_hour_start is None:
                current_hour_start = current_hour

            if current_hour != current_hour_start:
                if last_energy is not None:
                    hourly_energy.append(current_hour_energy)
                    hourly_timestamps.append(current_hour_start)
                current_hour_start = current_hour
                current_hour_energy = 0.0

            if last_energy is not None:
                current_hour_energy += abs(report.total_active_energy - last_energy.total_active_energy)

            last_energy = report

        if last_energy is not None:
            hourly_energy.append(current_hour_energy)
            hourly_timestamps.append(current_hour_start)

        self.plot_energy(hourly_timestamps, hourly_energy)

    def open_date_range_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Обрати проміжок")
        dialog.setFixedSize(500, 500)

        layout = QVBoxLayout(dialog)

        start_calendar = QCalendarWidget()
        start_calendar.setGridVisible(True)
        layout.addWidget(QLabel("Початкова дата:"))
        layout.addWidget(start_calendar)

        end_calendar = QCalendarWidget()
        end_calendar.setGridVisible(True)
        layout.addWidget(QLabel("Кінцева дата:"))
        layout.addWidget(end_calendar)

        button_layout = QHBoxLayout()
        confirm_button = QPushButton("Підтвердити")
        cancel_button = QPushButton("Скасувати")
        button_layout.addWidget(confirm_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)

        def apply_date_range():
            start_date = start_calendar.selectedDate().startOfDay().toPyDateTime()
            end_date = end_calendar.selectedDate().endOfDay().toPyDateTime()
            self.plot_graphs(start_date=start_date, end_date=end_date)
            dialog.accept()

        confirm_button.clicked.connect(apply_date_range)
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec_()

    def apply_date_range(self, dialog):
        start_date = self.start_calendar.selectedDate().toPyDate()
        end_date = self.end_calendar.selectedDate().toPyDate()
        self.plot_graphs(start_date=start_date, end_date=end_date)
        dialog.accept()

    def set_light_theme(self):
        self.voltage_graph_widget.setBackground('w')
        self.current_graph_widget.setBackground('w')
        self.energy_graph_widget.setBackground('w')

        self.voltage_graph_widget.plot([], pen=pg.mkPen(color='b', width=2))  # Синя лінія для напруги
        self.current_graph_widget.plot([], pen=pg.mkPen(color='r', width=2))  # Червона лінія для струму
        self.energy_graph_widget.plot([], pen=pg.mkPen(color='g', width=2))  # Зелена лінія для енергії

    def open_export_dialog(self):
        self.dialog = QDialog(self)
        self.dialog.setWindowTitle("Експорт в Excel")
        self.dialog.setFixedSize(400, 150)

        layout = QVBoxLayout(self.dialog)

        # Вибір діапазону дат
        date_range_layout = QHBoxLayout()
        start_label = QLabel("Початок:")
        self.start_date = QDateEdit(QDate.currentDate().addYears(-1))
        self.start_date.setCalendarPopup(True)
        end_label = QLabel("Кінець:")
        self.end_date = QDateEdit(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        date_range_layout.addWidget(start_label)
        date_range_layout.addWidget(self.start_date)
        date_range_layout.addWidget(end_label)
        date_range_layout.addWidget(self.end_date)

        layout.addLayout(date_range_layout)

        self.include_charts = QCheckBox("Додати графіки")
        self.include_charts.setChecked(True)
        layout.addWidget(self.include_charts)

        save_button = QPushButton("Зберегти в Excel")
        save_button.clicked.connect(self.export_to_excel)
        layout.addWidget(save_button)

        self.dialog.setLayout(layout)
        self.dialog.exec()

    def export_to_excel(self):
        start_datetime = self.start_date.dateTime().toPyDateTime()
        end_datetime = self.end_date.dateTime().toPyDateTime()

        report_data = self.db_session.query(SDM120Report).filter(
            SDM120Report.device_id == self.device.id,
            SDM120Report.timestamp >= start_datetime,
            SDM120Report.timestamp <= end_datetime
        ).order_by(SDM120Report.timestamp).all()

        if not report_data:
            QMessageBox.warning(self, "Експорт", "Дані за вибраний період відсутні.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Зберегти файл",
            f"{self.device.name}_{start_datetime.date()}_{end_datetime.date()}.xlsx",
            "Excel Files (*.xlsx)")

        if not file_path:
            return

        try:
            workbook = xlsxwriter.Workbook(file_path)

            worksheet = workbook.add_worksheet('Дані')

            worksheet.write('A1', 'Дата/Час')
            worksheet.write('B1', 'Напруга (V)')
            worksheet.write('C1', 'Струм (A)')
            worksheet.write('D1', 'Потужність (W)')

            row = 1
            for entry in report_data:
                timestamp_str = entry.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                worksheet.write(row, 0, timestamp_str)  # Дата/Час
                worksheet.write(row, 1, entry.voltage)  # Напруга
                worksheet.write(row, 2, entry.current)  # Струм
                worksheet.write(row, 3, entry.active_power)    # Потужність

                row += 1

            for col in range(4):
                worksheet.set_column(col, col, 20)

            # Якщо користувач вибрав додавання графіків
            if self.include_charts:
                parameters = ['voltage', 'current', 'active_power']
                for param in parameters:
                    worksheet_param = workbook.add_worksheet(param)

                    worksheet_param.write('A1', 'Дата/Час')
                    worksheet_param.write('B1', param)

                    row = 1
                    for entry in report_data:
                        worksheet_param.write(row, 0, entry.timestamp.strftime('%Y-%m-%d %H:%M:%S'))
                        worksheet_param.write(row, 1, getattr(entry, param.lower()))
                        row += 1

                    worksheet_param.add_table(f'A1:B{row}', {'name': f'{param}_data', 'columns': [{'header': 'Дата/Час'}, {'header': param}]})

                    chart = workbook.add_chart({'type': 'line'})
                    chart.add_series({'values': f'={param}!$B$2:$B${row}', 'name': param, 'categories': f'={param}!$A$2:$A${row-1}'})
                    chart.set_title({'name': param})

                    chart.set_x_axis({'date_axis': True, 'num_format': 'yyyy-mm-dd hh:mm:ss'})

                    worksheet_param.insert_chart('D2', chart)

                    for col in range(4):
                        worksheet.set_column(col, col, 20)

            workbook.close()
            QMessageBox.information(self, "Експорт", "Експорт даних в Excel пройшов успішно.")
            self.dialog.accept()

        except Exception as e:
            QMessageBox.warning(self, "Помилка", f"Сталася помилка при експорті даних: {e}")
