from datetime import datetime

from PyQt5.QtCore import QObject
from sqlalchemy import select

from models.Device import Device
from models.Report import SDM120Report, SDM630Report, SDM120ReportTmp
from rtu.SerialReaderRS485 import SerialReaderRS485


async def get_data_from_device(device, project, properties_list, db_session):
    client = SerialReaderRS485(db_session, device.name, device.model, project.port, device.device_address,
                               project.baudrate,
                               project.bytesize, project.parity, project.stopbits)
    return await client.read_all_properties(properties_list, device)


class DataCollector(QObject):
    def __init__(self, db_session, project, port_queue, status_update_signal):
        super().__init__()
        self.db_session = db_session
        self.project = project
        self.port_queue = port_queue
        self.status_update_signal = status_update_signal  # Сигнал для оновлення статусу порту

    async def collect_data(self):
        async with self.db_session() as session:
            result = await session.execute(
                select(Device).filter(Device.project_id == self.project.id)
            )
            devices = result.scalars().all()

            for device in devices:
                if device.reading_status:
                    self.port_queue.put({
                        'device': device,
                        'properties_list': device.get_parameter_names(),
                        'callback': self.process_device
                    })

    async def process_device(self, device, properties_list):
        try:
            print(f"{datetime.now().strftime('%d/%m/%Y, %H:%M:%S')} - {device.name} is reading")
            new_data = await get_data_from_device(db_session=self.db_session, project=self.project,
                                                  properties_list=properties_list, device=device)

            if new_data:
                await self.create_tmp_report(device, new_data)
                await self.create_full_report(device, new_data)
                await self.update_project_connection_status(device.project, True)

        except Exception as e:
            print(f"Error processing device {device.name}: {e}")
            await self.update_project_connection_status(device.project, False)

    async def create_tmp_report(self, device, new_data):
        tmp_report_data = {
            "device_id": device.id,
            "voltage": new_data.get("voltage"),
            "current": new_data.get("current"),
            "active_power": new_data.get("active_power"),
            "total_active_energy": new_data.get("total_active_energy"),
        }

        tmp_report = SDM120ReportTmp(**tmp_report_data)

        async with self.db_session() as session:
            session.add(tmp_report)
            await session.commit()

    async def create_full_report(self, device, new_data):
        report_data = {
            "device_id": device.id,
        }
        report_data.update({key: value for key, value in new_data.items() if value is not None})

        if device.model == "SDM120":
            new_report = SDM120Report(**report_data)
        elif device.model == "SDM630":
            new_report = SDM630Report(**report_data)
        else:
            return

        async with self.db_session() as session:
            session.add(new_report)
            await session.commit()

    async def update_project_connection_status(self, project, is_connected):
        """Оновлюємо статус порту проєкту лише якщо він змінився"""
        async with self.db_session() as session:
            db_project = await session.get(type(project), project.id)
            if db_project.is_connected != is_connected:
                db_project.is_connected = is_connected
                await session.commit()
                # Викликаємо сигнал для оновлення UI, передаючи проект
                print(f"Статус порту для проєкту {project.name} змінився!!!")
                self.status_update_signal.emit(db_project)
            else:
                print(f"Статус порту для проєкту {project.name} не змінився.")
