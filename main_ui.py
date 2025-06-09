# -*- coding: utf-8 -*-
import sys
from PySide6.QtWidgets import QApplication
from UI.auth_window import AuthWindow

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # Установка шрифта
    font = app.font()
    font.setFamily("Segoe UI")
    app.setFont(font)

    window = AuthWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()