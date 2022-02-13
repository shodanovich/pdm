from mysql.connector import connect, Error
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout, QMessageBox)
from mysql_dbconf_io import get_db_params

class Sou(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.initUI()
        self.initUI()
    def initUI(self):
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("Сменный отчет участка")
        # дата
        self.date = QtWidgets.QDateEdit(self)
        # таблица
        self.table = QtWidgets.QTableWidget()
        tab = self.table
        tab.setColumnCount(3)
        tab.setRowCount(0)
        # Устанавливаем заголовки таблицы
        header_labels = ('Изделие', ' ', 'Количество')
        tab.setHorizontalHeaderLabels(header_labels)
        # первую колонку растягиваем по содержимому
        header = tab.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.setColumnWidth(1, 20)    # колонка для кнопки
        # управляющие кнопки
        btn_insert = QPushButton("Добавить (Ins)")
        btn_insert.setShortcut('Ins')
        btn_insert.clicked.connect(self.add_row)
        btn_delete = QPushButton('Удалить (Del)')
        btn_delete.setShortcut('Del')
        btn_delete.clicked.connect(self.delete_row)
        btn_save = QPushButton('Сохранить (Ctrl+S)')
        btn_save.setShortcut('ctrl+s')
        btn_save.clicked.connect(self.save_table)  # слот с параметром
        btn_exit = QPushButton('Выйти (Esc)')
        btn_exit.setShortcut('Esc')
        btn_exit.clicked.connect(self.out)
        # строка состояния
        self.info_label = QtWidgets.QLabel()
        # размещение
        # дата слева
        hdate = QHBoxLayout()
        hdate.addWidget(self.date)
        hdate.addStretch(1)
        # кнопки по горизонтали
        hbtnbox = QHBoxLayout()
        hbtnbox.addStretch(1)
        hbtnbox.addWidget(btn_insert)
        hbtnbox.addWidget(btn_delete)
        hbtnbox.addWidget(btn_save)
        hbtnbox.addWidget(btn_exit)

        # главный бокс
        vbox = QVBoxLayout()
        vbox.addLayout(hdate)
        vbox.addWidget(tab)
        vbox.addLayout(hbtnbox)
        vbox.addWidget(self.info_label)

        self.setLayout(vbox)
        self.show()

    def add_row(self):
        pass

    def delete_row(self):
        pass

    def save_table(self):
        pass

    def out(self):
        pass
