from mysql.connector import connect, Error
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout, QMessageBox)
from mysql_dbconf_io import get_db_params

class EditTables(QWidget):
    def __init__(self, parent=None):
        super().__init__()

    def build(self,table_name):
        self.setGeometry(300, 300, 600, 400)
        # читаем параметры таблицы из config.ini (модуль mysql_dbconfig_io)
        # в config.ini собраны параметры таблицы в MySql и в QTableWidget
        params = get_db_params(filename='config.ini', section=table_name)
        self.setWindowTitle(params['title'])    # заголовок окна
        ### --- таблица ---
        self.table = QtWidgets.QTableWidget(self)
        tab = self.table
        # Устанавливаем заголовки таблицы
        headers = params['columnnames']
        headers_list = [x.strip() for x in headers.split(',')]
        columncount = len(headers_list)  # количество колонок
        tab.setColumnCount(columncount)
        tab.setHorizontalHeaderLabels(headers_list) # заголовки столбцов
        tab.setRowCount(0)  # количество строк = 0

        # первая колонка имеет фиксированную ширину
        tab.setColumnWidth(0,40)
        # вторую колонку растягиваем по содержимому
        header = tab.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        # событие изменения значения в клетке
        unique = params['unique']   #колонки, в которых значение д. б. уникальным
        unique_list = [int(x.strip()) for x in unique.split(',')]
        # будет проверка на уникальность
        tab.itemChanged.connect(lambda: self.check_unique(unique_list))
        # читаем данные из БД
        lst_table = read_table(table_name)
        # вставляем данные из БД в QTableWidget
        self.table.blockSignals(True)  # блокируем сигналы в QWidgetTable
        i = 0
        for row in lst_table:
            self.table.insertRow(i)
            for j in range(0,columncount):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(str(row[j])))
            i += 1
        self.table.blockSignals(False)  # разблокируем сигналы

        ### --- строка состояния ---
        self.info_label = QtWidgets.QLabel()
        self.info_label.setText("Прочитано записей: {}".format(i))

        ### --- кнопки ---
        btn_insert = QPushButton("Добавить (Ins)")
        btn_insert.setShortcut('Ins')
        btn_insert.clicked.connect(self.add_record)
        btn_delete = QPushButton('Удалить (Del)')
        btn_delete.setShortcut('Del')
        btn_delete.clicked.connect(self.delete_record)
        btn_save = QPushButton('Сохранить (Ctrl+S)')
        btn_save.setShortcut('ctrl+s')
        btn_save.clicked.connect(lambda: self.save_table(table_name)) #слот с параметром
        btn_exit = QPushButton('Выйти (Esc)')
        btn_exit.setShortcut('Esc')
        btn_exit.clicked.connect(lambda: self.out(table_name))

        ### --- расположение виджетов в окне ---
        # кнопки располагаем по горизонтали:
        hbtnbox = QHBoxLayout()
        hbtnbox.addStretch(1)
        hbtnbox.addWidget(btn_insert)
        hbtnbox.addWidget(btn_delete)
        hbtnbox.addWidget(btn_save)
        hbtnbox.addWidget(btn_exit)
        # сначала таблица, потом кнопки, внизу статус:
        vbox = QVBoxLayout()
        vbox.addWidget(tab)

        vbox.addLayout(hbtnbox)
        vbox.addWidget(self.info_label)
        # помещаем всё в QWidget
        self.setLayout(vbox)

        self.show()

    # добавляем пустую строку в QTableWidget
    def add_record(self):
        rowCount = self.table.rowCount()
        # собираем коды QTableWidget в кортеж
        ids = ()
        for i in range(rowCount):
            ids += (int(self.table.item(i,0).text()),)
        self.table.insertRow(rowCount)
        # добавляем код
        for i in range(rowCount):
            if not (i in ids):
                id = i  # если есть, то заполняем код
                break
        else:
            id = rowCount
        self.table.setItem(rowCount,0,QtWidgets.QTableWidgetItem(str(id)))
        self.table.setCurrentCell(rowCount,1)

    # удаляем строку из QTableWidget
    def delete_record(self):
        rowPosition = self.table.currentRow()
        if self.table.item(rowPosition,1) == None:
            self.table.removeRow(rowPosition)
            return
        # проверяем ссылки на этот ресурс в таблице нормативов
        db_config = get_db_params()
        id = self.table.item(rowPosition,0).text() # код ресурса
        name = self.table.item(rowPosition,1).text()
        select_query = """
        SELECT * from costs WHERE (res1_id=%s) OR (res2_id=%s) 
        """
        tpl_id = (id,)
        tpl_id += (id,)
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(select_query,tpl_id)
            result = cursor.fetchall()
            if len(result) != 0:
                txt_msg = ('Для удаления "' + name +
                           '" необходимо удалить все ссылки на этот ' +
                           'ресурс в файле нормативов')
                mBox = QtWidgets.QMessageBox
                mBox.information(self, "Ошибка удаления", txt_msg)
                return
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()
        self.table.removeRow(rowPosition)

    # сохраняем QTableWidget в MySql
    def save_table(self,table_name):
        db_config = get_db_params()
        params = get_db_params(filename='config.ini', section=table_name)
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            ### --- заменяем таблицу ---
            # --- сначала всё удаляем ---
            cursor.execute("DELETE from "+table_name)
            conn.commit()
            # --- вставляем в таблицу---
            # формируем список значений для вставки
            items = []
            rowcount = self.table.rowCount()
            columnCount = self.table.columnCount()
            for i in range(rowcount):
                item_i = ()
                for j in range(columnCount):
                    item = self.table.item(i, j)
                    if item != None:
                        req = item.text()
                        if req == '':
                            req = '0'
                    else:
                        req = '0'
                    item_i += (req,)
                items += (item_i,)
            # вставляем items в таблицу
            insert_query = ("INSERT " + table_name + "("+params['fieldnames']+")"
                            + " VALUES " + params['picture'])
            cursor.executemany(insert_query,items)
            conn.commit()

            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    # поиск кода и единицы измерения по наименованию ресурса
    def code_measure(self, txt):
        for res in self.resources:
            if res[1] == txt:
                tpl = (res[0], res[2],)
                return tpl

    # проверка на уникальность
    def check_unique(self,col_list=[]):
        tab = self.table
        currentColumn = tab.currentColumn()
        try:
            if currentColumn in col_list:
                if tab.currentItem() != None:
                    currenttext = tab.currentItem().text()
                    currentrow = tab.currentRow()
                    for row in range(tab.rowCount()):
                        if row != currentrow:
                            if tab.item(row, currentColumn).text() == currenttext:
                                QMessageBox.warning(self, "Поле не уникально!",
                                                    "Запись не будет добавлена в таблицу.")
                                #tab.setCurrentCell(tab.rowCount()-2,0)
                                tab.setRowCount(tab.rowCount()-1)
        except Error as e:
            print(e)

    def out(self,table_name):
        self.save_table(table_name)
        self.close()

# читаем данные из БД в QTableWidget
def read_table(table_name):
    db_config = get_db_params()
    params = get_db_params(filename='config.ini', section=table_name)
    try:
        conn = connect(**db_config)
        cursor = conn.cursor()
        # строка запроса
        select_query = ("SELECT "+params['fieldnames']+" FROM " + table_name)
        orderFields = params.get('orderfields')
        if orderFields != None:
            select_query += (" ORDER BY " + orderFields)
        cursor.execute(select_query)
        result = cursor.fetchall()  # данных немного, читаем все
    except Error as e:
        print("Error: ", e)
    finally:
        conn.close()
        return result


