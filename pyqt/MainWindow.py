import asyncio

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, \
    QStackedWidget, QAction, QDialog, QMessageBox
from qasync import asyncSlot

from queue import Queue
from threading import Thread, Lock

from sqlalchemy.ext.asyncio import async_sessionmaker

from models.Admin import Admin
from models.Project import Project
from pyqt.dialogs.ConnectionDialog import ConnectionDialog
from pyqt.dialogs.LanguageDialog import LanguageDialog
from pyqt.widgets.DeviceDetailsSDM120Widget import DeviceDetailsSDM120Widget
from pyqt.widgets.ProjectViewWidget import ProjectViewWidget
from pyqt.widgets.ProjectsWidget import ProjectsWidget
from pyqt.widgets.RegistrationLoginForm import RegistrationLoginForm
from rtu.DataCollector import DataCollector


from sqlalchemy.future import select


class MainWindow(QMainWindow):
    status_update_signal = pyqtSignal(Project)

    def __init__(self, engine):
        super().__init__()

        self.db_session = async_sessionmaker(bind=engine, expire_on_commit=False)
        self.port_queues = {}  # Черги для портів
        self.port_locks = {}  # Блокування для портів
        self.port_threads = {}  # Потоки для обробки черг
        self.data_collectors = []

        self.isAdmin = False

        self.setWindowTitle("EON EMS (SDM120 edition)")
        self.setGeometry(100, 100, 1200, 800)
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        self.menu_bar = self.menuBar()
        self.menu_bar.setStyleSheet("font-size: 18px;")

        back_action = QAction("Назад", self)
        self.menu_bar.addAction(back_action)
        back_action.triggered.connect(self.go_back)

        settings_menu = self.menu_bar.addMenu("Налаштування")
        language_action = QAction("Мова", self)
        settings_menu.addAction(language_action)
        language_action.triggered.connect(self.change_language)

        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        self.stacked_widget = QStackedWidget(self.central_widget)
        self.central_layout = QVBoxLayout(self.central_widget)
        self.central_layout.addWidget(self.stacked_widget)

        self.registration_widget = RegistrationLoginForm(self)
        self.stacked_widget.addWidget(self.registration_widget)

        self.stacked_widget.setCurrentIndex(0)

        # Ініціалізація черг портів
        asyncio.ensure_future(self.initialize_port_queues())

        # Ініціалізація адміністратора
        asyncio.ensure_future(self.initialize_admin())

        # Викликаємо метод асинхронно
        QTimer.singleShot(0, self.start_data_collectors)

    async def initialize_admin(self):
        # асинхронний запит до БД для отримання адміністратора
        async with self.db_session() as session:
            result = await session.execute(select(Admin))
            admin = result.scalars().first()

        if admin is not None and admin.always_admin:
            self.isAdmin = True
            await self.open_projects_list()

    async def open_projects_list(self):
        # асинхронний запит для отримання проектів
        async with self.db_session() as session:
            result = await session.execute(select(Project))
            projects = result.scalars().all()

        # подальше використання отриманих проектів
        projects_widget = ProjectsWidget(self, self.status_update_signal)
        self.stacked_widget.addWidget(projects_widget)
        self.stacked_widget.setCurrentIndex(1)

    async def initialize_port_queues(self):
        # асинхронний запит для отримання проектів
        async with self.db_session() as session:
            result = await session.execute(select(Project))
            projects = result.scalars().all()

        for project in projects:
            port = project.port
            if port not in self.port_queues:
                self.port_queues[port] = Queue()
                self.port_locks[port] = Lock()
                thread = Thread(target=self.process_port_queue, args=(port,))
                thread.daemon = True
                thread.start()
                self.port_threads[port] = thread

    def process_port_queue(self, port):
        while True:
            task = self.port_queues[port].get()
            if task is None:
                break
            try:
                with self.port_locks[port]:
                    task['callback'](task['device'], task['properties_list'])
            except Exception as e:
                print(f"Error processing task for port {port}: {e}")
            finally:
                self.port_queues[port].task_done()

    @asyncSlot()
    async def start_data_collectors(self):
        await self.initialize_port_queues()

        async with self.db_session() as session:
            result = await session.execute(select(Project))
            projects = result.scalars().all()

        for project in projects:
            port = project.port

            if port not in self.port_queues:
                print(f"Port {port} not found in port_queues. Skipping project {project.name}.")
                QMessageBox.warning(self, "Помилка", f"Порт {port} не знайдено. Пропущено проект {project.name}.")
                continue

            port_queue = self.port_queues[port]

            data_collector = DataCollector(self.db_session, project, port_queue, self.status_update_signal)
            self.data_collectors.append(data_collector)

        await self.start_timers()

    async def start_timers(self):
        while True:
            tasks = [data_collector.collect_data() for data_collector in self.data_collectors]
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)

    def closeEvent(self, event):
        for port, queue in self.port_queues.items():
            queue.put(None)
        event.accept()

    def change_language(self):
        language_dialog = LanguageDialog(self)
        if language_dialog.exec_() == QDialog.Accepted:
            current_language = language_dialog.selected_language
            print(f"Мова змінена на: {current_language}")

    def open_connection_dialog(self):
        dialog = ConnectionDialog(self)
        dialog.exec_()

    def open_projects_list(self):
        projects_widget = ProjectsWidget(self, self.status_update_signal)
        self.stacked_widget.addWidget(projects_widget)
        self.stacked_widget.setCurrentIndex(1)

    def open_project_details(self, project):
        project_view_widget = ProjectViewWidget(self, project)
        self.stacked_widget.addWidget(project_view_widget)
        self.stacked_widget.setCurrentIndex(2)

    def open_device_details(self, device):
        if device.model == "SDM120":
            device_details_widget = DeviceDetailsSDM120Widget(self, device)
            self.stacked_widget.addWidget(device_details_widget)
            self.stacked_widget.setCurrentIndex(3)
        elif device.model == "SDM630":
            pass


    def go_back(self):
        current_index = self.stacked_widget.currentIndex()

        if current_index > 0:
            current_widget = self.stacked_widget.currentWidget()
            self.stacked_widget.removeWidget(current_widget)

            self.stacked_widget.setCurrentIndex(current_index - 1)

        if current_index == 1:
            self.isAdmin = False

            self.stacked_widget.removeWidget(self.registration_widget)

            self.registration_widget = RegistrationLoginForm(self)
            self.stacked_widget.addWidget(self.registration_widget)

            self.stacked_widget.setCurrentIndex(0)