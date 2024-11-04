import csv
import os
import sys

from PyQt5.QtWidgets import QLabel, QTableWidget, QListWidget, QGridLayout, QWidget, QTextEdit, QTableWidgetItem, \
    QHBoxLayout, QPushButton

from DeviceManager import DeviceManager


class Logger:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, message):
        self.text_widget.append(message)

    def flush(self):
        pass


class StatisticsWidget(QWidget):
    def __init__(self, device_id=None):
        super().__init__()

        self.device_id = device_id
        main_layout = QGridLayout()

        self.device_params_label = QLabel("Device Details")
        self.param_table = QTableWidget(0, 3)
        self.param_table.setColumnWidth(0, 201)
        self.param_table.setColumnWidth(1, 80)
        self.param_table.setColumnWidth(2, 80)
        self.param_table.setHorizontalHeaderLabels(['Parameter', 'Value', 'Units'])
        self.param_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.param_table.setFixedHeight(535)

        device_list_label = QLabel("Device list")
        device_list_layout = QHBoxLayout()
        device_list_layout.addWidget(device_list_label)

        self.browse_devices_button = QPushButton("Browse")
        self.browse_devices_button.clicked.connect(self.browse_devices)
        device_list_layout.addWidget(self.browse_devices_button)

        self.device_list_widget = QListWidget()
        self.populate_device_list()

        report_label = QLabel("Reports")
        report_list_layout = QHBoxLayout()
        report_list_layout.addWidget(report_label)

        self.reports_settings_button = QPushButton("Settings")
        self.reports_settings_button.clicked.connect(self.reports_settings)
        report_list_layout.addWidget(self.reports_settings_button)

        self.report_list_widget = QListWidget()
        self.report_list_widget.setFixedHeight(150)

        log_label = QLabel("Log")
        self.log_text_edit = QTextEdit()
        self.log_text_edit.setFixedHeight(155)
        self.log_text_edit.setReadOnly(True)

        main_layout.addWidget(self.device_params_label, 0, 0)
        main_layout.addWidget(self.param_table, 1, 0)
        main_layout.addLayout(device_list_layout, 0, 1)
        main_layout.addWidget(self.device_list_widget, 1, 1)
        main_layout.addLayout(report_list_layout, 2, 1)
        main_layout.addWidget(self.report_list_widget, 3, 1)
        main_layout.addWidget(log_label, 4, 1)
        main_layout.addWidget(self.log_text_edit, 5, 1)

        self.setLayout(main_layout)

        if device_id is not None:
            self.load_parameters_from_csv()

        logger = Logger(self.log_text_edit)
        sys.stdout = logger

        print("Log started")

    def populate_device_list(self):
        device_manager = DeviceManager()
        device_manager.fetch_devices()
        for custom_name in device_manager.devices.keys():
            self.device_list_widget.addItem(custom_name)

    def browse_devices(self):
        # This method will handle what happens when the Browse button is clicked.
        print("Browse button clicked. Here you can implement the logic to navigate to another widget.")

    def reports_settings(self):
        # This method will handle what happens when the Browse button is clicked.
        print("Browse button clicked. Here you can implement the logic to navigate to another widget.")


    def load_parameters_from_csv(self):
        # Define the path to the reports directory
        reports_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'reports')

        # Find all CSV files for the given device_id
        csv_files = [f for f in os.listdir(reports_dir) if f.startswith(f"{self.device_id}_") and f.endswith(".csv")]

        # Populate the report_list with all relevant report files
        self.report_list_widget.clear()  # Clear the existing items in the report list
        if not csv_files:
            print("No CSV files found for the device.")
            return

        for file in csv_files:
            self.report_list_widget.addItem(file)

        # Get the most recent file based on the modification time
        latest_file = max(
            (os.path.join(reports_dir, f) for f in csv_files),
            key=os.path.getmtime
        )

        # Read CSV file and populate the table
        try:
            with open(latest_file, mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'device_id' in row:
                        del row['device_id']  # Remove device_id
                    self.param_table.insertRow(self.param_table.rowCount())
                    for col, key in enumerate(row.keys()):
                        self.param_table.setItem(self.param_table.rowCount() - 1, col,
                                                 QTableWidgetItem(str(row[key])))
            # Update the device parameters label with the latest file's name
            self.device_params_label.setText(
                f"Device Details - {self.device_id} (Latest: {os.path.basename(latest_file)})")

        except FileNotFoundError:
            print(f"File not found: {latest_file}")
        except Exception as e:
            print(f"Error reading file: {e}")
