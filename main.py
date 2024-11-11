import multiprocessing
import sys
from datetime import datetime, timedelta

from PyQt5.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Base
from models.Admin import Admin
from models.Device import Device
from models.Report import SDM120Report, SDM630Report
from pyqt.MainWindow import MainWindow


def create_database_and_tables():
    engine = create_engine('sqlite:///app.db')
    Base.metadata.create_all(engine)
    return engine


def start_gui_application(db_session):
    """Функція для запуску PyQt GUI."""
    app = QApplication(sys.argv)
    window = MainWindow(db_session)
    window.show()
    sys.exit(app.exec_())


CHECK_INTERVAL = 60


def background_update_process():
    while True:
        devices = session.query(Device).all()

        for device in devices:

            if device.model == "SDM120":
                last_report = (
                    session.query(SDM120Report)
                    .filter(SDM120Report.device_id == device.id)
                    .order_by(SDM120Report.timestamp.desc())
                    .first()
                )
            if device.model == "SDM630":
                last_report = (
                    session.query(SDM630Report)
                    .filter(SDM630Report.device_id == device.id)
                    .order_by(SDM630Report.timestamp.desc())
                    .first()
                )
            if last_report.timestamp + CHECK_INTERVAL > datetime.now():
                continue

            if device.reading_type == 1:
                if last_report:
                    time_since_last_report = datetime.now() - last_report.timestamp
                else:
                    time_since_last_report = timedelta(minutes=999)

                if time_since_last_report >= timedelta(seconds=CHECK_INTERVAL):
                    next_read_time = last_report.timestamp + timedelta(minutes=device.reading_interval)

                    if datetime.now() >= next_read_time:
                        print(f"Оновлення даних для пристрою {device.name}...")

                        new_data = {}  # get_data(device)

                        new_report = SDM120Report(
                            device_id=device.id,
                            timestamp=datetime.now(),
                        )
                        session.add(new_report)

                        session.commit()

                        print(f"Дані для пристрою {device.name} успішно оновлено.")
                    else:
                        print(f"Пристрій {device.name} ще не потребує оновлення.")
                else:
                    print(
                        f"Останнє оновлення для пристрою {device.name} відбулося менше ніж {CHECK_INTERVAL} секунд тому.")
            if device.reading_type == 2:
                pass  # Місце де потрібно реалізувати алгоритм
            else:
                print("Invalid reading type")


def test_admin_record(session):
    # Додаємо тестовий запис
    new_admin = Admin(username="admin_test", password="password123")
    session.add(new_admin)
    session.commit()
    print("Тестовий запис додано в таблицю Admin.")

    # Зчитуємо запис з таблиці Admin і виводимо в консоль
    admin_record = session.query(Admin).first()
    print("Прочитаний запис з таблиці Admin:", admin_record.username, admin_record.password)


if __name__ == "__main__":
    engine = create_database_and_tables()
    Session = sessionmaker(bind=engine)
    session = Session()

    # test_admin_record(session)
    gui_process = multiprocessing.Process(target=start_gui_application(session))
    gui_process.start()

    # background_process = multiprocessing.Process(target=background_update_process)
    # background_process.start()

    gui_process.join()
    # background_process.join()
