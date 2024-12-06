import asyncio
import os
import sys

from PyQt5.QtWidgets import QApplication
from qasync import QEventLoop
from sqlalchemy.ext.asyncio import create_async_engine

from config import Base
from pyqt.MainWindow import MainWindow


def get_database_path():
    """
    Визначає шлях до бази даних у каталозі APPDATA (Windows)
    або відповідному каталозі для Linux/MacOS.
    """
    appdata_dir = os.getenv('APPDATA') if sys.platform == 'win32' else os.path.expanduser('~/.config')
    app_dir = os.path.join(appdata_dir, 'EON')
    os.makedirs(app_dir, exist_ok=True)
    return os.path.join(app_dir, 'app.db')


async def create_database_and_tables(db_path):
    """
    Створює базу даних і таблиці, якщо вони ще не існують.
    """
    engine = create_async_engine(f'sqlite+aiosqlite:///{db_path}', echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine


async def main():
    db_path = get_database_path()

    engine = await create_database_and_tables(db_path)
    app = QApplication(sys.argv)

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow(engine)
    window.show()

    loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
