import sys
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QLabel, QPushButton, QScrollArea, QDialog, QFrame,
                               QGridLayout, QTextEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt, Signal, QSize, QTimer
from PySide6.QtGui import QPixmap, QFont, QColor


class Product:
    def __init__(self, data):
        self.name = data["name"]
        self.article = data["article"]
        self.type = data["type"]
        self.material = data["material"]
        self.insert_type = data["insert_type"]
        self.weight = data["weight"]
        self.price = data["price"]
        self.stock_quantity = data["stock_quantity"]
        self.image_id = data["image_id"]
        self.product_id = data["product_id"]
        self.image_url = f"http://127.0.0.1:8000/images/{self.image_id}"


class ProductCard(QFrame):
    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setup_ui()

    def setup_ui(self):
        self.setObjectName("ProductCard")
        self.setStyleSheet("""
            #ProductCard {
                background-color: #252525;
                border-radius: 8px;
                padding: 0;
                border: 1px solid #333;
            }
            QLabel {
                color: white;
                font-size: 14px;
                padding: 8px;
            }
            QLabel#title {
                font-size: 16px;
                font-weight: bold;
                padding-top: 0;
            }
            QLabel#price {
                color: #d4af37;
                font-size: 18px;
                font-weight: bold;
                padding-bottom: 12px;
            }
        """)
        self.setFixedSize(250, 320)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Изображение товара
        image_container = QWidget()
        image_container.setFixedHeight(200)
        image_container.setStyleSheet(
            "background-color: #1a1a1a; border-top-left-radius: 8px; border-top-right-radius: 8px;")
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(image_container)

        # Контейнер для текстовой информации
        text_container = QWidget()
        text_layout = QVBoxLayout(text_container)
        text_layout.setContentsMargins(12, 8, 12, 8)
        text_layout.setSpacing(4)

        # Название товара
        self.name_label = QLabel(self.product.name)
        self.name_label.setObjectName("title")
        self.name_label.setWordWrap(True)
        text_layout.addWidget(self.name_label)

        # Цена
        self.price_label = QLabel(f"{self.product.price:,} ₽".replace(",", " "))
        self.price_label.setObjectName("price")
        text_layout.addWidget(self.price_label)

        # Кнопка "Подробнее" с восстановленным дизайном
        self.detail_btn = QPushButton("Подробнее")
        self.detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f0d87c;
            }
            QPushButton:pressed {
                background-color: #b79530;
            }
        """)
        text_layout.addWidget(self.detail_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(text_container)
        layout.addStretch()

        self.load_image()

    def load_image(self):
        try:
            response = requests.get(self.product.image_url, stream=True)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_label.setPixmap(pixmap.scaled(
                    200, 200,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.set_placeholder_image()
        except:
            self.set_placeholder_image()

    def set_placeholder_image(self):
        pixmap = QPixmap(QSize(200, 200))
        pixmap.fill(QColor("#1a1a1a"))
        self.image_label.setPixmap(pixmap)


class ProductDialog(QDialog):
    add_to_cart = Signal(object)

    def __init__(self, product, parent=None):
        super().__init__(parent)
        self.product = product
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(self.product.name)
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLabel#title {
                font-size: 24px;
                color: #d4af37;
                font-weight: bold;
            }
            QLabel#price {
                font-size: 20px;
                color: #d4af37;
                font-weight: bold;
            }
            QTextEdit {
                background-color: #252525;
                color: white;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Изображение товара
        image_container = QWidget()
        image_container.setStyleSheet("background-color: #1a1a1a; border-radius: 8px;")
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(400, 400)
        image_layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(image_container, alignment=Qt.AlignmentFlag.AlignCenter)

        # Название товара
        self.title_label = QLabel(self.product.name)
        self.title_label.setObjectName("title")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        # Цена
        self.price_label = QLabel(f"{self.product.price:,} ₽".replace(",", " "))
        self.price_label.setObjectName("price")
        self.price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.price_label)

        # Детали
        details_text = QTextEdit()
        details_text.setReadOnly(True)
        details_text.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        details = [
            f"<b>Артикул:</b> {self.product.article}",
            f"<b>Тип:</b> {self.product.type}",
            f"<b>Материал:</b> {self.product.material}",
            f"<b>Вставка:</b> {self.product.insert_type}",
            f"<b>Вес:</b> {self.product.weight} г",
            f"<b>В наличии:</b> {self.product.stock_quantity} шт"
        ]
        details_text.setHtml("<br>".join(details))
        layout.addWidget(details_text)

        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)

        self.add_btn = QPushButton("Добавить в корзину")
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f0d87c;
            }
            QPushButton:pressed {
                background-color: #b79530;
            }
        """)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: white;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #444;
            }
            QPushButton:pressed {
                background-color: #222;
            }
        """)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.close_btn)
        layout.addLayout(buttons_layout)

        self.add_btn.clicked.connect(self.add_to_cart_clicked)
        self.close_btn.clicked.connect(self.close)

        self.load_image()

    def load_image(self):
        try:
            response = requests.get(self.product.image_url, stream=True)
            if response.status_code == 200:
                pixmap = QPixmap()
                pixmap.loadFromData(response.content)
                self.image_label.setPixmap(pixmap.scaled(
                    400, 400,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                ))
            else:
                self.set_placeholder_image()
        except:
            self.set_placeholder_image()

    def set_placeholder_image(self):
        pixmap = QPixmap(QSize(400, 400))
        pixmap.fill(QColor("#1a1a1a"))
        self.image_label.setPixmap(pixmap)

    def add_to_cart_clicked(self):
        self.add_to_cart.emit(self.product)
        self.close()


class CartDialog(QDialog):
    cart_cleared = Signal()

    def __init__(self, cart_items, parent=None):
        super().__init__(parent)
        self.cart_items = cart_items
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("Корзина")
        self.setMinimumSize(500, 600)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a1a;
                color: white;
                font-family: 'Segoe UI';
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QLabel#totalLabel {
                font-size: 18px;
                color: #d4af37;
                font-weight: bold;
            }
            QListWidget {
                background-color: #252525;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                font-size: 14px;
                color: white;
            }
            QListWidget::item {
                border-bottom: 1px solid #333;
                padding: 8px;
                color: white;
            }
            QListWidget::item:selected {
                background-color: #333;
                color: white;
            }
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f0d87c;
            }
            QPushButton:pressed {
                background-color: #b79530;
            }
            QPushButton#clearButton {
                background-color: #ff4d4d;
                color: white;
            }
            QPushButton#clearButton:hover {
                background-color: #ff6b6b;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Список товаров
        self.cart_list = QListWidget()
        self.cart_list.setAlternatingRowColors(True)
        self.update_cart_list()

        layout.addWidget(self.cart_list)

        # Итого
        self.total_label = QLabel()
        self.total_label.setObjectName("totalLabel")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.total_label)
        self.update_total()

        # Кнопки
        buttons_layout = QHBoxLayout()

        self.clear_btn = QPushButton("Очистить корзину")
        self.clear_btn.setObjectName("clearButton")
        self.clear_btn.clicked.connect(self.clear_cart)

        self.checkout_btn = QPushButton("Оформить заказ")
        self.checkout_btn.clicked.connect(self.checkout)

        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.close)

        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addWidget(self.checkout_btn)
        buttons_layout.addWidget(self.close_btn)

        layout.addLayout(buttons_layout)

    def update_cart_list(self):
        self.cart_list.clear()
        for item in self.cart_items:
            list_item = QListWidgetItem(f"{item.name} - {item.price:,} ₽".replace(",", " "))
            list_item.setData(Qt.ItemDataRole.UserRole, item)
            self.cart_list.addItem(list_item)

    def update_total(self):
        total = sum(item.price for item in self.cart_items)
        self.total_label.setText(f"Итого: {total:,} ₽".replace(",", " "))

    def clear_cart(self):
        self.cart_items.clear()
        self.update_cart_list()
        self.update_total()
        self.cart_cleared.emit()
        QMessageBox.information(self, "Корзина очищена", "Ваша корзина была очищена")

    def checkout(self):
        if len(self.cart_items) == 0:
            QMessageBox.warning(self, "Корзина пуста", "Ваша корзина пуста, добавьте товары перед оформлением заказа")
            return

        QMessageBox.information(self, "Заказ оформлен", "Ваш заказ успешно оформлен!")
        self.clear_cart()
        self.close()


class JewelryCatalog(QMainWindow):
    def __init__(self):
        super().__init__()
        self.products = []
        self.cart = []
        self.setup_ui()
        self.load_products()

    def setup_ui(self):
        self.setWindowTitle("Каталог ювелирных изделий")
        self.resize(1000, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1a1a1a;
                font-family: 'Segoe UI';
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QScrollBar:vertical {
                background: #252525;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #d4af37;
                min-height: 20px;
            }
            QWidget#scrollContent {
                background-color: #1a1a1a;
            }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Заголовок и кнопка корзины
        header_layout = QHBoxLayout()

        self.title_label = QLabel("Каталог ювелирных изделий")
        self.title_label.setStyleSheet("""
            QLabel {
                font-size: 28px;
                color: #d4af37;
                font-weight: bold;
            }
        """)

        self.cart_btn = QPushButton("Корзина")
        self.cart_btn.setStyleSheet("""
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 10px 20px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #f0d87c;
            }
            QPushButton:pressed {
                background-color: #b79530;
            }
        """)
        self.cart_btn.clicked.connect(self.show_cart)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.cart_btn, alignment=Qt.AlignmentFlag.AlignRight)

        main_layout.addLayout(header_layout)

        # Область с товарами
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.scroll_content = QWidget()
        self.scroll_content.setObjectName("scrollContent")
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Контейнер для товаров с сеткой
        self.products_container = QWidget()
        self.products_container.setStyleSheet("background-color: #1a1a1a;")
        self.grid_layout = QGridLayout(self.products_container)
        self.grid_layout.setHorizontalSpacing(20)
        self.grid_layout.setVerticalSpacing(20)
        self.grid_layout.setContentsMargins(0, 0, 20, 0)

        self.scroll_layout.addWidget(self.products_container)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)

        # Кнопка обновления
        self.refresh_btn = QPushButton("Обновить каталог")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 12px;
                font-size: 16px;
                border-radius: 4px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #f0d87c;
            }
            QPushButton:pressed {
                background-color: #b79530;
            }
        """)
        self.refresh_btn.clicked.connect(self.load_products)
        main_layout.addWidget(self.refresh_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        # Таймер для отложенного обновления
        self.resize_timer = QTimer()
        self.resize_timer.setSingleShot(True)
        self.resize_timer.timeout.connect(self.update_layout)

    def load_products(self):
        try:
            response = requests.get("http://127.0.0.1:8000/products/get/all/")
            if response.status_code == 200:
                self.products = [Product(data) for data in response.json()]
                self.update_layout()
                self.update_cart_button()
            else:
                self.show_error("Ошибка загрузки данных", f"Код ошибки: {response.status_code}")
        except Exception as e:
            self.show_error("Ошибка подключения", str(e))

    def update_layout(self):
        # Очищаем текущие товары
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget is not None:
                widget.setParent(None)

        # Рассчитываем количество колонок
        column_count = max(1, (self.width() - 60) // 270)

        # Добавляем товары в сетку
        for i, product in enumerate(self.products):
            card = ProductCard(product)
            card.detail_btn.clicked.connect(lambda _, p=product: self.show_product_details(p))
            self.grid_layout.addWidget(card, i // column_count, i % column_count)

    def resizeEvent(self, event):
        # Откладываем обновление на 100 мс после окончания изменения размера
        self.resize_timer.start(100)
        super().resizeEvent(event)

    def show_product_details(self, product):
        dialog = ProductDialog(product)
        dialog.add_to_cart.connect(self.add_to_cart)
        dialog.exec()

    def add_to_cart(self, product):
        self.cart.append(product)
        self.show_message("Товар добавлен", f"{product.name} добавлен в корзину")
        self.update_cart_button()

    def show_cart(self):
        if not self.cart:
            self.show_message("Корзина пуста", "Ваша корзина пока пуста")
            return

        dialog = CartDialog(self.cart, self)
        dialog.cart_cleared.connect(self.on_cart_cleared)
        dialog.exec()

    def on_cart_cleared(self):
        self.cart.clear()
        self.update_cart_button()

    def update_cart_button(self):
        count = len(self.cart)
        self.cart_btn.setText(f"Корзина ({count})" if count > 0 else "Корзина")

    def show_message(self, title, message):
        msg = QDialog(self)
        msg.setWindowTitle(title)
        msg.setFixedSize(300, 150)
        msg.setStyleSheet("""
            QDialog {
                background-color: #252525;
                color: white;
            }
            QLabel {
                font-size: 14px;
            }
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
                min-width: 80px;
            }
        """)

        layout = QVBoxLayout(msg)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("OK")
        btn.clicked.connect(msg.accept)

        layout.addWidget(label)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        msg.exec()

    def show_error(self, title, message):
        error = QDialog(self)
        error.setWindowTitle(title)
        error.setFixedSize(400, 200)
        error.setStyleSheet("""
            QDialog {
                background-color: #252525;
                color: white;
            }
            QLabel {
                font-size: 14px;
                color: #ff6b6b;
            }
            QPushButton {
                background-color: #d4af37;
                color: black;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 4px;
                min-width: 80px;
            }
        """)

        layout = QVBoxLayout(error)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        btn = QPushButton("Понятно")
        btn.clicked.connect(error.accept)

        layout.addWidget(label)
        layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)

        error.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    font = QFont("Segoe UI", 10)
    app.setFont(font)

    window = JewelryCatalog()
    window.show()
    sys.exit(app.exec())