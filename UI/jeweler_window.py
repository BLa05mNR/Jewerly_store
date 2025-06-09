import os
import sys
from datetime import datetime

import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame,
                               QScrollArea, QStackedWidget, QSizePolicy, QDialog,
                               QGridLayout, QMessageBox, QLineEdit, QLayout, QTextEdit, QFormLayout, QComboBox,
                               QDialogButtonBox)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage, QDoubleValidator, QIntValidator, QAction


class ApiThread(QThread):
    products_loaded = Signal(list)
    image_loaded = Signal(int, QPixmap)
    orders_loaded = Signal(list)
    individual_orders_loaded = Signal(list)
    order_updated = Signal(bool, str)
    product_updated = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_url = "http://127.0.0.1:8000"

    def fetch_products(self):
        try:
            response = requests.get(f"{self.base_url}/products/get/all/")
            if response.status_code == 200:
                self.products_loaded.emit(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching products: {e}")

    def fetch_image(self, image_id):
        try:
            response = requests.get(f"{self.base_url}/images/{image_id}")
            if response.status_code == 200:
                image = QImage()
                image.loadFromData(response.content)
                pixmap = QPixmap.fromImage(image)
                self.image_loaded.emit(image_id, pixmap)
        except requests.exceptions.RequestException as e:
            print(f"Error fetching image {image_id}: {e}")

    def fetch_orders(self):
        try:
            response = requests.get(f"{self.base_url}/orders/get/all/")
            if response.status_code == 200:
                self.orders_loaded.emit(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching orders: {e}")

    def fetch_individual_orders(self):
        try:
            response = requests.get(f"{self.base_url}/individual-orders/get/all/")
            if response.status_code == 200:
                self.individual_orders_loaded.emit(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Error fetching individual orders: {e}")

    def update_order_status(self, order_id, new_status):
        try:
            response = requests.patch(
                f"{self.base_url}/orders/{order_id}/status",  # Changed endpoint
                json={"status": new_status}
            )
            if response.status_code == 200:
                self.order_updated.emit(True, "Статус заказа успешно обновлен")
            else:
                self.order_updated.emit(False, f"Ошибка обновления статуса: {response.text}")
        except requests.exceptions.RequestException as e:
            self.order_updated.emit(False, f"Ошибка соединения: {str(e)}")

    def update_individual_order_status(self, order_id, new_status):
        try:
            response = requests.patch(
                f"{self.base_url}/individual-orders/update-status/{order_id}",
                json={"status": new_status}
            )
            if response.status_code == 200:
                self.order_updated.emit(True, "Статус индивидуального заказа успешно обновлен")
            else:
                self.order_updated.emit(False, f"Ошибка обновления статуса: {response.text}")
        except requests.exceptions.RequestException as e:
            self.order_updated.emit(False, f"Ошибка соединения: {str(e)}")

    def update_product(self, product_id, update_data):
        try:
            response = requests.patch(
                f"{self.base_url}/products/update/{product_id}",
                json=update_data
            )
            if response.status_code == 200:
                self.product_updated.emit(True, "Товар успешно обновлен")
            else:
                self.product_updated.emit(False, f"Ошибка обновления товара: {response.text}")
        except requests.exceptions.RequestException as e:
            self.product_updated.emit(False, f"Ошибка соединения: {str(e)}")

class OrderDetailDialog(QDialog):
    def __init__(self, order_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Детали заказа #{order_details.get('order_id', '')}")
        self.setMinimumSize(800, 600)
        self.order_details = order_details

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Основная информация о заказе
        order_info = QLabel(f"Заказ #{order_details.get('order_id', 'N/A')}")
        order_info.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        order_info.setStyleSheet("color: #d4af37;")
        layout.addWidget(order_info)

        # Статус и дата
        status_date_layout = QHBoxLayout()

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Новый", "В обработке", "Оплачен", "Доставка", "Завершен", "Отменен"])
        current_status = order_details.get('status', 'Новый')
        self.status_combo.setCurrentText(current_status)

        date_label = QLabel(self.format_date(order_details.get('order_date', '')))
        date_label.setFont(QFont('Montserrat', 14))

        status_date_layout.addWidget(QLabel("Статус:"))
        status_date_layout.addWidget(self.status_combo)
        status_date_layout.addStretch()
        status_date_layout.addWidget(date_label)
        layout.addLayout(status_date_layout)

        # Информация о клиенте
        client_label = QLabel(f"Клиент ID: {order_details.get('client_id', 'N/A')}")
        client_label.setFont(QFont('Montserrat', 14))
        layout.addWidget(client_label)

        # Состав заказа
        items_label = QLabel("Состав заказа:")
        items_label.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        items_label.setStyleSheet("color: #d4af37;")
        layout.addWidget(items_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        items_container = QWidget()
        items_layout = QVBoxLayout(items_container)
        items_layout.setContentsMargins(0, 0, 0, 0)
        items_layout.setSpacing(10)

        for item in order_details.get('items', []):
            product_info = item.get('product_info', {})
            item_frame = self.create_item_frame(item, product_info)
            items_layout.addWidget(item_frame)

        items_layout.addStretch()
        scroll.setWidget(items_container)
        layout.addWidget(scroll)

        # Общая сумма
        total_label = QLabel(f"Общая сумма: {order_details.get('total_amount', 0):,} ₽".replace(",", " "))
        total_label.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #d4af37;")
        layout.addWidget(total_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Кнопка обновления статуса
        update_btn = QPushButton("Обновить статус")
        update_btn.setObjectName("updateButton")
        update_btn.clicked.connect(self.update_status)
        layout.addWidget(update_btn)

        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog { background-color: #1a1a1a; }
            QLabel { color: white; }
            QComboBox {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #444;
                border-radius: 4px;
            }
            #updateButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #updateButton:hover { background-color: #f0d87c; }
            .itemFrame {
                border: 1px solid #444;
                border-radius: 8px;
                padding: 10px;
            }
        """)

    def format_date(self, date_str):
        if not date_str:
            return "Дата неизвестна"
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime("%d.%m.%Y %H:%M")
        except ValueError:
            return date_str

    def create_item_frame(self, item, product_info):
        frame = QFrame()
        frame.setObjectName("itemFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(10, 10, 10, 10)

        # Левая часть - основная информация
        left_layout = QVBoxLayout()
        left_layout.setSpacing(5)

        # Используем данные из item или product_info
        name = item.get('product_name', product_info.get('name', 'Неизвестный товар'))
        article = item.get('article', product_info.get('article', 'N/A'))

        name_label = QLabel(name)
        name_label.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))

        article_label = QLabel(f"Артикул: {article}")
        article_label.setFont(QFont('Montserrat', 12))
        article_label.setStyleSheet("color: #aaaaaa;")

        left_layout.addWidget(name_label)
        left_layout.addWidget(article_label)
        left_layout.addStretch()

        # Правая часть - цена и количество
        right_layout = QVBoxLayout()
        right_layout.setAlignment(Qt.AlignmentFlag.AlignRight)

        quantity = QLabel(f"{item.get('quantity', 1)} шт × {item.get('price', 0):,} ₽".replace(",", " "))
        quantity.setFont(QFont('Montserrat', 14))

        total = QLabel(f"= {item.get('quantity', 1) * item.get('price', 0):,} ₽".replace(",", " "))
        total.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
        total.setStyleSheet("color: #d4af37;")

        right_layout.addWidget(quantity)
        right_layout.addWidget(total)
        right_layout.addStretch()

        layout.addLayout(left_layout, stretch=2)
        layout.addLayout(right_layout, stretch=1)

        return frame

    def update_status(self):
        new_status = self.status_combo.currentText()
        self.parent().api_thread.update_order_status(
            self.order_details['order_id'],
            new_status
        )
        self.accept()


class IndividualOrderDetailDialog(QDialog):
    def __init__(self, order_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Индивидуальный заказ #{order_details.get('order_id', '')}")
        self.setMinimumSize(800, 600)
        self.order_details = order_details

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Order info
        order_info = QLabel(f"Индивидуальный заказ #{order_details.get('order_id', 'N/A')}")
        order_info.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        order_info.setStyleSheet("color: #d4af37;")
        layout.addWidget(order_info)

        # Status and date
        status_date_layout = QHBoxLayout()

        self.status_combo = QComboBox()
        self.status_combo.addItems(
            ["Новый", "В обработке", "Дизайн", "Изготовление", "Готов", "Доставка", "Завершен", "Отменен"])
        current_status = order_details.get('status', 'Новый')
        self.status_combo.setCurrentText(current_status)

        order_date = order_details.get('order_date', '')
        if order_date:
            try:
                dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                date_text = f"Дата: {formatted_date}"
            except ValueError:
                date_text = f"Дата: {order_date}"
        else:
            date_text = "Дата неизвестна"

        date = QLabel(date_text)
        date.setFont(QFont('Montserrat', 14))

        status_date_layout.addWidget(QLabel("Статус:"))
        status_date_layout.addWidget(self.status_combo)
        status_date_layout.addStretch()
        status_date_layout.addWidget(date)
        layout.addLayout(status_date_layout)

        # Client info
        client_info = QLabel(f"Клиент: ID {order_details.get('client_id', 'N/A')}")
        client_info.setFont(QFont('Montserrat', 14))
        layout.addWidget(client_info)

        # Contact info
        contact_info = QLabel(f"Телефон: {order_details.get('contact_phone', 'Не указан')}")
        contact_info.setFont(QFont('Montserrat', 14))
        layout.addWidget(contact_info)

        # Delivery address
        address_info = QLabel(f"Адрес доставки: {order_details.get('delivery_address', 'Не указан')}")
        address_info.setFont(QFont('Montserrat', 14))
        address_info.setWordWrap(True)
        layout.addWidget(address_info)

        # Description
        desc_label = QLabel("Описание заказа:")
        desc_label.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        desc_label.setStyleSheet("color: #d4af37;")
        layout.addWidget(desc_label)

        description = QTextEdit()
        description.setPlainText(order_details.get('description', 'Нет описания'))
        description.setReadOnly(True)
        description.setFont(QFont('Montserrat', 12))
        description.setStyleSheet("""
            QTextEdit {
                background-color: #252525;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        layout.addWidget(description)

        # Total amount
        total_amount = order_details.get('total_amount', 0)
        total_label = QLabel(f"Сумма: {total_amount:,} ₽".replace(",", " "))
        total_label.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #d4af37;")
        layout.addWidget(total_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Update button
        update_btn = QPushButton("Обновить статус")
        update_btn.setObjectName("updateButton")
        update_btn.clicked.connect(self.update_status)
        layout.addWidget(update_btn)

        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
            }
            QComboBox {
                background-color: #333;
                color: white;
                padding: 5px;
                border: 1px solid #444;
                border-radius: 4px;
            }
            #updateButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #updateButton:hover {
                background-color: #f0d87c;
            }
        """)

    def update_status(self):
        new_status = self.status_combo.currentText()
        self.parent().api_thread.update_individual_order_status(
            self.order_details['order_id'],
            new_status
        )
        self.accept()


class EditProductDialog(QDialog):
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Редактирование товара")
        self.setMinimumSize(500, 700)
        self.product_data = product_data

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Форма для редактирования
        form = QFormLayout()
        form.setVerticalSpacing(15)

        # Поля для редактирования
        self.name_edit = QLineEdit(product_data.get('name', ''))
        self.article_edit = QLineEdit(product_data.get('article', ''))
        self.type_edit = QLineEdit(product_data.get('type', ''))
        self.material_edit = QLineEdit(product_data.get('material', ''))
        self.insert_type_edit = QLineEdit(product_data.get('insert_type', ''))

        # Числовые поля с валидацией
        self.weight_edit = QLineEdit(str(product_data.get('weight', 0)))
        self.weight_edit.setValidator(QDoubleValidator(0, 9999, 2))

        self.price_edit = QLineEdit(str(product_data.get('price', 0)))
        self.price_edit.setValidator(QIntValidator(0, 9999999))

        self.stock_quantity_edit = QLineEdit(str(product_data.get('stock_quantity', 0)))
        self.stock_quantity_edit.setValidator(QIntValidator(0, 9999))

        self.image_id_edit = QLineEdit(str(product_data.get('image_id', 0)))
        self.image_id_edit.setValidator(QIntValidator(0, 9999))

        # Добавляем поля в форму
        form.addRow("Название:", self.name_edit)
        form.addRow("Артикул:", self.article_edit)
        form.addRow("Тип:", self.type_edit)
        form.addRow("Материал:", self.material_edit)
        form.addRow("Вставка:", self.insert_type_edit)
        form.addRow("Вес (г):", self.weight_edit)
        form.addRow("Цена (₽):", self.price_edit)
        form.addRow("Количество:", self.stock_quantity_edit)
        form.addRow("ID изображения:", self.image_id_edit)

        layout.addLayout(form)

        # Кнопки
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Сохранить")
        save_btn.setObjectName("saveButton")
        save_btn.clicked.connect(self.save_product)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
            }
            QLineEdit {
                background-color: #333;
                color: white;
                padding: 8px;
                border: 1px solid #444;
                border-radius: 4px;
            }
            #saveButton {
                background-color: #d4af37;
                color: black;
                padding: 10px;
                border-radius: 5px;
            }
            #saveButton:hover {
                background-color: #f0d87c;
            }
            #cancelButton {
                background-color: #333;
                color: white;
                padding: 10px;
                border-radius: 5px;
            }
            #cancelButton:hover {
                background-color: #444;
            }
        """)

    def save_product(self):
        update_data = {
            "name": self.name_edit.text(),
            "article": self.article_edit.text(),
            "type": self.type_edit.text(),
            "material": self.material_edit.text(),
            "insert_type": self.insert_type_edit.text(),
            "weight": float(self.weight_edit.text()),
            "price": int(self.price_edit.text()),
            "stock_quantity": int(self.stock_quantity_edit.text()),
            "image_id": int(self.image_id_edit.text())
        }

        # Вызываем метод родителя для обновления товара
        self.parent().api_thread.update_product(self.product_data['product_id'], update_data)
        self.accept()


class JewelryStoreApp(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("Гусарочка - Панель ювелира")
        self.setMinimumSize(1280, 900)

        # API Thread
        self.api_thread = ApiThread()
        self.api_thread.products_loaded.connect(self.display_products)
        self.api_thread.image_loaded.connect(self.update_product_image)
        self.api_thread.orders_loaded.connect(self.display_orders)
        self.api_thread.individual_orders_loaded.connect(self.display_individual_orders)
        self.api_thread.order_updated.connect(self.handle_order_updated)
        self.api_thread.product_updated.connect(self.handle_product_updated)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.create_sidebar(main_layout)

        # Content area
        self.content_stack = QStackedWidget()

        # Orders page
        self.orders_page = self.create_orders_page()
        self.content_stack.addWidget(self.orders_page)

        # Individual orders page
        self.individual_orders_page = self.create_individual_orders_page()
        self.content_stack.addWidget(self.individual_orders_page)

        # Products page (только просмотр)
        self.products_page = self.create_products_page()
        self.content_stack.addWidget(self.products_page)

        main_layout.addWidget(self.content_stack, stretch=5)

        # Apply styles
        self.apply_styles()

        # Load data
        self.api_thread.fetch_orders()
        self.api_thread.fetch_individual_orders()
        self.api_thread.fetch_products()

    def create_sidebar(self, layout):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(290)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 40, 20, 40)
        sidebar_layout.setSpacing(20)

        # Logo
        logo = QLabel("ГУСАРОЧКА")
        logo.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        logo.setStyleSheet("color: #d4af37;")
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sidebar_layout.addWidget(logo)

        # Navigation buttons
        self.orders_btn = QPushButton("Заказы")
        self.orders_btn.setIcon(QIcon("icons/orders.png"))
        self.orders_btn.setIconSize(QSize(24, 24))
        self.orders_btn.setObjectName("navButton")
        self.orders_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))

        self.individual_orders_btn = QPushButton("Индивидуальные заказы")
        self.individual_orders_btn.setIcon(QIcon("icons/custom.png"))
        self.individual_orders_btn.setIconSize(QSize(24, 24))
        self.individual_orders_btn.setObjectName("navButton")
        self.individual_orders_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))

        self.products_btn = QPushButton("Товары")
        self.products_btn.setIcon(QIcon("icons/catalog.png"))
        self.products_btn.setIconSize(QSize(24, 24))
        self.products_btn.setObjectName("navButton")
        self.products_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(2))

        print("Текущая рабочая директория:", os.getcwd())
        sidebar_layout.addWidget(self.orders_btn)
        sidebar_layout.addWidget(self.individual_orders_btn)
        sidebar_layout.addWidget(self.products_btn)
        sidebar_layout.addStretch()

        # Logout button
        logout_btn = QPushButton("Выйти")
        logout_btn.setObjectName("logoutButton")
        logout_btn.clicked.connect(self.restart_application)
        sidebar_layout.addWidget(logout_btn)

        layout.addWidget(sidebar)

    def restart_application(self):
        """Перезапускает приложение"""
        QApplication.quit()
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def closeEvent(self, event):
        """Обработчик события закрытия окна"""
        self.api_thread.quit()
        event.accept()

    def create_orders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Заказы клиентов")
        title.setFont(QFont('Montserrat', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Refresh button
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setIcon(QIcon("icons/refresh.png"))
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(lambda: self.api_thread.fetch_orders())
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Orders scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.orders_container = QWidget()
        self.orders_layout = QVBoxLayout(self.orders_container)
        self.orders_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_layout.setSpacing(15)

        scroll.setWidget(self.orders_container)
        layout.addWidget(scroll)

        return page

    def create_individual_orders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title = QLabel("Индивидуальные заказы")
        title.setFont(QFont('Montserrat', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Refresh button
        refresh_btn = QPushButton("Обновить")
        refresh_btn.setIcon(QIcon("icons/refresh.png"))
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(lambda: self.api_thread.fetch_individual_orders())
        layout.addWidget(refresh_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        # Orders scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.individual_orders_container = QWidget()
        self.individual_orders_layout = QVBoxLayout(self.individual_orders_container)
        self.individual_orders_layout.setContentsMargins(0, 0, 0, 0)
        self.individual_orders_layout.setSpacing(15)

        scroll.setWidget(self.individual_orders_container)
        layout.addWidget(scroll)

        return page

    def create_products_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Title
        title_layout = QHBoxLayout()

        title = QLabel("Каталог товаров")
        title.setFont(QFont('Montserrat', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        title_layout.addWidget(title)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.setIcon(QIcon("icons/refresh.png"))
        refresh_btn.setObjectName("refreshButton")
        refresh_btn.clicked.connect(lambda: self.api_thread.fetch_products())
        title_layout.addWidget(refresh_btn)

        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Products scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.products_container = QWidget()
        self.products_grid = QGridLayout(self.products_container)
        self.products_grid.setContentsMargins(0, 0, 0, 0)
        self.products_grid.setSpacing(15)
        self.products_grid.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.products_container)
        layout.addWidget(scroll)

        return page

    def display_orders(self, orders):
        # Clear existing orders
        while self.orders_layout.count():
            item = self.orders_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not orders:
            no_orders = QLabel("Нет заказов")
            no_orders.setFont(QFont('Montserrat', 14))
            no_orders.setStyleSheet("color: white;")
            no_orders.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.orders_layout.addWidget(no_orders)
            return

        for order in orders:
            order_frame = QFrame()
            order_frame.setObjectName("orderFrame")
            order_frame.setStyleSheet("""
                #orderFrame { 
                    border: 1px solid #444; 
                    border-radius: 8px;
                }
                #orderFrame:hover {
                    background-color: #252525;
                    border-color: #555;
                    cursor: pointer;
                }
            """)

            # Создаем обработчик клика с замыканием
            def make_click_handler(order_id):
                def handler(event):
                    self.show_order_details(order_id)

                return handler

            order_frame.mousePressEvent = make_click_handler(order['order_id'])

            order_layout = QVBoxLayout(order_frame)
            order_layout.setContentsMargins(15, 15, 15, 15)
            order_layout.setSpacing(10)

            # Верхняя строка с номером заказа и датой
            top_row = QHBoxLayout()

            order_id_label = QLabel(f"Заказ #{order.get('order_id', 'N/A')}")
            order_id_label.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
            order_id_label.setStyleSheet("color: #d4af37;")

            # Форматирование даты заказа
            order_date = order.get('order_date', '')
            if order_date:
                try:
                    dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                    date_text = formatted_date
                except ValueError:
                    date_text = order_date
            else:
                date_text = "Дата неизвестна"

            date_label = QLabel(date_text)
            date_label.setFont(QFont('Montserrat', 12))
            date_label.setStyleSheet("color: #aaaaaa;")

            top_row.addWidget(order_id_label)
            top_row.addStretch()
            top_row.addWidget(date_label)

            order_layout.addLayout(top_row)

            # Клиент
            client_label = QLabel(f"Клиент: {order.get('username', 'N/A')}")
            client_label.setFont(QFont('Montserrat', 12))
            client_label.setStyleSheet("color: white;")
            order_layout.addWidget(client_label)

            # Статус заказа
            status_label = QLabel(f"Статус: {order.get('status', 'Неизвестен')}")
            status_label.setFont(QFont('Montserrat', 12))

            # Цвет статуса в зависимости от состояния
            status = order.get('status', '').lower()
            if 'оплачен' in status or 'завершен' in status:
                status_label.setStyleSheet("color: #55ff55;")
            elif 'отменен' in status or 'возврат' in status:
                status_label.setStyleSheet("color: #ff5555;")
            elif 'обработк' in status or 'ожидан' in status:
                status_label.setStyleSheet("color: #ffff55;")
            else:
                status_label.setStyleSheet("color: white;")

            order_layout.addWidget(status_label)

            # Добавляем иконку для индикации кликабельности
            click_indicator = QLabel("Нажмите для просмотра деталей →")
            click_indicator.setFont(QFont('Montserrat', 10))
            click_indicator.setStyleSheet("color: #888;")
            click_indicator.setAlignment(Qt.AlignmentFlag.AlignRight)
            order_layout.addWidget(click_indicator)

            self.orders_layout.addWidget(order_frame)

        # Добавляем растягивающий элемент в конец
        self.orders_layout.addStretch()

    def display_individual_orders(self, orders):
        # Clear existing orders
        while self.individual_orders_layout.count():
            item = self.individual_orders_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not orders:
            no_orders = QLabel("Нет индивидуальных заказов")
            no_orders.setFont(QFont('Montserrat', 14))
            no_orders.setStyleSheet("color: white;")
            no_orders.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.individual_orders_layout.addWidget(no_orders)
            return

        for order in orders:
            order_frame = QFrame()
            order_frame.setObjectName("orderFrame")
            order_frame.setStyleSheet("""
                #orderFrame { 
                    border: 1px solid #444; 
                    border-radius: 8px;
                }
                #orderFrame:hover {
                    background-color: #252525;
                    border-color: #555;
                    cursor: pointer;
                }
            """)

            # Создаем отдельную функцию для обработки клика с замыканием
            def make_click_handler(order_data):
                def handler(event):
                    self.show_individual_order_details(order_data)

                return handler

            order_frame.mousePressEvent = make_click_handler(order)

            order_layout = QVBoxLayout(order_frame)
            order_layout.setContentsMargins(15, 15, 15, 15)
            order_layout.setSpacing(10)

            # Верхняя строка с номером заказа и датой
            top_row = QHBoxLayout()

            order_id_label = QLabel(f"Индивидуальный заказ #{order.get('order_id', 'N/A')}")
            order_id_label.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
            order_id_label.setStyleSheet("color: #d4af37;")

            # Форматирование даты заказа
            order_date = order.get('order_date', '')
            if order_date:
                try:
                    dt = datetime.fromisoformat(order_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                    date_text = formatted_date
                except ValueError:
                    date_text = order_date
            else:
                date_text = "Дата неизвестна"

            date_label = QLabel(date_text)
            date_label.setFont(QFont('Montserrat', 12))
            date_label.setStyleSheet("color: #aaaaaa;")

            top_row.addWidget(order_id_label)
            top_row.addStretch()
            top_row.addWidget(date_label)

            order_layout.addLayout(top_row)

            # Статус заказа
            status_label = QLabel(f"Статус: {order.get('status', 'Неизвестен')}")
            status_label.setFont(QFont('Montserrat', 12))

            # Цвет статуса в зависимости от состояния
            status = order.get('status', '').lower()
            if 'готов' in status or 'завершен' in status:
                status_label.setStyleSheet("color: #55ff55;")
            elif 'отменен' in status:
                status_label.setStyleSheet("color: #ff5555;")
            elif 'обработк' in status or 'ожидан' in status:
                status_label.setStyleSheet("color: #ffff55;")
            else:
                status_label.setStyleSheet("color: white;")

            order_layout.addWidget(status_label)

            # Клиент
            client_label = QLabel(f"Клиент: ID {order.get('client_id', 'N/A')}")
            client_label.setFont(QFont('Montserrat', 12))
            client_label.setStyleSheet("color: white;")
            order_layout.addWidget(client_label)

            # Телефон
            phone_label = QLabel(f"Телефон: {order.get('contact_phone', 'Не указан')}")
            phone_label.setFont(QFont('Montserrat', 12))
            phone_label.setStyleSheet("color: white;")
            order_layout.addWidget(phone_label)

            # Добавляем иконку для индикации кликабельности
            click_indicator = QLabel("Нажмите для просмотра деталей →")
            click_indicator.setFont(QFont('Montserrat', 10))
            click_indicator.setStyleSheet("color: #888;")
            click_indicator.setAlignment(Qt.AlignmentFlag.AlignRight)
            order_layout.addWidget(click_indicator)

            self.individual_orders_layout.addWidget(order_frame)

        # Добавляем растягивающий элемент в конец
        self.individual_orders_layout.addStretch()

    def display_products(self, products):
        # Clear existing products
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not products:
            no_products = QLabel("Нет товаров")
            no_products.setFont(QFont('Montserrat', 14))
            no_products.setStyleSheet("color: white;")
            no_products.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.products_grid.addWidget(no_products, 0, 0)
            return

        row, col = 0, 0
        max_columns = 4  # Максимальное количество колонок

        for product in products:
            product_frame = QFrame()
            product_frame.setObjectName("productFrame")
            product_frame.setFixedWidth(300)  # Фиксированная ширина плитки

            product_frame.setCursor(Qt.CursorShape.PointingHandCursor)

            def make_click_handler(product_data):
                def handler(event):
                    self.edit_product(product_data)

                return handler

            product_frame.mousePressEvent = make_click_handler(product)

            main_layout = QVBoxLayout(product_frame)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # Image placeholder
            image = QLabel()
            image.setObjectName(f"image_{product['image_id']}")
            image.setAlignment(Qt.AlignmentFlag.AlignCenter)
            image.setStyleSheet("""
                background: #2a2a2a;
                border-radius: 8px 8px 0 0;
                min-height: 220px;
                max-height: 220px;
            """)

            # Product info
            info_frame = QFrame()
            info_frame.setStyleSheet("background: #252525; border-radius: 0 0 8px 8px;")
            info_layout = QVBoxLayout(info_frame)
            info_layout.setContentsMargins(15, 15, 15, 15)
            info_layout.setSpacing(10)

            # Name and details
            name = QLabel(product["name"])
            name.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
            name.setStyleSheet("color: white; margin-bottom: 5px;")
            name.setWordWrap(True)

            details = QLabel(f"{product['material']} · {product['weight']}г · {product['stock_quantity']} шт")
            details.setFont(QFont('Montserrat', 12))
            details.setStyleSheet("color: #aaaaaa; margin-bottom: 10px;")

            # Price
            price = QLabel(f"{product['price']:,} ₽".replace(",", " "))
            price.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
            price.setStyleSheet("color: #d4af37; margin-bottom: 15px;")

            info_layout.addWidget(name)
            info_layout.addWidget(details)
            info_layout.addWidget(price)

            main_layout.addWidget(image)
            main_layout.addWidget(info_frame)

            self.products_grid.addWidget(product_frame, row, col)

            col += 1
            if col >= max_columns:
                col = 0
                row += 1

        # Load images for all products
        for product in products:
            self.api_thread.fetch_image(product["image_id"])

            # Добавляем контекстное меню
            product_frame.setContextMenuPolicy(Qt.ContextMenuPolicy.ActionsContextMenu)
            edit_action = QAction("Редактировать", product_frame)
            edit_action.triggered.connect(lambda _, p=product: self.edit_product(p))
            product_frame.addAction(edit_action)

            self.products_grid.addWidget(product_frame, row, col)

    def edit_product(self, product_data):
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактирование {product_data['name']}")
        dialog.setMinimumWidth(400)

        layout = QVBoxLayout()

        # Форма для редактирования
        form = QFormLayout()

        # Поля для редактирования
        name_edit = QLineEdit(product_data['name'])
        price_edit = QLineEdit(str(product_data['price']))
        price_edit.setValidator(QIntValidator(0, 1000000))

        type_edit = QLineEdit(product_data['type'])
        material_edit = QLineEdit(product_data['material'])

        weight_edit = QLineEdit(str(product_data['weight']))
        weight_edit.setValidator(QDoubleValidator(0, 9999, 2))

        insert_type_edit = QLineEdit(product_data['insert_type'])

        # Добавляем поля в форму
        form.addRow("Название:", name_edit)
        form.addRow("Цена (₽):", price_edit)
        form.addRow("Тип:", type_edit)
        form.addRow("Материал:", material_edit)
        form.addRow("Вес (г):", weight_edit)
        form.addRow("Тип вставки:", insert_type_edit)

        # Кнопки
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(dialog.accept)
        btn_box.rejected.connect(dialog.reject)

        layout.addLayout(form)
        layout.addWidget(btn_box)
        dialog.setLayout(layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            update_data = {
                "name": name_edit.text(),
                "price": int(price_edit.text()),
                "type": type_edit.text(),
                "material": material_edit.text(),
                "weight": float(weight_edit.text()),
                "insert_type": insert_type_edit.text(),
                # Остальные поля оставляем как есть
                "article": product_data['article'],
                "stock_quantity": product_data['stock_quantity'],
                "image_id": product_data['image_id']
            }

            self.api_thread.update_product(product_data['product_id'], update_data)

    def handle_product_updated(self, success, message):
        if success:
            QMessageBox.information(self, "Успех", message)
            self.api_thread.fetch_products()  # Обновляем список
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def update_product_image(self, image_id, pixmap):
        # Update product images
        for image_label in self.findChildren(QLabel, f"image_{image_id}"):
            image_label.setPixmap(pixmap.scaled(
                300, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def show_order_details(self, order_id):
        try:
            response = requests.get(f"http://127.0.0.1:8000/orders/get/{order_id}")
            if response.status_code == 200:
                order_data = response.json()

                # Calculate total amount
                total_amount = sum(item['price'] * item['quantity'] for item in order_data.get('items', []))

                # Prepare data for dialog
                dialog_data = {
                    "order_id": order_data.get("order_id"),
                    "client_id": order_data.get("username"),
                    "order_date": order_data.get("order_date"),
                    "status": order_data.get("status"),
                    "items": [
                        {
                            "item_id": item.get("item_id"),
                            "order_id": item.get("order_id"),
                            "product_id": item.get("product_id"),
                            "product_name": item.get("product_name", "Неизвестный товар"),
                            "article": item.get("article", "N/A"),
                            "quantity": item.get("quantity"),
                            "price": item.get("price")
                        }
                        for item in order_data.get("items", [])
                    ],
                    "total_amount": total_amount
                }

                dialog = OrderDetailDialog(dialog_data, self)
                dialog.exec()
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось получить детали заказа: {response.text}")
        except requests.exceptions.RequestException as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка соединения: {str(e)}")

    def show_individual_order_details(self, order_data):
        dialog = IndividualOrderDetailDialog(order_data, self)
        dialog.exec()

    def handle_order_updated(self, success, message):
        if success:
            QMessageBox.information(self, "Успех", message)
            self.api_thread.fetch_orders()
            self.api_thread.fetch_individual_orders()
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a1a;
                font-family: 'Segoe UI';
            }
            #sidebar {
                background-color: #252525;
                border-right: 1px solid #333;
            }
            #navButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding: 12px 20px;
                font-size: 16px;
                border-radius: 6px;
            }
            #navButton:hover {
                background-color: #333;
            }
            #logoutButton {
                background-color: #333;
                color: white;
                padding: 12px;
                border-radius: 6px;
            }
            #logoutButton:hover {
                background-color: #444;
            }
            #orderFrame {
                background: transparent;
                border: 1px solid #333;
                border-radius: 8px;
            }
            #orderFrame:hover {
                background: #252525;
                border-color: #444;
            }
            #productFrame {
            background: transparent;
            border: 1px solid #333;
            border-radius: 10px;
            }
            #productFrame:hover {
                background: #252525;
                border-color: #444;
            }
            #refreshButton {
                background-color: #333;
                color: white;
                padding: 8px 16px;
                border-radius: 5px;
                font-size: 14px;
            }
            #refreshButton:hover {
                background-color: #444;
            }
            QScrollBar:vertical {
                width: 10px;
                background: #252525;
            }
            QScrollBar::handle:vertical {
                background: #d4af37;
                min-height: 20px;
                border-radius: 5px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Для тестирования можно использовать user_id=1 (администратор)
    window = JewelryStoreApp(user_id=1)
    window.show()

    sys.exit(app.exec())