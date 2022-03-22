from mysql.connector import connect, Error
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QPushButton,
                             QHBoxLayout, QVBoxLayout,
                             QComboBox)
from edit_tables import EditTables
from commons import *

class Costs(EditTables):
    def __init__(self, params):
        super().__init__(params)
        # параметры таблицы
        self.setGeometry(300, 300, 600, 400)
        table_params = params["table_params"]

        # выбор изделия
        self.prod_box = QComboBox()
        # выбираем изделия из базы (строка запроса с нулевой ценой)
        query = "SELECT * from resources"
        self.lst_prod = read_table(query)
        # и заполняем prod_box
        for prod in self.lst_prod:
            self.prod_box.addItem(prod[1])
        # обработка при выборе
        self.prod_box.activated.connect(lambda: self.change_prod(self.lst_prod))

        # начальное значение единицы измерения для изделия
        self.measure_label = QtWidgets.QLabel('1 ' + self.lst_prod[0][2]
                                              if self.lst_prod else '')

        # Таблица ресурсов. Отсюда будем всё выбирать
        query = "SELECT * FROM resources ORDER BY name"
        self.lst_res = read_table(query)
        zlst = list(zip(*self.lst_res))  # транспонируем список
        self.names = zlst[1]        # здесь наименования

        # местный QTableWidget
        # вторую колонку растягиваем по содержимому
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.setColumnWidth(0,20)     # код
        self.table.setColumnWidth(2, 20)    # ед. изм.
        # вносим начальные данные в таблицу
        self.change_prod(self.lst_prod)

        # размещение
        # вставляем в первую строчку изделие
        hprodbox = QHBoxLayout()
        hprodbox.addWidget(self.prod_box)
        hprodbox.addWidget(self.measure_label)
        self.vbox.insertLayout(0,hprodbox)

        self.show()


    # выбрали изделие, собираем и добавляем затраты на него
    def change_prod(self,lst_prod):
        if not lst_prod:
            return
        # единица измерения в метке на форме
        i = self.prod_box.currentIndex()
        self.measure_label.setText('1 ' + lst_prod[i][2])
        # затраты на изделие
        code = lst_prod[i][0]   # код изделия
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

        # заполняем QTableWidget
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

            # обработка выбора в QComboBox

    def change_res_box(self):
        lst = self.lst_res
        row_position = self.table.currentRow()
        txt = self.res_box.currentText()  # выбранный текст в QComboBox
        row = [x for x in lst if x[1] == txt]
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

    # удаляем строку из QTableWidget
    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)

    # сохраняем QTableWidget в MySql
    def save_table(self):
        i = self.prod_box.currentIndex()
        code_prod = self.lst_prod[i][0]
        db_config = get_db_params()
        try:
            # удаляем в базе затраты для данного изделия
            conn = connect(**db_config)
            cursor = conn.cursor()
            delete_query = f"DELETE FROM costs WHERE res2_id = {str(code_prod)}"
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

            insert_db_query = "INSERT INTO costs (res1_id, res2_id, cost) VALUES (%s,%s,%s)"
            cursor.executemany(insert_db_query, items)
            conn.commit()
            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    def out(self):  # при выходе сохраняем QWidgetTable
        self.save_table()
        self.close()



