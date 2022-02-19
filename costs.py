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
        # параметры таблицы
        params = get_db_params(filename='config.ini', section='resources')

        self.prod_box = QComboBox()
        # выбираем изделие из базы (строка запроса с нулевой ценой)
        select_query = ("SELECT * FROM resources WHERE price < 0.01")
        orderFields = params.get('orderfields')
        select_query += " ORDER BY " + orderFields if orderFields else ""
        # читаем таблицу ресурсов (изделия)
        lst_prod = read_table(params['tablename'],select_query)

        # заполняем prod_box
        for prod in lst_prod:
            self.prod_box.addItem(prod[1])
        # начальное значение единицы измерения для изделия
        self.measure_label = QtWidgets.QLabel()
        self.measure_label.setText('1 ' + lst_prod[0][2])
        # обработка при выборе
        self.prod_box.activated.connect(lambda: self.change_prod(lst_prod))

        # таблица ресурсов
        query = "SELECT * FROM resources ORDER BY name"
        self.lst_res = read_table('resources', query)
        zlst = list(zip(*self.lst_res))  # транспонируем список
        self.names = zlst[1]        # здесь наименования

        self.table = QtWidgets.QTableWidget()
        tab = self.table
        tab.setColumnCount(5)
        tab.setRowCount(0)
        # Устанавливаем заголовки таблицы
        tab.setHorizontalHeaderLabels(('Код','Ресурс',' ','Ед. изм.','Расход на ед.'))
        header = tab.horizontalHeader()
        # вторую колонку растягиваем по содержимому
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.setColumnWidth(0,20)     # код
        self.table.setColumnWidth(2, 20)    # ед. изм.
        # вносим начальные данные в таблицу
        self.change_prod(lst_prod)

        # управляющие кнопки
        btn_insert = QPushButton("Добавить (Ins)")
        btn_insert.setShortcut('Ins')
        btn_insert.clicked.connect(self.add_row)
        btn_delete = QPushButton('Удалить (Del)')
        btn_delete.setShortcut('Del')
        btn_delete.clicked.connect(self.delete_record)
        btn_save = QPushButton('Сохранить (Ctrl+S)')
        btn_save.setShortcut('ctrl+s')

        btn_save.clicked.connect(lambda: self.save_table(lst_prod))
        btn_exit = QPushButton('Выйти (Esc)')
        btn_exit.setShortcut('Esc')
        btn_exit.clicked.connect(lambda: self.out(lst_prod))
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

    # выбрали изделие, собираем и добавляем затраты на него
    def change_prod(self,lst):
        # единица измерения в метке на форме
        i = self.prod_box.currentIndex()
        self.measure_label.setText('1 ' + lst[i][2])
        # затраты на изделие
        code = lst[i][0]   # код изделия
        # ищем в базе нормативных затрат затраты по коду выбранного изделия
        db_config = get_db_params()
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            # читаем затраты для данного издения
            select_query = """
            SELECT resources.id, resources.name, resources.measure, 
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

        # заполняем таблицу
        self.table.setRowCount(0)
        for row in result:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setCurrentCell(i, 0)
            self.insert_btn_choice(i, 2)
            self.table.setItem(i,0,QtWidgets.QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1])))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row[2])))
            self.table.setItem(i, 4, QtWidgets.QTableWidgetItem(str(row[3])))

    # по нажатию кнопки (...)
    # вставляем в 1 столбец таблицы QComboBox со значениями
    def btn_choice_clicked(self, names):
        # вставляем в текущую строку QComboBox()
        row_position = self.table.currentRow()
        self.res_box = QComboBox()
        self.table.setCellWidget(row_position, 1, self.res_box)

        self.res_box.activated.connect(self.change_res_box)

        # формируем список для выбора
        # nonames - этих наименований не должно быть в списке для выбора
        nonames = [self.prod_box.currentText()]
        nonames += [self.table.item(row, 1).text() for row in range(row_position)]
        fnames = [x for x in names if x not in nonames]
        self.res_box.addItems(fnames)

    # обработка выбора в QComboBox
    def change_res_box(self):
        lst = self.lst_res
        row_position = self.table.currentRow()
        txt = self.res_box.currentText()  # выбранный текст в QComboBox
        row = [x for x in lst if x[1]==txt]
        id, measure = row[0][0], row[0][2]
        # устанавливаем в таблице код, наименование и ед. изм
        self.table.setItem(row_position, 0, QtWidgets.QTableWidgetItem(str(id)))
        self.table.setItem(row_position, 1, QtWidgets.QTableWidgetItem(txt))
        self.table.setItem(row_position, 3, QtWidgets.QTableWidgetItem(measure))

    # добавляем строку в QTableWidget
    def add_row(self):
        i = self.table.rowCount()
        self.table.insertRow(i)
        self.table.setCurrentCell(i,1)
        # вставляем кнопку
        self.insert_btn_choice(i,2)
        return i

    def insert_btn_choice(self,i,j):
        self.btn_choice = QPushButton('...')
        self.btn_choice.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                      QtWidgets.QSizePolicy.Maximum)
        self.table.setCellWidget(i, j, self.btn_choice)
        self.btn_choice.clicked.connect(lambda: self.btn_choice_clicked(self.names))

    # удаляем строку из QTableWidget
    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)


    # сохраняем QTableWidget в MySql
    def save_table(self,lst_prod):
        i = self.prod_box.currentIndex()
        code_prod = lst_prod[i][0]
        db_config = get_db_params()
        params = get_db_params(filename='config.ini', section='costs')
        table_name = params['tablename']
        try:
            # удаляем в базе затраты для данного изделия
            conn = connect(**db_config)
            cursor = conn.cursor()
            delete_query = "DELETE FROM costs WHERE res2_id = " + str(code_prod)
            cursor.execute(delete_query)
            conn.commit()

            # записываем данные
            rowcount = self.table.rowCount()
            items = []
            for i in range(rowcount):
                code_res = int(self.table.item(i, 0).text())    # код ресурса
                item_i = (code_res,code_prod)
                item = self.table.item(i,4)         # затраты
                item_i += (float(item.text()),) if item else (0.0,)
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

    def out(self,lst_prod):
        self.save_table(lst_prod)
        self.close()

