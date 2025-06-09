import sys
import requests
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLabel, QFrame,
                               QScrollArea, QStackedWidget, QSizePolicy, QDialog,
                               QGridLayout, QMessageBox)
from PySide6.QtCore import Qt, QSize, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QPixmap, QImage


class ApiThread(QThread):
    products_loaded = Signal(list)
    image_loaded = Signal(int, QPixmap)

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


class ProductDetailDialog(QDialog):
    def __init__(self, product, pixmap, parent=None):
        super().__init__(parent)
        self.product = product
        self.parent = parent
        self.setWindowTitle(product["name"])
        self.setFixedSize(600, 500)

        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        # Product image
        image_label = QLabel()
        image_label.setPixmap(pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio))
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Product details
        details_layout = QVBoxLayout()

        name_label = QLabel(product["name"])
        name_label.setFont(QFont('Montserrat', 18, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #d4af37; background: transparent;")

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
        main_layout.addWidget(image_label)
        main_layout.addLayout(details_layout)

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
            #closeButton {
                background-color: #333;
                color: white;
                font-size: 16px;
                border-radius: 5px;
            }
            #closeButton:hover {
                background-color: #444;
            }
        """)

    def add_to_cart(self):
        """Метод для добавления товара в корзину без дополнительных действий"""
        if hasattr(self.parent, 'add_to_cart'):
            self.parent.add_to_cart(self.product)


class JewelryStoreApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Гусарочка")
        self.setMinimumSize(1280, 900)
        self.cart = []  # Список товаров в корзине

        # API Thread
        self.api_thread = ApiThread()
        self.api_thread.products_loaded.connect(self.display_products)
        self.api_thread.image_loaded.connect(self.update_product_image)

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

        sidebar_layout.addWidget(self.home_btn)
        sidebar_layout.addWidget(self.catalog_btn)
        sidebar_layout.addWidget(self.cart_btn)
        sidebar_layout.addStretch()

        # Logout button
        logout_btn = QPushButton("Выйти")
        logout_btn.setObjectName("logoutButton")
        sidebar_layout.addWidget(logout_btn)

        layout.addWidget(sidebar)

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
        filters = QHBoxLayout()
        filters.setSpacing(10)

        filter_btns = ["Все", "Кольца", "Серьги", "Подвески", "Браслеты"]
        for text in filter_btns:
            btn = QPushButton(text)
            btn.setObjectName("filterButton")
            filters.addWidget(btn)

        layout.addLayout(filters)

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

        checkout_btn = QPushButton("Оформить заказ")
        checkout_btn.setObjectName("checkoutButton")
        checkout_btn.setFixedHeight(50)

        layout.addWidget(self.total_label)
        layout.addWidget(checkout_btn)

        return page

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
        total = sum(p["price"] for p in self.cart)
        self.total_label.setText(f"Итого: {total:,} ₽".replace(",", " "))

        # Update cart button in sidebar
        self.cart_btn.setText(f"Корзина ({len(self.cart)})")

        # Show cart page
        self.content_stack.setCurrentIndex(2)

    def create_cart_item(self, product):
        frame = QFrame()
        frame.setObjectName("cartItemFrame")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Image
        image = QLabel()
        image.setObjectName(f"cart_image_{product['image_id']}")
        image.setFixedSize(80, 80)
        image.setStyleSheet("background: #2a2a2a; border-radius: 8px;")

        # Product info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)

        name = QLabel(product["name"])
        name.setFont(QFont('Montserrat', 14))

        details = QLabel(f"{product['material']} · {product['weight']}г")
        details.setFont(QFont('Montserrat', 12))
        details.setStyleSheet("color: #aaaaaa;")

        price = QLabel(f"{product['price']:,} ₽".replace(",", " "))
        price.setFont(QFont('Montserrat', 14, QFont.Weight.Bold))
        price.setStyleSheet("color: #d4af37;")

        info_layout.addWidget(name)
        info_layout.addWidget(details)
        info_layout.addWidget(price)

        # Remove button
        remove_btn = QPushButton()
        remove_btn.setIcon(QIcon("icons/trash.png"))
        remove_btn.setIconSize(QSize(24, 24))
        remove_btn.setObjectName("removeButton")
        remove_btn.clicked.connect(lambda: self.remove_from_cart(product))

        layout.addWidget(image)
        layout.addLayout(info_layout)
        layout.addStretch()
        layout.addWidget(remove_btn)

        # Load image if available
        for label in self.findChildren(QLabel):
            if label.objectName() == f"image_{product['image_id']}":
                if label.pixmap():
                    image.setPixmap(label.pixmap().scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio))

        return frame

    def add_to_cart(self, product):
        """Просто добавляем товар в корзину без обновления страницы"""
        self.cart.append(product)
        # Обновляем только счетчик в боковом меню
        self.cart_btn.setText(f"Корзина ({len(self.cart)})")

    def remove_from_cart(self, product):
        self.cart = [p for p in self.cart if p["product_id"] != product["product_id"]]
        self.update_cart_page()

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
                200, 200,
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

    # Try to set Montserrat font
    font = QFont("Montserrat")
    app.setFont(font)

    window = JewelryStoreApp()
    window.show()

    sys.exit(app.exec())