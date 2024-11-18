request_button = QPushButton("Моніторинг")
request_button.setFixedSize(120, 36)
request_button.clicked.connect(self.show_current_data_dialog)
top_layout.addWidget(request_button)

def show_current_data_dialog(self):
    # Функція для отримання та оновлення даних
    def update_data():
        data = get_data_from_device(self.device, self.db_session.query(Admin).first().port,
                                    self.device.get_parameter_names())

        # Оновлення значень у таблиці без очищення моделі
        for row, (key, value) in enumerate(data.items()):
            model.setItem(row, 1, QStandardItem(str(value) if value is not None else ""))
            unit = parameter_units.get(key, "")
            model.setItem(row, 2, QStandardItem(unit))

        # Оновлення ширини колонок (можна прибрати, якщо не потрібно)
        data_table.resizeColumnsToContents()

    # Створення діалогового вікна
    parameter_units = {}
    if self.device.parameters:
        for param in self.device.parameters.split(','):
            param_name, unit = param.split(':')
            parameter_units[param_name.strip()] = unit.strip()

    dialog = QDialog(self)
    dialog.setWindowTitle("Поточні дані")
    dialog_layout = QVBoxLayout(dialog)

    data_table = QTableView(dialog)
    parameter_names = self.device.get_parameter_names()  # Отримуємо назви параметрів

    # Створення моделі з початковим розміром, відповідним до кількості параметрів
    model = QStandardItemModel(len(parameter_names), 3)
    model.setHorizontalHeaderLabels(["Параметр", "Значення", "Од. вим"])

    # Заповнення імен параметрів і одиниць вимірювання
    for row, key in enumerate(parameter_names):
        model.setItem(row, 0, QStandardItem(key))
        model.setItem(row, 1, QStandardItem(""))
        model.setItem(row, 2, QStandardItem(parameter_units.get(key, "")))

    data_table.setModel(model)
    header = data_table.horizontalHeader()
    header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
    dialog_layout.addWidget(data_table)

    # Налаштування таймера для періодичного оновлення
    timer = QTimer(dialog)
    timer.timeout.connect(update_data)
    timer.start(1000)  # Оновлення кожну секунду

    # Перший виклик оновлення даних
    update_data()

    # Зупинка таймера при закритті діалогу
    dialog.finished.connect(timer.stop)

    dialog.exec()

