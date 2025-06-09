# -*- coding: utf-8 -*-
import requests
from PySide6.QtWidgets import QWidget, QMessageBox, QLineEdit
from PySide6.QtCore import Qt
from auth import Ui_Form
from UI.registration_window import RegistrationWindow
from UI.jewerly_store import JewelryStoreApp


class AuthWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        self.setWindowTitle("Авторизация")
        self.setWindowFlag(Qt.WindowCloseButtonHint, True)

        self.ui.pushButton.clicked.connect(self.login)
        self.ui.pushButton_2.clicked.connect(self.show_registration)
        self.ui.lineEdit_2.setEchoMode(QLineEdit.Password)

        self.api_url = "http://127.0.0.1:8000/login"
        self.store_window = None

    def login(self):
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
                # Проверяем role
                if user_data.get("role") == 1:
                    # Если role = 1 (администратор), открываем администраторское окно
                    self.open_admin_window(user_data.get("user_id"))
                elif user_data.get("role") == 2:
                    # Если role_id = 2 (мастер), открываем master_window
                    self.open_master_window(user_data.get("user_id"))
                elif user_data.get("role") == 3:
                    # Если role_id = 3 (кладовщик), открываем warehouse_window
                    self.open_warehouse_window(user_data.get("user_id"))
                else:
                    # Для других ролей открываем обычный магазин
                    self.open_store(user_data.get("user_id"))

            else:
                self.show_error("Ошибка", f"Неверные данные: {response.json().get('detail', '')}")

        except requests.exceptions.ConnectionError:
            self.show_error("Ошибка", "Не удалось подключиться к серверу")
        except Exception as e:
            self.show_error("Ошибка", f"Произошла ошибка: {str(e)}")

    def open_store(self, user_id):
        """Открывает главное окно магазина и закрывает окно авторизации"""
        self.store_window = JewelryStoreApp(user_id)  # Передаем user_id в конструктор
        self.store_window.show()
        self.close()

    def show_registration(self):
        registration_window = RegistrationWindow(self)
        registration_window.exec()

    def show_error(self, title, message):
        QMessageBox.critical(self, title, message)

    def open_master_window(self, user_id):
        """Открывает окно мастера и закрывает окно авторизации"""
        from UI.jeweler_window import JewelryStoreApp  # Импортируем здесь, чтобы избежать циклического импорта
        self.master_window = JewelryStoreApp(user_id)
        self.master_window.show()
        self.close()

    def open_admin_window(self, user_id):
        """Открывает окно администратора и закрывает окно авторизации"""
        from UI.administrator_window import AdminApp  # Импортируем здесь, чтобы избежать циклического импорта
        self.admin_window = AdminApp(user_id)
        self.admin_window.show()
        self.close()

    def open_warehouse_window(self, user_id):
        """Открывает окно кладовщика и закрывает окно авторизации"""
        from UI.warehouse_window import StorekeeperApp  # Импортируем здесь, чтобы избежать циклического импорта
        self.warehouse_window = StorekeeperApp(user_id)
        self.warehouse_window.show()
        self.close()