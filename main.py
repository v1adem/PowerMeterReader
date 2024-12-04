import sys
import os
from PyQt5.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Base
from pyqt.MainWindow import MainWindow


def get_database_path():
    """
    Визначає шлях до бази даних у каталозі APPDATA (Windows)
    або відповідному каталозі для Linux/MacOS.
    """
    # Отримуємо каталог APPDATA (Windows) або аналог на інших ОС
    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    app_dir = os.path.join(appdata_dir, 'PowerMeterReader')

    # Створюємо каталог, якщо він не існує
    os.makedirs(app_dir, exist_ok=True)

    # Повертаємо шлях до файлу бази даних
    return os.path.join(app_dir, 'app.db')


def create_database_and_tables(db_path):
    """
    Створює базу даних і таблиці, якщо вони ще не існують.
    """
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
    return engine


if __name__ == "__main__":
    # Отримуємо шлях до бази даних
    db_path = get_database_path()

    # Створюємо базу даних і таблиці
    engine = create_database_and_tables(db_path)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Запускаємо PyQt-додаток
    app = QApplication(sys.argv)
    window = MainWindow(session)
    window.show()
    sys.exit(app.exec_())