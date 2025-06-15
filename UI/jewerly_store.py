import os
import sys
from datetime import datetime

import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame,
                               QScrollArea, QStackedWidget, QSizePolicy, QDialog,
                               QGridLayout, QMessageBox, QLineEdit, QLayout, QTextEdit, QFormLayout, QComboBox)
from PySide6.QtCore import Qt, QSize, QThread, Signal, QTimer
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage, QDoubleValidator, QIntValidator


class ApiThread(QThread):
    products_loaded = Signal(list)
    image_loaded = Signal(int, QPixmap)
    payment_success = Signal(bool, str)
    order_created = Signal(bool, str)  # Новый сигнал для результата создания заказа

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

    def process_payment(self, card_data, total_amount):
        print(card_data, "  ", total_amount)
        try:
            # В реальном приложении здесь должен быть вызов API платежной системы
            # Это имитация обработки платежа
            response = {"success": True, "message": "Платеж успешно обработан"}

            # Имитируем задержку обработки платежа
            self.msleep(2000)

            self.payment_success.emit(response["success"], response["message"])
        except Exception as e:
            self.payment_success.emit(False, f"Ошибка при обработке платежа: {str(e)}")

    def create_order(self, order_data):
        try:
            response = requests.post(
                f"{self.base_url}/orders/create",
                json=order_data
            )

            if response.status_code == 200:
                order_id = response.json().get('order_id')
                if order_id:
                    for item in order_data.get('items', []):
                        product_id = item.get('product_id')
                        quantity = item.get('quantity', 1)

                        reduce_data = {
                            "amount": quantity,
                            "reason": f"Order #{order_id}"
                        }
                        reduce_response = requests.patch(
                            f"{self.base_url}/products/reduce-stock/{product_id}",
                            json=reduce_data
                        )

                        if reduce_response.status_code != 200:
                            print(f"Failed to reduce stock for product {product_id}: {reduce_response.text}")

                    self.order_created.emit(True, "Заказ успешно создан")
                else:
                    self.order_created.emit(False, "Не удалось получить ID созданного заказа")
            else:
                self.order_created.emit(False, f"Ошибка создания заказа: {response.text}")
        except requests.exceptions.RequestException as e:
            self.order_created.emit(False, f"Ошибка соединения: {str(e)}")

    def fetch_order_details(self, client_id, order_id):
        try:
            response = requests.get(f"{self.base_url}/orders/client/{client_id}/{order_id}")
            if response.status_code == 200:
                order_data = response.json()

                # Дополнительно запрашиваем информацию о товарах, если она не полная
                if 'items' in order_data:
                    for item in order_data['items']:
                        if 'name' not in item or 'price' not in item:
                            product_response = requests.get(f"{self.base_url}/products/get/{item['product_id']}")
                            if product_response.status_code == 200:
                                product_data = product_response.json()
                                item.update({
                                    'name': product_data.get('name', 'Неизвестный товар'),
                                    'price': product_data.get('price', 0)
                                })
                return order_data
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching order details: {e}")
            return None


class PaymentDialog(QDialog):
    payment_success = Signal(bool, str)

    def __init__(self, total_amount, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Оформление заказа")
        self.setFixedSize(400, 400)

        self.total_amount = total_amount
        self.parent = parent  # Сохраняем ссылку на родительское окно

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("Введите данные карты")
        title.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #d4af37;")
        layout.addWidget(title)

        # Поля для ввода данных карты
        self.card_number = QLineEdit()
        self.card_number.setPlaceholderText("Номер карты")
        self.card_number.setInputMask("9999 9999 9999 9999;_")

        self.card_expiry = QLineEdit()
        self.card_expiry.setPlaceholderText("ММ/ГГ")
        self.card_expiry.setInputMask("99/99;_")

        self.card_cvv = QLineEdit()
        self.card_cvv.setPlaceholderText("CVV")
        self.card_cvv.setInputMask("999;_")
        self.card_cvv.setEchoMode(QLineEdit.Password)

        # Сумма заказа
        amount_label = QLabel(f"Сумма к оплате: {total_amount:,} ₽".replace(",", " "))
        amount_label.setFont(QFont('Montserrat', 14))
        amount_label.setStyleSheet("color: white;")

        # Кнопка оплаты
        pay_button = QPushButton("Оплатить")
        pay_button.setObjectName("payButton")
        pay_button.clicked.connect(self.process_payment)

        # Сообщение о статусе
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)

        # Добавляем элементы в layout
        for widget in [self.card_number, self.card_expiry, self.card_cvv, amount_label, pay_button, self.status_label]:
            layout.addWidget(widget)

        layout.addStretch()
        self.setLayout(layout)

        self.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 4px;
                background: #333;
                color: white;
            }
            #payButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #payButton:hover {
                background-color: #f0d87c;
            }
        """)

    def process_payment(self):
        # Проверка заполнения полей
        if not all([self.card_number.text().replace(" ", "").replace("_", ""),
                    self.card_expiry.text().replace("/", "").replace("_", ""),
                    self.card_cvv.text().replace("_", "")]):
            self.show_status("Пожалуйста, заполните все поля", False)
            return

        # Показываем сообщение о обработке
        self.show_status("Обработка платежа...", True)

        # Блокируем кнопку оплаты
        self.findChild(QPushButton, "payButton").setEnabled(False)

        # Имитируем обработку платежа
        QTimer.singleShot(2000, self.payment_successful)

    def payment_successful(self):
        # В реальном приложении здесь должен быть вызов платежного API
        # После успешной оплаты создаем заказ
        self.show_status("Платеж успешно обработан", True)

        # Получаем реальный ID пользователя из родительского окна
        user_id = getattr(self.parent, 'user_id', None) or getattr(self.parent, 'current_user_id', None)

        if user_id is None:
            self.show_status("Ошибка: не удалось определить пользователя", False)
            self.findChild(QPushButton, "payButton").setEnabled(True)
            return

        # Подготавливаем данные заказа
        order_data = {
            "client_id": user_id,  # Используем реальный ID пользователя
            "status": "Оплачен",
            "items": [
                {
                    "product_id": item["product_id"],
                    "quantity": item.get("quantity", 1)  # Добавил quantity из корзины, если есть
                } for item in self.parent.cart
            ]
        }
        print("Создание заказа с данными:", order_data)

        # Используем API thread из родительского окна для создания заказа
        self.parent.api_thread.create_order(order_data)

        # Закрываем диалог после небольшой задержки
        QTimer.singleShot(1000, self.accept)

    def show_status(self, message, is_success):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #d4af37;" if is_success else "color: #ff5555;")
        self.status_label.setVisible(True)

class ProductDetailDialog(QDialog):
    def __init__(self, product, pixmap, parent=None):
        super().__init__(parent)
        self.product = product
        self.parent = parent
        self.setWindowTitle(product["name"])

        # Устанавливаем минимальный размер и позволяем изменять размер окна
        self.setMinimumSize(600, 500)
        self.setSizeGripEnabled(True)  # Включаем возможность изменения размера

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Product image - сохраняем оригинальное изображение
        self.original_pixmap = pixmap
        self.image_label = QLabel()
        self.update_image_display()  # Метод для обновления отображения изображения
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Product details
        details_layout = QVBoxLayout()

        # Название товара с переносом слов и возможностью расширения
        name_label = QLabel(product["name"])
        name_label.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #d4af37; background: transparent;")
        name_label.setWordWrap(True)  # Включаем перенос слов
        name_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        price_label = QLabel(f"{product['price']:,} ₽".replace(",", " "))
        price_label.setFont(QFont('Montserrat', 16))
        price_label.setStyleSheet("color: #d4af37;")

        details = [
            f"Артикул: {product['article']}",
            f"Тип: {product['type']}",
            f"Материал: {product['material']}",
            f"Вставка: {product['insert_type']}",
            f"Вес: {product['weight']}г",
            f"На складе: {product['stock_quantity']} шт"
        ]

        details_text = "\n".join(details)
        details_label = QLabel(details_text)
        details_label.setFont(QFont('Montserrat', 14))
        details_label.setStyleSheet("color: white; background: transparent;")
        details_label.setWordWrap(True)  # Перенос слов для деталей

        # Add to cart button
        add_to_cart_btn = QPushButton("Добавить в корзину")
        add_to_cart_btn.setObjectName("addToCartButton")
        add_to_cart_btn.setFixedHeight(50)
        add_to_cart_btn.clicked.connect(self.add_to_cart)

        details_layout.addWidget(name_label)
        details_layout.addWidget(price_label)
        details_layout.addWidget(details_label)
        details_layout.addStretch()

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(add_to_cart_btn)
        details_layout.addLayout(buttons_layout)

        # Main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(self.image_label, stretch=1)
        main_layout.addLayout(details_layout, stretch=1)

        layout.addLayout(main_layout)
        self.setLayout(layout)

        self.setStyleSheet("""
            #addToCartButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                border-radius: 5px;
            }
            #addToCartButton:hover {
                background-color: #f0d87c;
            }
            QDialog {
                background-color: #1a1a1a;
            }
        """)

        # Обработчик изменения размера окна
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetMinimumSize)

    def update_image_display(self):
        """Обновляет отображение изображения с учетом текущего размера окна"""
        if not self.original_pixmap.isNull():
            # Получаем текущий размер области для изображения
            img_width = self.width() // 2 - 60  # Половина ширины окна минус отступы
            img_height = self.height() - 100  # Высота окна минус отступы

            # Масштабируем с сохранением пропорций и сглаживанием
            scaled_pixmap = self.original_pixmap.scaled(
                img_width, img_height,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        """Обработчик изменения размера окна"""
        super().resizeEvent(event)
        self.update_image_display()

    def add_to_cart(self):
        """Метод для добавления товара в корзину с проверкой наличия"""
        if hasattr(self.parent, 'add_to_cart'):
            # Проверяем количество товара на складе
            if self.product["stock_quantity"] <= 0:
                QMessageBox.warning(self.parent, "Товара нет в наличии",
                                    f"Товар '{self.product['name']}' отсутствует на складе")
                return

            # Проверяем, если товар уже в корзине, не превышает ли количество доступное
            for item in self.parent.cart:
                if item["product_id"] == self.product["product_id"]:
                    if item.get("quantity", 1) >= self.product["stock_quantity"]:
                        QMessageBox.warning(self.parent, "Недостаточно товара",
                                            f"Нельзя добавить больше товара '{self.product['name']}', чем есть на складе ({self.product['stock_quantity']} шт.)")
                        return

            self.parent.add_to_cart(self.product)


class OrderDetailDialog(QDialog):
    def __init__(self, order_details, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Детали заказа #{order_details.get('order_id', '')}")
        self.setMinimumSize(800, 600)
        self.order_details = order_details  # Сохраняем детали заказа

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Order info
        order_info = QLabel(f"Заказ #{order_details.get('order_id', 'N/A')}")
        order_info.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        order_info.setStyleSheet("color: #d4af37;")
        layout.addWidget(order_info)

        # Status and date
        status_date_layout = QHBoxLayout()

        status = QLabel(f"Статус: {order_details.get('status', 'Неизвестен')}")
        status.setFont(QFont('Montserrat', 14))

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

        status_date_layout.addWidget(status)
        status_date_layout.addStretch()
        status_date_layout.addWidget(date)
        layout.addLayout(status_date_layout)

        # Items
        items_label = QLabel("Товары:")
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
            item_frame = QFrame()
            item_layout = QHBoxLayout(item_frame)
            item_layout.setContentsMargins(10, 10, 10, 10)

            # Item info
            info_layout = QVBoxLayout()
            info_layout.setContentsMargins(0, 0, 0, 0)
            info_layout.setSpacing(5)

            name = QLabel(item.get('name', 'Неизвестный товар'))
            name.setFont(QFont('Montserrat', 14))

            quantity = item.get('quantity', 1)
            price = item.get('price', 0)
            total_price = quantity * price

            details = QLabel(f"{quantity} × {price:,} ₽ = {total_price:,} ₽".replace(",", " "))
            details.setFont(QFont('Montserrat', 12))
            details.setStyleSheet("color: #aaaaaa;")

            info_layout.addWidget(name)
            info_layout.addWidget(details)
            info_layout.addStretch()

            item_layout.addLayout(info_layout, stretch=1)
            items_layout.addWidget(item_frame)

        items_layout.addStretch()
        scroll.setWidget(items_container)
        layout.addWidget(scroll)

        # Total
        total = sum(item.get('price', 0) * item.get('quantity', 1) for item in order_details.get('items', []))
        total_label = QLabel(f"Итого: {total:,} ₽".replace(",", " "))
        total_label.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        total_label.setStyleSheet("color: #d4af37;")
        layout.addWidget(total_label, alignment=Qt.AlignmentFlag.AlignRight)

        # Кнопка возврата товара (добавлено)
        return_btn = QPushButton("Оформить возврат")
        return_btn.setObjectName("returnButton")
        return_btn.clicked.connect(self.initiate_return)
        layout.addWidget(return_btn)

        self.setLayout(layout)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
            }
            #returnButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #returnButton:hover {
                background-color: #f0d87c;
            }
        """)

    def initiate_return(self):
        """Инициирует процесс возврата товара"""
        # Создаем диалог для ввода причины возврата
        dialog = QDialog(self)
        dialog.setWindowTitle("Оформление возврата")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Оформление возврата")
        title.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #d4af37;")
        layout.addWidget(title)

        # Поле для описания причины возврата
        description_label = QLabel("Причина возврата:")
        description_label.setFont(QFont('Montserrat', 12))
        description_label.setStyleSheet("color: white;")

        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Опишите причину возврата...")
        self.description_edit.setMaximumHeight(100)

        # Кнопка подтверждения
        confirm_btn = QPushButton("Подтвердить возврат")
        confirm_btn.setObjectName("confirmButton")
        confirm_btn.clicked.connect(lambda: self.process_return(dialog))

        # Сообщение о статусе
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)

        layout.addWidget(description_label)
        layout.addWidget(self.description_edit)
        layout.addWidget(confirm_btn)
        layout.addWidget(self.status_label)
        layout.addStretch()

        dialog.setStyleSheet("""
            QTextEdit {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
            #confirmButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #confirmButton:hover {
                background-color: #f0d87c;
            }
        """)

        dialog.exec()

    def process_return(self, dialog):
        """Отправляет запрос на возврат товара"""
        description = self.description_edit.toPlainText().strip()
        if not description:
            self.status_label.setText("Пожалуйста, укажите причину возврата")
            self.status_label.setStyleSheet("color: #ff5555;")
            self.status_label.setVisible(True)
            return

        return_data = {
            "order_id": self.order_details.get('order_id'),
            "client_id": self.parent().user_id,  # Получаем user_id из родительского окна
            "return_date": datetime.now().isoformat(),
            "description": description,
            "status": "В обработке"
        }

        try:
            response = requests.post(
                "http://127.0.0.1:8000/returns/create",
                json=return_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                self.status_label.setText("Запрос на возврат успешно отправлен")
                self.status_label.setStyleSheet("color: #55ff55;")
                self.status_label.setVisible(True)
                QTimer.singleShot(1500, dialog.close)
                QMessageBox.information(self, "Успех", "Запрос на возврат успешно оформлен")
            else:
                error_msg = f"Ошибка {response.status_code}: {response.text}"
                self.status_label.setText(error_msg)
                self.status_label.setStyleSheet("color: #ff5555;")
                self.status_label.setVisible(True)
        except requests.exceptions.RequestException as e:
            self.status_label.setText(f"Ошибка соединения: {str(e)}")
            self.status_label.setStyleSheet("color: #ff5555;")
            self.status_label.setVisible(True)


class IndividualOrderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Индивидуальный заказ")
        self.setMinimumSize(500, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Заголовок
        title = QLabel("Индивидуальный заказ")
        title.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #d4af37;")
        layout.addWidget(title)

        # Описание
        desc = QLabel(
            "Заполните форму для создания индивидуального заказа. Наши менеджеры свяжутся с вами для уточнения деталей.")
        desc.setWordWrap(True)
        desc.setFont(QFont('Montserrat', 12))
        layout.addWidget(desc)

        # Форма
        form_layout = QFormLayout()
        form_layout.setHorizontalSpacing(15)
        form_layout.setVerticalSpacing(10)

        # Поля формы
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Опишите ваши пожелания к изделию...")
        self.description_input.setMaximumHeight(100)

        self.total_amount_input = QLineEdit()
        self.total_amount_input.setPlaceholderText("Предполагаемая сумма")
        self.total_amount_input.setValidator(QDoubleValidator(0, 1000000, 2))

        self.delivery_address_input = QLineEdit()
        self.delivery_address_input.setPlaceholderText("Адрес доставки")

        self.contact_phone_input = QLineEdit()
        self.contact_phone_input.setPlaceholderText("+7 (XXX) XXX-XX-XX")
        self.contact_phone_input.setInputMask("+7 (999) 999-99-99;_")

        # Добавление полей в форму
        form_layout.addRow("Описание:", self.description_input)
        form_layout.addRow("Сумма:", self.total_amount_input)
        form_layout.addRow("Адрес доставки:", self.delivery_address_input)
        form_layout.addRow("Контактный телефон:", self.contact_phone_input)

        layout.addLayout(form_layout)

        # Кнопки
        buttons_layout = QHBoxLayout()

        submit_btn = QPushButton("Оформить заказ")
        submit_btn.setObjectName("submitButton")
        submit_btn.clicked.connect(self.submit_order)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.setObjectName("cancelButton")
        cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(submit_btn)
        buttons_layout.addWidget(cancel_btn)
        layout.addLayout(buttons_layout)

        # Статус
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
            }
            QLabel {
                color: white;
            }
            QLineEdit, QTextEdit {
                background-color: #333;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 8px;
            }
            QTextEdit {
                padding: 8px;
            }
            #submitButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #submitButton:hover {
                background-color: #f0d87c;
            }
            #cancelButton {
                background-color: #333;
                color: white;
                font-size: 16px;
                padding: 12px;
                border-radius: 5px;
            }
            #cancelButton:hover {
                background-color: #444;
            }
        """)

    def submit_order(self):
        # Проверка обязательных полей
        if not all([
            self.description_input.toPlainText().strip(),
            self.contact_phone_input.text().replace(" ", "").replace("_", ""),
            self.delivery_address_input.text().strip()
        ]):
            self.show_status("Пожалуйста, заполните все обязательные поля", False)
            return

        try:
            total_amount = float(self.total_amount_input.text()) if self.total_amount_input.text() else 0
        except ValueError:
            total_amount = 0

        order_data = {
            "client_id": self.parent().user_id,
            "order_date": datetime.now().isoformat(),
            "status": "Новый",
            "description": self.description_input.toPlainText().strip(),
            "total_amount": total_amount,
            "delivery_address": self.delivery_address_input.text().strip(),
            "contact_phone": self.contact_phone_input.text()
        }

        self.show_status("Отправка заказа...", True)

        try:
            response = requests.post(
                "http://127.0.0.1:8000/individual-orders/create",
                json=order_data,
                headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                self.show_status("Ваш индивидуальный заказ успешно создан!", True)
                QTimer.singleShot(1500, self.accept)
            else:
                self.show_status(f"Ошибка: {response.text}", False)
        except requests.exceptions.RequestException as e:
            self.show_status(f"Ошибка соединения: {str(e)}", False)

    def show_status(self, message, is_success):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("color: #55ff55;" if is_success else "color: #ff5555;")
        self.status_label.setVisible(True)


class JewelryStoreApp(QMainWindow):
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id  # Сохраняем user_id
        self.setWindowTitle("Гусарочка")
        self.setMinimumSize(1280, 900)
        self.cart = []  # Список товаров в корзине
        print(user_id)

        # API Thread
        self.api_thread = ApiThread()
        self.api_thread.products_loaded.connect(self.display_products)
        self.api_thread.image_loaded.connect(self.update_product_image)
        self.api_thread.products_loaded.connect(self.update_category_filters)  # Добавляем обновление фильтров
        self.api_thread.order_created.connect(self.handle_order_created)

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

        # Home page
        self.home_page = self.create_home_page()
        self.content_stack.addWidget(self.home_page)

        # Catalog page
        self.catalog_page = self.create_catalog_page()
        self.content_stack.addWidget(self.catalog_page)

        # Cart page
        self.cart_page = self.create_cart_page()
        self.content_stack.addWidget(self.cart_page)

        # Profile page (будет создана при первом обращении)
        self.profile_page = self.create_profile_page()
        self.content_stack.addWidget(self.profile_page)

        main_layout.addWidget(self.content_stack, stretch=5)

        # Apply styles
        self.apply_styles()

        # Load data
        self.api_thread.fetch_products()

    def create_sidebar(self, layout):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(280)
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
        self.home_btn = QPushButton("Главная")
        self.home_btn.setIcon(QIcon("icons/home.png"))
        self.home_btn.setIconSize(QSize(24, 24))
        self.home_btn.setObjectName("navButton")
        self.home_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(0))

        self.catalog_btn = QPushButton("Каталог")
        self.catalog_btn.setIcon(QIcon("icons/catalog.png"))
        self.catalog_btn.setIconSize(QSize(24, 24))
        self.catalog_btn.setObjectName("navButton")
        self.catalog_btn.clicked.connect(lambda: self.content_stack.setCurrentIndex(1))

        self.cart_btn = QPushButton(f"Корзина ({len(self.cart)})")
        self.cart_btn.setIcon(QIcon("icons/cart.png"))
        self.cart_btn.setIconSize(QSize(24, 24))
        self.cart_btn.setObjectName("navButton")
        self.cart_btn.clicked.connect(lambda: self.update_cart_page())

        self.profile_btn = QPushButton("Профиль")
        self.profile_btn.setIcon(QIcon("icons/profile.png"))
        self.profile_btn.setIconSize(QSize(24, 24))
        self.profile_btn.setObjectName("navButton")
        self.profile_btn.clicked.connect(lambda: self.show_profile_page())

        self.custom_order_btn = QPushButton("Индивидуальный заказ")
        self.custom_order_btn.setIcon(QIcon("icons/custom.png"))
        self.custom_order_btn.setIconSize(QSize(24, 24))
        self.custom_order_btn.setObjectName("navButton")
        self.custom_order_btn.clicked.connect(self.show_individual_order_dialog)


        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.catalog_btn)
        sidebar_layout.addWidget(self.cart_btn)
        sidebar_layout.addWidget(self.custom_order_btn)
        sidebar_layout.addWidget(self.profile_btn)
        sidebar_layout.addStretch()

        # Logout button
        logout_btn = QPushButton("Выйти")
        logout_btn.setObjectName("logoutButton")
        logout_btn.clicked.connect(self.restart_application)  # Изменено здесь
        sidebar_layout.addWidget(logout_btn)

        layout.addWidget(sidebar)

    def restart_application(self):
        """Перезапускает приложение"""
        QApplication.quit()
        # Запускаем новую копию приложения с тем же user_id
        python = sys.executable
        os.execl(python, python, *sys.argv)

    def closeEvent(self, event):
        """Обработчик события закрытия окна"""
        self.api_thread.quit()
        event.accept()

    def create_home_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Welcome section
        welcome = QLabel("Добро пожаловать в Гусарочку")
        welcome.setFont(QFont('Montserrat', 24, QFont.Weight.Bold))
        welcome.setStyleSheet("color: white;")
        layout.addWidget(welcome)

        # Promo section
        promo = QLabel("Новая коллекция 2025")
        promo.setFont(QFont('Montserrat', 20, QFont.Weight.Bold))
        promo.setStyleSheet("color: #d4af37;")
        layout.addWidget(promo)

        # Featured products
        self.featured_products = QWidget()
        self.featured_layout = QHBoxLayout(self.featured_products)
        self.featured_layout.setContentsMargins(0, 0, 0, 0)
        self.featured_layout.setSpacing(20)

        layout.addWidget(self.featured_products)
        layout.addStretch()

        return page

    def create_catalog_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Filters
        self.filters_layout = QHBoxLayout()
        self.filters_layout.setSpacing(10)

        layout.addLayout(self.filters_layout)

        # Products scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet("border: none; background: transparent;")

        self.products_container = QWidget()
        self.products_grid = QVBoxLayout(self.products_container)  # Changed to VBox
        self.products_grid.setContentsMargins(0, 0, 0, 0)
        self.products_grid.setSpacing(20)

        scroll.setWidget(self.products_container)
        layout.addWidget(scroll)

        return page

    def update_category_filters(self, products):
        # Clear existing filters
        while self.filters_layout.count():
            item = self.filters_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Get unique materials from products
        materials = set(product["material"] for product in products)
        materials = sorted(materials)  # Sort materials alphabetically

        # Add "All" button
        all_btn = QPushButton("Все")
        all_btn.setObjectName("filterButton")
        all_btn.clicked.connect(lambda: self.filter_products("Все"))
        self.filters_layout.addWidget(all_btn)

        # Add material buttons
        for material in materials:
            btn = QPushButton(material)
            btn.setObjectName("filterButton")
            btn.clicked.connect(lambda _, mat=material: self.filter_products(mat))
            self.filters_layout.addWidget(btn)

        # Save all products
        self.all_products = products

    def filter_products(self, material):
        # Clear existing products
        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Filter products by material
        if material == "Все":
            filtered_products = self.all_products
        else:
            filtered_products = [product for product in self.all_products if product["material"] == material]

        # Display filtered products
        for product in filtered_products:
            item = self.create_product_item(product)
            self.products_grid.addWidget(item)
            # Load image for this product
            self.api_thread.fetch_image(product["image_id"])

    def show_individual_order_dialog(self):
        dialog = IndividualOrderDialog(self)
        dialog.exec()

    def create_cart_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Cart title
        title = QLabel("Ваша корзина")
        title.setFont(QFont('Montserrat', 24, QFont.Weight.Bold))
        title.setStyleSheet("color: white;")
        layout.addWidget(title)

        # Cart items
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setStyleSheet("border: none; background: transparent;")

        self.cart_container = QWidget()
        self.cart_layout = QVBoxLayout(self.cart_container)
        self.cart_layout.setContentsMargins(0, 0, 0, 0)
        self.cart_layout.setSpacing(15)

        self.cart_scroll.setWidget(self.cart_container)
        layout.addWidget(self.cart_scroll)

        # Total and checkout
        self.total_label = QLabel("Итого: 0 ₽")
        self.total_label.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        self.total_label.setStyleSheet("color: #d4af37;")

        # Buttons layout
        buttons_layout = QHBoxLayout()

        # Clear cart button
        clear_cart_btn = QPushButton("Очистить корзину")
        clear_cart_btn.setObjectName("clearCartButton")
        clear_cart_btn.setFixedHeight(50)
        clear_cart_btn.clicked.connect(self.clear_cart)

        # Checkout button
        checkout_btn = QPushButton("Оформить заказ")
        checkout_btn.setObjectName("checkoutButton")
        checkout_btn.setFixedHeight(50)
        checkout_btn.clicked.connect(self.checkout)

        buttons_layout.addWidget(clear_cart_btn)
        buttons_layout.addWidget(checkout_btn)

        layout.addWidget(self.total_label)
        layout.addLayout(buttons_layout)

        return page

    def checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Корзина пуста", "Ваша корзина пуста. Добавьте товары перед оформлением заказа.")
            return

        # Используем тот же расчет суммы, что и в update_cart_page
        total = sum(p["price"] * p.get("quantity", 1) for p in self.cart)
        payment_dialog = PaymentDialog(total, self)
        payment_dialog.exec()

    def handle_order_created(self, success, message):
        if success:
            # Очищаем корзину после успешного создания заказа
            self.cart = []
            self.update_cart_page()
            # Обновляем список заказов в профиле
            self.load_profile_data()
            QMessageBox.information(self, "Успех", "Ваш заказ успешно создан и оплачен!")
        else:
            QMessageBox.warning(self, "Ошибка", message)

    def clear_cart(self):
        """Очищает всю корзину"""
        if not self.cart:
            QMessageBox.information(self, "Корзина пуста", "Ваша корзина уже пуста.")
            return

        reply = QMessageBox.question(
            self,
            "Очистка корзины",
            "Вы уверены, что хотите очистить корзину?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.cart = []
            self.update_cart_page()
            QMessageBox.information(self, "Корзина очищена", "Все товары удалены из корзины.")

    def update_cart_page(self):
        # Clear existing cart items
        while self.cart_layout.count():
            item = self.cart_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add current cart items
        for product in self.cart:
            item = self.create_cart_item(product)
            self.cart_layout.addWidget(item)

        # Update total
        total = sum(p["price"] * p.get("quantity", 1) for p in self.cart)
        self.total_label.setText(f"Итого: {total:,} ₽".replace(",", " "))

        # Update cart button in sidebar
        self.cart_btn.setText(f"Корзина ({len(self.cart)})")

        # Show cart page
        self.content_stack.setCurrentIndex(2)

    def create_cart_item(self, product):
        frame = QFrame()
        frame.setObjectName("cartItemFrame")
        frame.setFixedHeight(120)  # Фиксированная высота для всех элементов корзины

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Image
        image = QLabel()
        image.setObjectName(f"cart_image_{product['image_id']}")
        image.setFixedSize(80, 80)
        image.setStyleSheet("""
            background: #2a2a2a;
            border-radius: 8px;
        """)

        # Product info - теперь с вертикальным выравниванием по верхнему краю
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)
        info_layout.setSpacing(5)
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # Выравнивание по верхнему краю

        name = QLabel(product["name"])
        name.setFont(QFont('Montserrat', 14))
        name.setStyleSheet("margin-bottom: 5px;")

        details = QLabel(f"{product['material']} · {product['weight']}г · Количество: {product.get('quantity', 1)}")
        details.setFont(QFont('Montserrat', 12))
        details.setStyleSheet("color: #aaaaaa; margin-bottom: 5px;")

        price = QLabel(f"{product['price']:,} ₽".replace(",", " "))
        price.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
        price.setStyleSheet("color: #d4af37;")

        info_layout.addWidget(name)
        info_layout.addWidget(details)
        info_layout.addWidget(price)
        info_layout.addStretch()  # Добавляем растягивающий элемент

        # Remove button - выравниваем по центру вертикально
        remove_btn = QPushButton()
        remove_btn.setIcon(QIcon("icons/trash.png"))
        remove_btn.setIconSize(QSize(24, 24))
        remove_btn.setObjectName("removeButton")
        remove_btn.clicked.connect(lambda: self.remove_from_cart(product))
        remove_btn.setFixedSize(40, 40)

        layout.addWidget(image)
        layout.addLayout(info_layout)
        layout.addWidget(remove_btn, alignment=Qt.AlignmentFlag.AlignVCenter)  # Выравнивание кнопки по центру

        # Load image if available
        for label in self.findChildren(QLabel):
            if label.objectName() == f"image_{product['image_id']}":
                if label.pixmap():
                    image.setPixmap(label.pixmap().scaled(
                        80, 80,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    ))

        return frame

    def add_to_cart(self, product):
        """Добавляем товар в корзину или увеличиваем количество, если уже есть"""
        # Проверяем, есть ли товар уже в корзине
        for item in self.cart:
            if item["product_id"] == product["product_id"]:
                # Проверяем, не превышает ли количество доступное на складе
                if item.get("quantity", 1) >= product["stock_quantity"]:
                    QMessageBox.warning(self, "Недостаточно товара",
                                        f"Нельзя добавить больше товара '{product['name']}', чем есть на складе ({product['stock_quantity']} шт.)")
                    return
                item["quantity"] = item.get("quantity", 1) + 1
                self.cart_btn.setText(f"Корзина ({len(self.cart)})")
                return

        # Если товара нет в корзине, проверяем, есть ли он на складе
        if product["stock_quantity"] <= 0:
            QMessageBox.warning(self, "Товара нет в наличии",
                                f"Товар '{product['name']}' отсутствует на складе")
            return

        # Если товара нет в корзине, добавляем с количеством 1
        product_with_quantity = product.copy()
        product_with_quantity["quantity"] = 1
        self.cart.append(product_with_quantity)
        self.cart_btn.setText(f"Корзина ({len(self.cart)})")

    def remove_from_cart(self, product):
        """Удаляет конкретный товар из корзины или уменьшает количество"""
        for item in self.cart:
            if item["product_id"] == product["product_id"]:
                if item.get("quantity", 1) > 1:
                    item["quantity"] -= 1
                else:
                    self.cart = [p for p in self.cart if p["product_id"] != product["product_id"]]
                self.update_cart_page()
                QMessageBox.information(self, "Товар удален", f"Товар {product['name']} удален из корзины.")
                return

    def show_product_detail(self, product, pixmap):
        dialog = ProductDetailDialog(product, pixmap, self)
        dialog.exec()

    def display_products(self, products):
        # Clear existing products
        while self.featured_layout.count():
            item = self.featured_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        while self.products_grid.count():
            item = self.products_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Display featured products (first 3)
        for product in products[:3]:
            item = self.create_product_item(product)
            self.featured_layout.addWidget(item)

        # Display all products in catalog
        for product in products:
            item = self.create_product_item(product)
            self.products_grid.addWidget(item)
            # Load image for this product
            self.api_thread.fetch_image(product["image_id"])

    def create_product_item(self, product):
        frame = QFrame()
        frame.setObjectName("productFrame")
        frame.setFixedHeight(420)

        main_layout = QVBoxLayout(frame)
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

        details = QLabel(f"{product['material']} · {product['weight']}г")
        details.setFont(QFont('Montserrat', 12))
        details.setStyleSheet("color: #aaaaaa; margin-bottom: 10px;")

        # Price
        price = QLabel(f"{product['price']:,} ₽".replace(",", " "))
        price.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        price.setStyleSheet("color: #d4af37; margin-bottom: 15px;")

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)

        # Detail button
        detail_btn = QPushButton("Подробнее")
        detail_btn.setIcon(QIcon("icons/eye.png"))
        detail_btn.setIconSize(QSize(28, 28))
        detail_btn.setObjectName("detailButton")
        detail_btn.clicked.connect(lambda: self.show_product_detail(
            product,
            self.findChild(QLabel, f"image_{product['image_id']}").pixmap()
        ))

        # Cart button
        cart_btn = QPushButton("В корзину")
        cart_btn.setIcon(QIcon("icons/cart_add.png"))
        cart_btn.setIconSize(QSize(28, 28))
        cart_btn.setObjectName("cartButton")
        cart_btn.clicked.connect(lambda: self.add_to_cart(product))

        buttons_layout.addWidget(detail_btn)
        buttons_layout.addWidget(cart_btn)

        info_layout.addWidget(name)
        info_layout.addWidget(details)
        info_layout.addWidget(price)
        info_layout.addLayout(buttons_layout)

        main_layout.addWidget(image)
        main_layout.addWidget(info_frame)

        return frame

    def update_product_image(self, image_id, pixmap):
        # Update product images
        for image_label in self.findChildren(QLabel, f"image_{image_id}"):
            image_label.setPixmap(pixmap.scaled(
                300, 300,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

        # Update cart images if needed
        for cart_image in self.findChildren(QLabel, f"cart_image_{image_id}"):
            cart_image.setPixmap(pixmap.scaled(
                80, 80,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))

    def create_profile_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(30)

        # Стили
        info_label_style = """
            QLabel {
                color: white;
                background-color: transparent;
                padding: 0;
                margin: 0;
                border: none;
            }
        """

        title_style = """
            QLabel {
                color: #d4af37;
                background-color: transparent;
                font-weight: bold;
                padding: 0;
                margin: 0;
                border: none;
            }
        """

        # Заголовок
        title = QLabel("Ваш профиль")
        title.setFont(QFont('Montserrat', 24, QFont.Weight.Bold))
        title.setStyleSheet(title_style)
        layout.addWidget(title)

        # Контейнер для основной информации
        profile_frame = QFrame()
        profile_frame.setObjectName("profileFrame")
        profile_layout = QVBoxLayout(profile_frame)
        profile_layout.setContentsMargins(20, 20, 20, 20)
        profile_layout.setSpacing(15)

        # Заголовок информации
        info_title = QLabel("Основная информация")
        info_title.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        info_title.setStyleSheet(title_style)
        profile_layout.addWidget(info_title)

        # Поля информации
        self.username_label = QLabel("Имя пользователя: загрузка...")
        self.username_label.setFont(QFont('Montserrat', 14))
        self.username_label.setStyleSheet(info_label_style)

        self.role_label = QLabel("Роль: загрузка...")
        self.role_label.setFont(QFont('Montserrat', 14))
        self.role_label.setStyleSheet(info_label_style)

        self.reg_date_label = QLabel("Дата регистрации: загрузка...")
        self.reg_date_label.setFont(QFont('Montserrat', 14))
        self.reg_date_label.setStyleSheet(info_label_style)

        profile_layout.addWidget(self.username_label)
        profile_layout.addWidget(self.role_label)
        profile_layout.addWidget(self.reg_date_label)

        # Кнопка обновления данных
        update_btn = QPushButton("Обновить данные")
        update_btn.setObjectName("refreshButton")
        update_btn.clicked.connect(self.show_update_dialog)
        profile_layout.addWidget(update_btn, alignment=Qt.AlignmentFlag.AlignLeft)

        layout.addWidget(profile_frame)

        # Создаем контейнер для двух колонок (заказы и возвраты)
        columns_container = QWidget()
        columns_layout = QHBoxLayout(columns_container)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(20)

        # Колонка заказов
        orders_column = QFrame()
        orders_column.setObjectName("profileFrame")
        orders_column_layout = QVBoxLayout(orders_column)
        orders_column_layout.setContentsMargins(20, 20, 20, 20)
        orders_column_layout.setSpacing(15)

        # Заголовок заказов
        orders_title = QLabel("Ваши заказы")
        orders_title.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        orders_title.setStyleSheet(title_style)
        orders_column_layout.addWidget(orders_title)

        # Scroll area для заказов
        self.orders_scroll = QScrollArea()
        self.orders_scroll.setWidgetResizable(True)
        self.orders_scroll.setStyleSheet("border: none; background: transparent;")

        self.orders_container = QWidget()
        self.orders_container_layout = QVBoxLayout(self.orders_container)
        self.orders_container_layout.setContentsMargins(0, 0, 0, 0)
        self.orders_container_layout.setSpacing(15)

        self.orders_scroll.setWidget(self.orders_container)
        orders_column_layout.addWidget(self.orders_scroll)

        # Placeholder на случай отсутствия заказов
        self.no_orders_label = QLabel("У вас пока нет заказов")
        self.no_orders_label.setFont(QFont('Montserrat', 14))
        self.no_orders_label.setStyleSheet(info_label_style)
        self.no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.orders_container_layout.addWidget(self.no_orders_label)

        columns_layout.addWidget(orders_column, stretch=1)  # Растягиваем на всю доступную ширину

        # Колонка возвратов
        returns_column = QFrame()
        returns_column.setObjectName("profileFrame")
        returns_column_layout = QVBoxLayout(returns_column)
        returns_column_layout.setContentsMargins(20, 20, 20, 20)
        returns_column_layout.setSpacing(15)

        # Заголовок возвратов
        returns_title = QLabel("Ваши возвраты")
        returns_title.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        returns_title.setStyleSheet(title_style)
        returns_column_layout.addWidget(returns_title)

        # Scroll area для возвратов
        self.returns_scroll = QScrollArea()
        self.returns_scroll.setWidgetResizable(True)
        self.returns_scroll.setStyleSheet("border: none; background: transparent;")

        self.returns_container = QWidget()
        self.returns_container_layout = QVBoxLayout(self.returns_container)
        self.returns_container_layout.setContentsMargins(0, 0, 0, 0)
        self.returns_container_layout.setSpacing(15)

        self.returns_scroll.setWidget(self.returns_container)
        returns_column_layout.addWidget(self.returns_scroll)

        # Placeholder на случай отсутствия возвратов
        self.no_returns_label = QLabel("У вас пока нет возвратов")
        self.no_returns_label.setFont(QFont('Montserrat', 14))
        self.no_returns_label.setStyleSheet(info_label_style)
        self.no_returns_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.returns_container_layout.addWidget(self.no_returns_label)

        columns_layout.addWidget(returns_column, stretch=1)  # Растягиваем на всю доступную ширину

        layout.addWidget(columns_container)
        layout.addStretch()

        # Загружаем данные профиля и возвратов
        self.load_profile_data()
        self.fetch_returns()

        return page

    def update_user_data(self, dialog):
        username = self.new_username.text().strip()
        password = self.new_password.text()
        confirm = self.confirm_password.text()

        if password and password != confirm:
            self.update_status.setText("Пароли не совпадают")
            self.update_status.setStyleSheet("color: #ff5555;")
            return

        data = {}
        if username:
            data["username"] = username
        if password:
            data["password"] = password

        if not data:
            self.update_status.setText("Введите новые данные для обновления")
            self.update_status.setStyleSheet("color: #ff5555;")
            return

        try:
            response = requests.put(
                f"http://127.0.0.1:8000/users/{self.user_id}",
                json=data,
                headers={"Content-Type": "application/json"}  # Добавляем заголовок
            )

            if response.status_code == 200:
                self.update_status.setText("Данные успешно обновлены")
                self.update_status.setStyleSheet("color: #55ff55;")
                QTimer.singleShot(1500, dialog.close)
                self.load_profile_data()
            else:
                error_msg = f"Ошибка {response.status_code}: {response.text}"
                self.update_status.setText(error_msg)
                self.update_status.setStyleSheet("color: #ff5555;")
        except requests.exceptions.RequestException as e:
            self.update_status.setText(f"Ошибка соединения: {str(e)}")
            self.update_status.setStyleSheet("color: #ff5555;")

    def show_update_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Обновление данных")
        dialog.setFixedSize(400, 300)

        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        title = QLabel("Обновление данных пользователя")
        title.setFont(QFont('Montserrat', 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #d4af37;")
        layout.addWidget(title)

        # Поля для ввода
        self.new_username = QLineEdit()
        self.new_username.setPlaceholderText("Новый никнейм")

        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Новый пароль")
        self.new_password.setEchoMode(QLineEdit.Password)

        self.confirm_password = QLineEdit()
        self.confirm_password.setPlaceholderText("Подтвердите пароль")
        self.confirm_password.setEchoMode(QLineEdit.Password)

        # Кнопка обновления
        update_btn = QPushButton("Обновить")
        update_btn.setObjectName("updateButton")
        update_btn.clicked.connect(lambda: self.update_user_data(dialog))

        # Сообщение о статусе
        self.update_status = QLabel()
        self.update_status.setWordWrap(True)

        # Добавляем элементы
        for widget in [self.new_username, self.new_password, self.confirm_password, update_btn, self.update_status]:
            layout.addWidget(widget)

        dialog.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 4px;
                background: #333;
                color: white;
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

        dialog.exec()

    def load_profile_data(self):
        try:
            # Загрузка данных пользователя
            user_response = requests.get(f"{self.api_thread.base_url}/users/{self.user_id}")
            if user_response.status_code == 200:
                user_data = user_response.json()
                self.username_label.setText(f"Имя пользователя: {user_data.get('username', 'Неизвестно')}")
                self.role_label.setText(f"Роль: {user_data.get('role', 'Неизвестно')}")

                # Форматирование даты
                created_at = user_data.get('created_at', '')
                if created_at:
                    try:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                        self.reg_date_label.setText(f"Дата регистрации: {formatted_date}")
                    except ValueError:
                        self.reg_date_label.setText(f"Дата регистрации: {created_at}")
                else:
                    self.reg_date_label.setText("Дата регистрации: Неизвестно")
            else:
                self.username_label.setText("Имя пользователя: ошибка загрузки")
                self.role_label.setText("Роль: ошибка загрузки")
                self.reg_date_label.setText("Дата регистрации: ошибка загрузки")

            # Загрузка заказов пользователя
            orders_response = requests.get(f"{self.api_thread.base_url}/orders/client/{self.user_id}")
            if orders_response.status_code == 200:
                orders = orders_response.json()
                self.display_orders(orders)
            else:
                # Создаем новый no_orders_label при ошибке
                self.no_orders_label = QLabel("Ошибка загрузки заказов")
                self.no_orders_label.setFont(QFont('Montserrat', 14))
                self.no_orders_label.setStyleSheet("color: #ff5555;")
                self.no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.orders_container_layout.addWidget(self.no_orders_label)

        except requests.exceptions.RequestException as e:
            print(f"Ошибка загрузки данных профиля: {str(e)}")
            # Создаем новый no_orders_label при ошибке соединения
            self.no_orders_label = QLabel("Нет соединения с сервером")
            self.no_orders_label.setFont(QFont('Montserrat', 14))
            self.no_orders_label.setStyleSheet("color: #ff5555;")
            self.no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.orders_container_layout.addWidget(self.no_orders_label)

    def display_orders(self, orders):
        # Очищаем контейнер заказов
        while self.orders_container_layout.count():
            item = self.orders_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not orders:
            # Создаем новый no_orders_label, если заказов нет
            self.no_orders_label = QLabel("У вас пока нет заказов")
            self.no_orders_label.setFont(QFont('Montserrat', 14))
            self.no_orders_label.setStyleSheet("color: white;")
            self.no_orders_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.orders_container_layout.addWidget(self.no_orders_label)
            return

        # Если есть заказы, no_orders_label не нужен
        if hasattr(self, 'no_orders_label'):
            del self.no_orders_label

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
                    self.show_order_details(order_data)

                return handler

            order_frame.mousePressEvent = make_click_handler(order)

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

            # Статус заказа
            status_label = QLabel(f"Статус: {order.get('status', 'Неизвестен')}")
            status_label.setFont(QFont('Montserrat', 12))

            # Цвет статуса в зависимости от состояния
            status = order.get('status', '').lower()
            if 'доставлен' in status or 'завершен' in status:
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

            self.orders_container_layout.addWidget(order_frame)

        # Добавляем растягивающий элемент в конец
        self.orders_container_layout.addStretch()

    def show_order_details(self, order_data):
        # Получаем детали заказа с сервера
        order_details = self.api_thread.fetch_order_details(self.user_id, order_data['order_id'])

        if order_details:
            # Создаем и показываем диалоговое окно с деталями
            dialog = OrderDetailDialog(order_details, self)
            dialog.exec()
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить детали заказа")

    def show_profile_page(self):
        self.content_stack.setCurrentWidget(self.profile_page)

    def fetch_returns(self):
        try:
            response = requests.get(f"{self.api_thread.base_url}/returns/get/by-client/{self.user_id}")
            if response.status_code == 200:
                returns = response.json()
                self.display_returns(returns)
            else:
                print(f"Error fetching returns: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching returns: {e}")

    def display_returns(self, returns):
        # Очищаем контейнер возвратов
        while self.returns_container_layout.count():
            item = self.returns_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not returns:
            self.no_returns_label = QLabel("У вас пока нет возвратов")
            self.no_returns_label.setFont(QFont('Montserrat', 14))
            self.no_returns_label.setStyleSheet("color: white;")
            self.no_returns_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.returns_container_layout.addWidget(self.no_returns_label)
            return

        # Скрываем placeholder, если есть возвраты
        if hasattr(self, 'no_returns_label') and self.no_returns_label:
            self.no_returns_label.hide()

        for return_item in returns:
            return_frame = QFrame()
            return_frame.setObjectName("returnFrame")
            return_frame.setStyleSheet("""
                #returnFrame {
                    border: 1px solid #444;
                    border-radius: 8px;
                }
                #returnFrame:hover {
                    background-color: #252525;
                    border-color: #555;
                    cursor: pointer;
                }
            """)

            return_layout = QVBoxLayout(return_frame)
            return_layout.setContentsMargins(15, 15, 15, 15)
            return_layout.setSpacing(10)

            # Верхняя строка с номером возврата и датой
            top_row = QHBoxLayout()

            return_id_label = QLabel(f"Возврат #{return_item.get('return_id', 'N/A')}")
            return_id_label.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
            return_id_label.setStyleSheet("color: #d4af37;")

            # Форматирование даты возврата
            return_date = return_item.get('return_date', '')
            if return_date:
                try:
                    dt = datetime.fromisoformat(return_date.replace('Z', '+00:00'))
                    formatted_date = dt.strftime("%d.%m.%Y %H:%M")
                    date_text = formatted_date
                except ValueError:
                    date_text = return_date
            else:
                date_text = "Дата неизвестна"

            date_label = QLabel(date_text)
            date_label.setFont(QFont('Montserrat', 12))
            date_label.setStyleSheet("color: #aaaaaa;")

            top_row.addWidget(return_id_label)
            top_row.addStretch()
            top_row.addWidget(date_label)

            return_layout.addLayout(top_row)

            # Статус возврата
            status_label = QLabel(f"Статус: {return_item.get('status', 'Неизвестен')}")
            status_label.setFont(QFont('Montserrat', 12))

            # Цвет статуса в зависимости от состояния
            status = return_item.get('status', '').lower()
            if 'завершен' in status or 'успешно' in status:
                status_label.setStyleSheet("color: #55ff55;")
            elif 'отменен' in status or 'отклонен' in status:
                status_label.setStyleSheet("color: #ff5555;")
            elif 'обработк' in status or 'ожидан' in status:
                status_label.setStyleSheet("color: #ffff55;")
            else:
                status_label.setStyleSheet("color: white;")

            return_layout.addWidget(status_label)

            # Описание возврата
            description_label = QLabel(f"Описание: {return_item.get('description', 'Нет описания')}")
            description_label.setFont(QFont('Montserrat', 12))
            description_label.setStyleSheet("color: white;")
            description_label.setWordWrap(True)

            return_layout.addWidget(description_label)

            self.returns_container_layout.addWidget(return_frame)

        # Добавляем растягивающий элемент в конец
        self.returns_container_layout.addStretch()

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
            #productFrame {
                background: transparent;
                border: 1px solid #333;
                border-radius: 10px;
            }
            #productFrame:hover {
                background: #252525;
                border-color: #444;
            }
            #filterButton {
                background-color: #333;
                color: white;
                padding: 8px 16px;
                border-radius: 15px;
                font-size: 14px;
            }
            #filterButton:hover {
                background-color: #444;
            }
            #filterButton:checked {
                background-color: #d4af37;
                color: black;
            }
            #cartButton {
                background-color: #d4af37;
                color: #d4af37;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                min-width: 120px;
            }
            #cartButton:hover {
                background-color: #d4af37;
            }
            #cartButton:pressed {
                background-color: #b79530;
            }
            #cartItemFrame {
                background-color: #252525;
                border-radius: 8px;
            }
            #detailButton {
                background-color: white;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            #detailButton:hover {
                background-color: #f5f5f5;
            }
            #detailButton:pressed {
                background-color: #e0e0e0;
            }
            #removeButton {
                background-color: transparent;
                border-radius: 50%;
                padding: 8px;
            }
            #removeButton:hover {
                background-color: #444;
            }
            #checkoutButton {
                background-color: #d4af37;
                color: black;
                font-size: 16px;
                border-radius: 5px;
            }
            #checkoutButton:hover {
                background-color: #f0d87c;
            }
            #clearCartButton {
                background-color: #333;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            #clearCartButton:hover {
                background-color: #444;
            }
            #profileFrame {
                background-color: #252525;
                border-radius: 10px;
                border: 1px solid #333;
                margin-bottom: 20px;
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
