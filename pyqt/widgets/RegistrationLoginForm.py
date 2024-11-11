from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt
from sqlalchemy.exc import IntegrityError
from models.Admin import Admin
import config


class RegistrationLoginForm(QWidget):
    def __init__(self, main_window):
        super().__init__(main_window)

        self.main_window = main_window
        self.db_session = main_window.db_session

        self.setWindowTitle("Реєстрація / Логін")

        # Основний лейаут для центрування форми
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Лейаут для центрування по горизонталі
        center_layout = QHBoxLayout()

        # Лейаут для форми
        form_layout = QVBoxLayout()

        # Повідомлення, яке буде показуватись вгорі
        self.status_label = QLabel(self)
        form_layout.addWidget(self.status_label, alignment=Qt.AlignCenter)

        # Поле для логіну
        self.username_label = QLabel("Логін:", self)
        self.username_input = QLineEdit(self)
        form_layout.addWidget(self.username_label)
        form_layout.addWidget(self.username_input)

        # Поле для паролю
        self.password_label = QLabel("Пароль:", self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addWidget(self.password_label)
        form_layout.addWidget(self.password_input)

        # Кнопки для входу та реєстрації
        self.login_button = QPushButton("Вхід")
        self.login_button.clicked.connect(self.login)
        self.register_button = QPushButton("Реєстрація")
        self.register_button.clicked.connect(self.register)
        self.guest_button = QPushButton("Ввійти як гість")
        self.guest_button.clicked.connect(self.guest_login)

        form_layout.addWidget(self.login_button)
        form_layout.addWidget(self.register_button)
        form_layout.addWidget(self.guest_button)

        # Встановлюємо ширину форми на середню третину екрану
        form_widget = QWidget()
        form_widget.setLayout(form_layout)
        form_widget.setFixedWidth(self.main_window.width() // 3)  # ширина на 1/3 від екрану

        # Додаємо форму до горизонтального лейаута для центрування
        center_layout.addWidget(form_widget)

        # Додаємо центровий лейаут до основного лейауту
        main_layout.addLayout(center_layout)

        # Встановлюємо відстань між елементами
        main_layout.setSpacing(10)

        self.check_if_first_run()

    def check_if_first_run(self):
        """Перевірка на наявність адміністратора в БД при першому запуску програми."""
        admin = self.db_session.query(Admin).first()

        if admin:
            self.show_login_form()
        else:
            self.show_registration_form()

    def show_registration_form(self):
        self.status_label.setText("Будь ласка, зареєструйтеся")
        self.register_button.setVisible(True)
        self.login_button.setVisible(False)
        self.guest_button.setVisible(False)

    def show_login_form(self):
        self.status_label.setText("Введіть логін та пароль")
        self.register_button.setVisible(False)
        self.login_button.setVisible(True)
        self.guest_button.setVisible(True)

    def register(self):
        username = self.username_input.text()
        password = self.password_input.text()

        admin = Admin(username=username, password=password)
        self.db_session.add(admin)
        try:
            self.db_session.commit()
            self.status_label.setText("Реєстрація успішна!")
            self.show_login_form()
        except IntegrityError:
            self.db_session.rollback()
            self.status_label.setText("Цей користувач вже існує!")

    def login(self):
        username = self.username_input.text()
        password = self.password_input.text()

        admin = self.db_session.query(Admin).filter_by(username=username, password=password).first()
        if admin:
            self.main_window.isAdmin = True
            self.status_label.setText(f"Вітаємо, {username}!")
            self.main_window.open_projects_list()
        else:
            self.status_label.setText("Невірний логін або пароль")

    def guest_login(self):
        self.main_window.isAdmin = False
        self.status_label.setText("Вхід як гість успішний")
        self.main_window.open_projects_list()
