from datetime import date
from mysql.connector import connect, Error
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QDateEdit,
                             QLabel,
                             QHBoxLayout)
from edit_tables import EditTables
from mysql_dbconf import get_db_params

class ShiftRep(EditTables):
    def __init__(self,params):
        super().__init__(params)
        self.dt_edit = QDateEdit(date.today())
        self.dt_edit.dateChanged.connect(self.date_changed)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Дата: "))
        hbox.addWidget(self.dt_edit)
        hbox.addStretch()
        self.vbox.insertLayout(0,hbox)
        self.date_changed()

        self.table.setColumnWidth(2, 20)    # здесь будет кнопка

        # Таблица ресурсов. Отсюда будем всё выбирать
        query = "SELECT * FROM resources WHERE price < 0.01 ORDER BY name"
        lst_prod = self.read_table(query)
        zlst = list(zip(*lst_prod))  # транспонируем список
        self.ids = zlst[0]      # здесь коды
        self.names = zlst[1]    # здесь наименования
        self.show()

    def date_changed(self):
        date_ = self.dt_edit.date().toPyDate()
        # заполняем QTableWidget изделиями за текущую дату, если они есть
        result = self.get_prods(date_)
        # заполняем таблицу
        self.table.setRowCount(0)
        for row in result:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0])))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1])))
            self.insert_btn_choice(i, 2)
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row[2])))

    def get_prods(self,date_):
        query = f"""
               SELECT resources.id, resources.name, shiftrep.count 
               FROM resources, shiftrep 
               WHERE shiftrep.daterep = DATE('{str(date_)}')
               AND resources.id = shiftrep.id
               """
        return self.read_table(query)

    def add_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.insert_btn_choice(row_count,2)

    def change_res_box(self):
        i = self.table.currentRow()
        j = self.names.index(self.res_box.currentText())
        self.table.setItem(i,0,QtWidgets.QTableWidgetItem(str(self.ids[j])))
        self.table.setItem(i,1,QtWidgets.QTableWidgetItem(self.res_box.currentText()))

    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)

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
            str_today = str(self.dt_edit.date().toPyDate())
            query = f"""
            DELETE FROM shiftrep WHERE daterep = DATE('{str_today}')
            """
            cursor.execute(query)
            conn.commit()
            # записываем
            items = []
            for i in range(row_count):
                id_ = int(self.table.item(i, 0).text())
                item_i = (str_today,id_)
                item = self.table.item(i, 3)
                item_i += (float(item.text()),) if item else (0.0,)
                items.append(item_i)

            query = "INSERT INTO shiftrep (daterep, id, count) VALUES (DATE(%s),%s,%s)"
            cursor.executemany(query,items)
            conn.commit()

            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    def change_prod(self,lst_prod):
        pass



