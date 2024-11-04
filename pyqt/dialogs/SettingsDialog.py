from PyQt5.QtWidgets import QDialog, QFormLayout, QLineEdit, QDialogButtonBox


class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")

        layout = QFormLayout()
        layout.addRow("Port:", QLineEdit())
        layout.addRow("Language:", QLineEdit())

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout.addWidget(buttons)
        self.setLayout(layout)