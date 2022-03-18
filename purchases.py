from datetime import date
from mysql.connector import connect, Error
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *
from edit_tables import EditTables
from mysql_dbconf import get_db_params


class Purchases(EditTables):
    def __init__(self, params):
        super().__init__(params)
        self.dt_edit = QDateEdit(date.today())
        self.dt_edit.dateChanged.connect(self.date_changed)

        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Дата: "))
        hbox.addWidget(self.dt_edit)
        hbox.addStretch()
        self.vbox.insertLayout(0, hbox)
        self.date_changed()

        self.table.setColumnWidth(2, 20)  # здесь будет кнопка

        # Таблица ресурсов. Отсюда будем выбирать в QComboBox
        query = """
        SELECT DISTINCT resources.* from resources, costs
        WHERE resources.id = costs.res1_id 
        AND NOT EXISTS (SELECT * FROM costs WHERE resources.id = costs.res2_id) 
        """
        self.lst_res = self.read_table(query)
        zlst = list(zip(*self.lst_res))  # транспонируем список
        self.ids = zlst[0]  # коды
        self.names = zlst[1]  # наименования
        self.show()

    def add_row(self):
        i = self.table.rowCount()
        self.table.insertRow(i)
        self.table.setCurrentCell(i, 1)
        # вставляем кнопку
        self.insert_btn_choice(i, 2)
        return i

    def insert_btn_choice(self, i, j):
        self.btn_choice = QPushButton('...')
        self.btn_choice.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                      QtWidgets.QSizePolicy.Maximum)
        self.table.setCellWidget(i, j, self.btn_choice)
        self.btn_choice.clicked.connect(self.btn_choice_clicked)

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

    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)

    def save_table(self):
        db_config = get_db_params()
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            # удаляем в таблице inventory ресурсы
            date_ = self.dt_edit.date().toPyDate()  # дата
            delete_query = f"""
            DELETE FROM inventory WHERE date_purchase = DATE('{str(date_)}')
            """
            cursor.execute(delete_query)
            conn.commit()

            # записываем данные
            rowcount = self.table.rowCount()
            items = []
            for i in range(rowcount):
                code_res = int(self.table.item(i, 0).text())  # код ресурса
                count = self.table.item(i, 4).text() if self.table.item(i, 4) else 0
                price = self.table.item(i, 5).text() if self.table.item(i, 5) else 0
                item_i = (code_res, count, price, date_)
                items.append(item_i)

            insert_query = """
            INSERT INTO inventory (id, count, price, date_purchase) VALUES (%s,%s,%s,%s)
            """
            cursor.executemany(insert_query, items)
            conn.commit()
            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    def date_changed(self):
        date_ = self.dt_edit.date().toPyDate()
        # заполняем QTableWidget ресурсами, купленными за date_, если они есть
        query = f"""
        SELECT resources.id, resources.name, resources.measure, 
        inventory.count, inventory.price
        FROM inventory, resources 
        WHERE inventory.id = resources.id 
        AND inventory.date_purchase = DATE('{str(date_)}')
        """
        result = self.read_table(query)
        # заполняем QWidgetTable
        self.table.setRowCount(0)
        for row in result:
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(row[0]))) # код
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(str(row[1]))) # наименование
            self.insert_btn_choice(i, 2)
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem(str(row[2]))) # ед. изм.
            self.table.setItem(i, 4, QTableWidgetItem(str(row[3]))) # кол-во
            self.table.setItem(i, 5, QTableWidgetItem(str(row[4]))) # цена
