from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class SettingsWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Налаштування"))
        self.setLayout(layout)