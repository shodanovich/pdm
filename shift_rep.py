from datetime import date
from mysql.connector import connect, Error
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import (QWidget, QPushButton, QDateEdit,
                             QComboBox,QLabel,
                             QHBoxLayout, QVBoxLayout, QMessageBox)
from edit_tables import EditTables
#from costs import btn_choice_clicked
from mysql_dbconf_io import get_db_params

class ShiftRep(EditTables):
    def __init__(self,params):
        super().__init__(params)
        self.dt_edit = QDateEdit(date.today())
        today = self.dt_edit.date().toPyDate()
        self.dt_edit.dateChanged.connect(lambda: self.date_changed(today))

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Дата: "))
        hbox.addWidget(self.dt_edit)
        hbox.addStretch()
        self.vbox.insertLayout(0,hbox)
        self.date_changed(self.dt_edit.date().toPyDate())

        self.table.setColumnWidth(2, 20)    # здесь будет кнопка

        # Таблица ресурсов. Отсюда будем всё выбирать
        query = "SELECT * FROM resources WHERE price < 0.01 ORDER BY name"
        lst_prod = self.read_table(query)
        zlst = list(zip(*lst_prod))  # транспонируем список
        self.names = zlst[1]  # здесь наименования

    def date_changed(self,today):
        """
        заполняем QTableWidget изделиями за текущую дату, если они есть
        :param today:
        """
        result = self.get_prods(today)
        # заполняем таблицу
        self.table.setRowCount(0)
        for row in result:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1])))
            self.insert_btn_choice(i, 2)
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row[2])))

    def get_prods(self,today):
        query = """
               SELECT resources.id, resources.name, shiftrep.count 
               FROM resources, shiftrep 
               WHERE shiftrep.daterep = DATE(%s)
               AND resources.id = shiftrep.id
               """
        return self.read_table(query,(str(today),))

    def add_row(self):
        super().add_row()
        self.insert_btn_choice(self.table.row_count,2)

    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)

    def insert_btn_choice(self,i,j):
        self.btn_choice = QPushButton('...')
        self.btn_choice.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                      QtWidgets.QSizePolicy.Maximum)
        self.table.setCellWidget(i, j, self.btn_choice)
        self.btn_choice.clicked.connect(self.btn_choice_clicked)

    def insert_to_table(self,lst_table,tab):
       pass

    def save_table(self):
        """сохраняем QTableWidget в MySql"""
        row_count = self.table.rowCount()
        column_count = self.table.columnCount()
        db_config = get_db_params()
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            ### --- заменяем таблицу ---
            query = """
            DELETE FROM shiftrep WHERE daterep = DATE(%s)
            AND id IN (%s)
            """
            str_today = str(self.dt_edit.date().toPyDate())
            query_params = (str_today,)
            # ids QTableWidget
            ids = tuple(int(self.table.item(i, 0).text()) for i in range(row_count))
            query_params += ids
            cursor.execute(query, query_params)
            conn.commit()
            # формируем список значений для вставки
            items = []
            for i in range(row_count):
                item_i = [str_today, self.table.item(i, 0).text(), \
                         self.table.item(i, 2).text()]
                items += item_i

            query = "INSERT INTO shiftrep (daterep, id, count) VALUES (%s,%s,%s)"
            cursor.execute(query,items)
            conn.commit()

            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    def change_prod(self,lst_prod):
        pass

    def change_res_box(self):
        pass

