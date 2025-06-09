# -*- coding: utf-8 -*-
import requests
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QMessageBox, QDialog
from UI.registration import Ui_Dialog
from UI.reg_completed import RegCompletedDialog


class RegistrationWindow(QDialog):
    registration_completed = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dialog()
        self.ui.setupUi(self)

        self.setWindowTitle("Регистрация")
        self.ui.pushButton.clicked.connect(self.register_user)
        self.api_url = "http://127.0.0.1:8000/create/users"
        self.user_id = None  # Будет установлен после успешной регистрации

    def register_user(self):
        username = self.ui.lineEdit.text()
        password = self.ui.lineEdit_2.text()

        if not username or not password:
            self.show_error("Ошибка", "Все поля должны быть заполнены")
            return

        try:
            response = requests.post(
                self.api_url,
                json={"username": username, "password": password},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data.get('user_id')
                self.registration_completed.emit(self.user_id)  # Отправляем сигнал
                self.show_success()
            else:
                error_msg = response.json().get('detail', 'Неизвестная ошибка')
                self.show_error("Ошибка", f"Ошибка регистрации: {error_msg}")

        except requests.exceptions.ConnectionError:
            self.show_error("Ошибка", "Не удалось подключиться к серверу")
        except Exception as e:
            self.show_error("Ошибка", f"Произошла ошибка: {str(e)}")

    def show_success(self):
        """Показывает окно успешной регистрации и закрывает текущее"""
        self.close()
        completed_dialog = RegCompletedDialog(self.parent())
        if completed_dialog.exec() == QDialog.Accepted:
            # Если пользователь нажал "Перейти в магазин"
            if self.parent() and hasattr(self.parent(), 'open_store'):
                # Передаем user_id в родительское окно для открытия магазина
                self.parent().open_store(self.user_id)

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)