import sys

from PyQt5.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import Base
from pyqt.MainWindow import MainWindow


def create_database_and_tables():
    engine = create_engine('sqlite:///app.db')
    Base.metadata.create_all(engine)
    return engine

if __name__ == "__main__":
    engine = create_database_and_tables()
    Session = sessionmaker(bind=engine)
    session = Session()

    app = QApplication(sys.argv)
    window = MainWindow(session)
    window.show()
    sys.exit(app.exec_())

