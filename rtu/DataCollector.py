from datetime import datetime, timedelta

from PyQt5.QtCore import QObject

from models.Admin import Admin
from models.Device import Device
from models.Report import SDM120Report, SDM630Report
from rtu.SerialReaderRS485 import SerialReaderRS485


def get_data_from_device(device, port, properties_list):
    print("reading started")
    client = SerialReaderRS485(device.name, device.model, port, device.device_address, device.baudrate,
                               device.bytesize, device.parity, device.stopbits)
    return client.read_all_properties(properties_list)


class DataCollector(QObject):
    def __init__(self, db_session):
        super().__init__()
        self.db_session = db_session
        self.devices_status = {}  # DeviceName: True/False

    def collect_data(self):
        devices = self.db_session.query(Device).all()
        port = self.db_session.query(Admin).first().port

        for device in devices:
            print(f"Device {device.name} is ok")
            if device.model == "SDM120":
                last_report = (
                    self.db_session.query(SDM120Report)
                    .filter(SDM120Report.device_id == device.id)
                    .order_by(SDM120Report.timestamp.desc())
                    .first()
                )
            elif device.model == "SDM630":
                last_report = (
                    self.db_session.query(SDM630Report)
                    .filter(SDM630Report.device_id == device.id)
                    .order_by(SDM630Report.timestamp.desc())
                    .first()
                )
            else:
                print("Invalid Device Model")
                continue

            if last_report:
                device_reading_interval = device.reading_interval - 10
                if device.reading_type == 2:
                    reading_time = last_report.reading_time
                    start_of_day = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                    if datetime.now() < (
                            start_of_day + timedelta(minutes=reading_time)) or last_report.timestamp >= start_of_day:
                        continue

                if last_report.timestamp + timedelta(seconds=device_reading_interval) > datetime.now():
                    continue

            properties_list = device.get_parameter_names()

            new_data = get_data_from_device(device, port, properties_list)
            self.devices_status[device.name] = True
            report_data = {
                "device_id": device.id,
            }
            report_data.update({key: value for key, value in new_data.items() if value is not None})

            if device.model == "SDM120":
                new_report = SDM120Report(**report_data)
            elif device.model == "SDM630":
                new_report = SDM630Report(**report_data)
            else:
                continue

            self.db_session.add(new_report)
            self.db_session.commit()
