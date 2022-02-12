import decimal
from mysql.connector import connect, Error
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout, QMessageBox,
                             QComboBox, QListWidget)
from edit_tables import EditTables
from edit_tables import read_table
from mysql_dbconf_io import get_db_params

class Costs(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.initUI()
    def initUI(self):
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("Нормативы затрат на изделие")
        # выбираем изделие
        self.prod_box = QComboBox()
        # выбираем ресурсы
        self.resources = read_table('resources') #список с данными из БД ресурсов
        for res in self.resources:
            self.prod_box.addItem(res[1])
        self.prod_box.activated.connect(self.change_prod)
        tpl = self.code_measure(self.prod_box.currentText())
        self.measure_label = QtWidgets.QLabel('1 ' + tpl[1])
        # таблица ресурсов
        self.table = QtWidgets.QTableWidget()
        tab = self.table
        tab.setColumnCount(4)
        tab.setRowCount(0)
        # Устанавливаем заголовки таблицы
        header_labels = ('Ресурс',' ','Ед. изм.','Расход на ед.')
        tab.setHorizontalHeaderLabels(header_labels)
        # первую колонку растягиваем по содержимому
        header = tab.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.table.setColumnWidth(1,20)
        # управляющие кнопки
        btn_insert = QPushButton("Добавить (Ins)")
        btn_insert.setShortcut('Ins')
        btn_insert.clicked.connect(self.add_record)
        btn_delete = QPushButton('Удалить (Del)')
        btn_delete.setShortcut('Del')
        btn_delete.clicked.connect(self.delete_record)
        btn_save = QPushButton('Сохранить (Ctrl+S)')
        btn_save.setShortcut('ctrl+s')
        btn_save.clicked.connect(lambda: self.save_table())  # слот с параметром
        btn_exit = QPushButton('Выйти (Esc)')
        btn_exit.setShortcut('Esc')
        btn_exit.clicked.connect(lambda: self.out())
        # строка состояния
        self.info_label = QtWidgets.QLabel()
        # размещение
        # изделие
        hprodbox = QHBoxLayout()
        hprodbox.addWidget(self.prod_box)
        hprodbox.addWidget(self.measure_label)
        # кнопки
        hbtnbox = QHBoxLayout()
        hbtnbox.addStretch(1)
        hbtnbox.addWidget(btn_insert)
        hbtnbox.addWidget(btn_delete)
        hbtnbox.addWidget(btn_save)
        hbtnbox.addWidget(btn_exit)

        # главный бокс
        vbox = QVBoxLayout()
        vbox.addLayout(hprodbox)
        vbox.addWidget(tab)
        vbox.addLayout(hbtnbox)
        vbox.addWidget(self.info_label)

        self.setLayout(vbox)
        self.show()

    def change_prod(self):
        txt = self.prod_box.currentText()
        tpl = self.code_measure(txt)        #(код, единица измерения)
        self.measure_label.setText('1 ' + tpl[1]) # единица измерения
        code = tpl[0]   # код изделия
        # ищем в базе нормативных затрат затраты по коду выбранного издения
        db_config = get_db_params()
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            # читаем затраты для данного издения
            select_query = """
            SELECT resources.name, resources.measure, 
            costs.cost FROM resources, costs 
            WHERE costs.res1_id = resources.id 
            AND costs.res2_id = 
            """ + str(code)
            cursor.execute(select_query)
            result = cursor.fetchall()
            conn.commit()

        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

        self.table.setRowCount(0)
        for row in result:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i,0,QtWidgets.QTableWidgetItem(row[0]))
            # вставляем во второй столбец кнопку
            self.btn_choice = QPushButton('...')
            self.btn_choice.clicked.connect(self.btn_choice_clicked)
            self.btn_choice.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                          QtWidgets.QSizePolicy.Maximum)
            self.table.setCellWidget(i, 1, self.btn_choice)
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(row[1]))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row[2])))

    # по нажатию кнопки (...)
    # вставляем в 0 столбец таблицы QComboBox
    def btn_choice_clicked(self):
        self.res_box = QComboBox()
        self.res_box.currentTextChanged.connect(self.change_res_box)

        rowPosition = self.table.currentRow()
        self.table.setCellWidget(rowPosition, 0, self.res_box)
        for res in self.resources:
            if res[1] == self.prod_box.currentText():
                continue
            for row in range(0,rowPosition):
                if res[1]==self.table.item(row,0).text():
                    break
            else:
                self.res_box.addItem(res[1])

    # добавляем строку в QTableWidget
    def add_record(self):
        rowPosition = self.table.rowCount()
        self.table.insertRow(rowPosition)
        self.table.setCurrentCell(rowPosition,0)
        item = self.table.currentItem()
        # вставляем во второй столбец кнопку
        self.btn_choice = QPushButton('...')
        self.btn_choice.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                               QtWidgets.QSizePolicy.Maximum)
        self.table.setCellWidget(rowPosition,1,self.btn_choice)
        self.btn_choice.clicked.connect(self.btn_choice_clicked)

    # удаляем строку из QTableWidget
    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)

    # обработка выбора в QComboBox
    def change_res_box(self):
        rowPosition = self.table.currentRow()
        txt = self.res_box.currentText()  # выбранный текст в QComboBox
        # устанавливаем его в ячейке таблицы
        self.table.setItem(rowPosition, 0, QtWidgets.QTableWidgetItem(txt))
        # ищем в списке resources единицу измерения и устанавливаем ее в QTableWidget
        tpl = self.code_measure(txt)
        self.table.setItem(rowPosition, 2, QtWidgets.QTableWidgetItem(tpl[1]))

    # поиск кода и единицы измерения по наименованию ресурса
    def code_measure(self,txt):
        for res in self.resources:
            if res[1] == txt:
                tpl = (res[0],res[2],)
                return tpl

    # сохраняем QTableWidget в MySql
    def save_table(self):
        db_config = get_db_params()
        params = get_db_params(filename='config.ini', section='costs')
        table_name = params['tablename']
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            tpl = self.code_measure(self.prod_box.currentText())
            code_prod = tpl[0]  # код изделия (полуфабриката)
            # удаляем в базе затраты для данного изделия
            delete_query = """
            DELETE FROM costs
            WHERE res2_id =
            """ + str(code_prod)
            cursor.execute(delete_query)
            conn.commit()

            rowcount = self.table.rowCount()
            # записываем данные
            items = []
            for i in range(rowcount):
                item_i = ()
                item = self.table.item(i, 0)
                if item != None:
                    tpl = self.code_measure(item.text())
                    item_i += (tpl[0],)     # код ресурса
                    item_i += (code_prod,)
                    item = self.table.item(i,3)
                    if item != None:
                        item_i += (float(item.text()),)
                items.append(item_i)

            fieldNames = params['fieldnames']
            insert_db_query = ("INSERT INTO " + table_name + " (" +
                               fieldNames + ") VALUES " +
                               params['picture'])
            cursor.executemany(insert_db_query, items)
            conn.commit()
            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    def out(self):
        self.save_table()
        self.close()

    # горячие клавиши. Переопределяем метод keyPressEvent
    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if event.key() == QtCore.Qt.Key_Insert:  # Insert
            self.add_record()  # Добавить запись
        elif event.key() == QtCore.Qt.Key_Delete:  # Delete
            self.delete_record()  # Удалить запись
        elif event.key() == QtCore.Qt.Key_F10:  # сохранить таблицу в БД
            self.save_table()
        elif event.key() == QtCore.Qt.Key_Escape:  # выход
            self.close()
