from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel


class ReportListWidget(QWidget):
    def __init__(self, device_id="ElNetPQ"):
        super().__init__()

        self.device_id = device_id
        mail_layout = QGridLayout()

        device_id_label = QLabel(device_id)

