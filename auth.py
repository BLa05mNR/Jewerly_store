# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'auth.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QSplitter, QVBoxLayout, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(425, 425)
        Form.setStyleSheet(u"\n"
"    background-color: #1a1a1a;  /* \u0422\u0451\u043c\u043d\u044b\u0439 \u0444\u043e\u043d */\n"
"    color: white;\n"
"    font-family: \"Segoe UI\";\n"
"")
        self.verticalLayout = QVBoxLayout(Form)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(Form)
        self.label.setObjectName(u"label")
        self.label.setStyleSheet(u"QLabel {\n"
"    font-size: 26px;\n"
"    color: #d4af37; /* \u0417\u043e\u043b\u043e\u0442\u043e\u0439 */\n"
"    font-weight: bold;\n"
"    padding: 10px;\n"
"}")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.verticalLayout.addWidget(self.label)

        self.splitter = QSplitter(Form)
        self.splitter.setObjectName(u"splitter")
        self.splitter.setOrientation(Qt.Orientation.Vertical)
        self.lineEdit = QLineEdit(self.splitter)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setStyleSheet(u"QLineEdit {\n"
"    background-color: #2a2a2a;\n"
"    border: 1px solid #d4af37;\n"
"    border-radius: 4px;\n"
"    padding: 8px;\n"
"    color: white;\n"
"    font-size: 14px;\n"
"    min-width: 250px;\n"
"    transition: border-color 0.3s ease-in-out;\n"
"}\n"
"QLineEdit:focus {\n"
"    border: 1px solid #f0d87c;\n"
"}\n"
"")
        self.splitter.addWidget(self.lineEdit)
        self.lineEdit_2 = QLineEdit(self.splitter)
        self.lineEdit_2.setObjectName(u"lineEdit_2")
        self.lineEdit_2.setStyleSheet(u"QLineEdit {\n"
"    background-color: #2a2a2a;\n"
"    border: 1px solid #d4af37;\n"
"    border-radius: 4px;\n"
"    padding: 8px;\n"
"    color: white;\n"
"    font-size: 14px;\n"
"    min-width: 250px;\n"
"}\n"
"\n"
"QLineEdit:focus {\n"
"    border: 1px solid #f0d87c;  /* \u042f\u0440\u043a\u043e\u0435 \u0437\u043e\u043b\u043e\u0442\u043e \u043f\u0440\u0438 \u0444\u043e\u043a\u0443\u0441\u0435 */\n"
"}")
        self.splitter.addWidget(self.lineEdit_2)
        self.pushButton = QPushButton(self.splitter)
        self.pushButton.setObjectName(u"pushButton")
        self.pushButton.setStyleSheet(u"QPushButton {\n"
"    background-color: #d4af37;  /* \u0417\u043e\u043b\u043e\u0442\u043e\u0439 */\n"
"    color: black;\n"
"    border: none;\n"
"    padding: 10px 20px;\n"
"    font-size: 16px;\n"
"    border-radius: 4px;\n"
"    min-width: 120px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #f0d87c;  /* \u0421\u0432\u0435\u0442\u043b\u0435\u0435 \u043f\u0440\u0438 \u043d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0438 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #b79530;  /* \u0422\u0435\u043c\u043d\u0435\u0435 \u043f\u0440\u0438 \u043d\u0430\u0436\u0430\u0442\u0438\u0438 */\n"
"}")
        self.splitter.addWidget(self.pushButton)
        self.pushButton_2 = QPushButton(self.splitter)
        self.pushButton_2.setObjectName(u"pushButton_2")
        self.pushButton_2.setStyleSheet(u"QPushButton {\n"
"    background-color: #d4af37;  /* \u0417\u043e\u043b\u043e\u0442\u043e\u0439 */\n"
"    color: black;\n"
"    border: none;\n"
"    padding: 10px 20px;\n"
"    font-size: 16px;\n"
"    border-radius: 4px;\n"
"    min-width: 120px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"    background-color: #f0d87c;  /* \u0421\u0432\u0435\u0442\u043b\u0435\u0435 \u043f\u0440\u0438 \u043d\u0430\u0432\u0435\u0434\u0435\u043d\u0438\u0438 */\n"
"}\n"
"\n"
"QPushButton:pressed {\n"
"    background-color: #b79530;  /* \u0422\u0435\u043c\u043d\u0435\u0435 \u043f\u0440\u0438 \u043d\u0430\u0436\u0430\u0442\u0438\u0438 */\n"
"}")
        self.splitter.addWidget(self.pushButton_2)

        self.verticalLayout.addWidget(self.splitter)


        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label.setText(QCoreApplication.translate("Form", u"\u0412\u043e\u0439\u0434\u0438\u0442\u0435 \u0432 \u0441\u0432\u043e\u0439 \u0430\u043a\u043a\u0430\u0443\u043d\u0442 \n"
"\u0438 \u043d\u0430\u0447\u043d\u0438\u0442\u0435 \u043f\u0440\u044f\u043c\u043e \u0441\u0435\u0439\u0447\u0430\u0441!", None))
        self.lineEdit.setPlaceholderText(QCoreApplication.translate("Form", u"\u0432\u0430\u0448 \u043d\u0438\u043a\u043d\u0435\u0439\u043c", None))
        self.lineEdit_2.setPlaceholderText(QCoreApplication.translate("Form", u"\u043f\u0430\u0440\u043e\u043b\u044c", None))
        self.pushButton.setText(QCoreApplication.translate("Form", u"\u0412\u043e\u0439\u0442\u0438", None))
        self.pushButton_2.setText(QCoreApplication.translate("Form", u"\u0417\u0430\u0440\u0435\u0433\u0438\u0441\u0442\u0440\u0438\u0440\u043e\u0432\u0430\u0442\u044c\u0441\u044f", None))
    # retranslateUi

