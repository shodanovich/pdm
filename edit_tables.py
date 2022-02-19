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
        tab = self.table = QtWidgets.QTableWidget(self)
        # Устанавливаем заголовки таблицы
        headers = params['columnnames']
        headers_list = [x.strip() for x in headers.split(',')]
        column_count = len(headers_list)  # количество колонок
        tab.setColumnCount(column_count)
        tab.setHorizontalHeaderLabels(headers_list) # заголовки столбцов
        tab.setRowCount(0)  # количество строк = 0

        # первая колонка с кодом имеет фиксированную ширину
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
        select_query = ("SELECT "+params['fieldnames']+" FROM " + table_name)
        orderFields = params.get('orderfields')
        if orderFields: select_query += (" ORDER BY " + orderFields)
        lst_table = read_table(table_name, select_query)
        # вставляем данные из БД в QTableWidget
        i = 0  # на случай, если в базе пусто
        tab.blockSignals(True)  # блокируем сигналы в QWidgetTable
        for i,row in enumerate(lst_table):
            tab.insertRow(i)
            for j in range(0,column_count):
                tab.setItem(i, j, QtWidgets.QTableWidgetItem(str(row[j])))
        tab.blockSignals(False)  # разблокируем сигналы

        ### --- строка состояния ---
        self.info_label = QtWidgets.QLabel()
        self.info_label.setText("Прочитано записей: {}".format(i))

        ### --- кнопки ---
        btn_insert = QPushButton("Добавить (Ins)")
        btn_insert.setShortcut('Ins')
        btn_insert.clicked.connect(self.add_record)
        btn_delete = QPushButton('Удалить (Shifr+Del)')
        btn_delete.setShortcut('Shift+Del')
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
        row_count = self.table.rowCount()
        # собираем коды ресурсов QTableWidget в кортеж
        ids = tuple(int(self.table.item(i,0).text()) for i in range(row_count))
        self.table.insertRow(row_count)
        # добавляем код
        ids1 = tuple(i for i in range(row_count) if not(i in ids))
        id = ids1[0] if ids1 else row_count
        self.table.setItem(row_count,0,QtWidgets.QTableWidgetItem(str(id)))
        self.table.setCurrentCell(row_count,1)

    # удаляем строку из QTableWidget
    def delete_record(self):
        rowPosition = self.table.currentRow()
        if not self.table.item(rowPosition,1):
            self.table.removeRow(rowPosition)
            return
        # проверяем ссылки на этот ресурс в таблице нормативов
        db_config = get_db_params()
        id = self.table.item(rowPosition,0).text() # код ресурса
        name = self.table.item(rowPosition,1).text()
        select_query = """
        SELECT * from costs WHERE (res1_id=%s) OR (res2_id=%s) 
        """
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(select_query,(id,id,))
            if cursor.fetchall():
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
            # формируем список значений для вставки
            row_count = self.table.rowCount()
            column_count = self.table.columnCount()
            items = [[self.table.item(i, j).text() for j in range(column_count)] \
                     for i in range(row_count)]
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

    # проверка на уникальность
    def check_unique(self,col_list=[]):
        tab = self.table
        current_column = tab.currentColumn()
        current_row = tab.currentRow()
        current_text = tab.currentItem().text()

        not_unique = [row for row in range(tab.rowCount()) if(
                row != current_row
                and tab.currentItem()
                and tab.item(row, current_column).text() == current_text
                and current_column in col_list)]
        if not_unique:
            QMessageBox.warning(self, "Поле не уникально!",
                                "Запись не будет добавлена в таблицу.")
            tab.setRowCount(tab.rowCount()-1)

    def out(self,table_name):
        self.save_table(table_name)
        self.close()

# читаем данные из БД в QTableWidget
def read_table(table_name,query):
    db_config = get_db_params()
    try:
        with connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            result = cursor.fetchall()  # данных немного, читаем все
    except Error as e:
        print("Error: ", e)
    finally:
        return result


