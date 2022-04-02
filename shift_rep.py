from datetime import date
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QDateEdit,
                             QLabel,
                             QHBoxLayout,
                             QMessageBox)
from edit_tables import EditTables
from commons import *


class ShiftRep(EditTables):
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

        # Таблица изделий. Отсюда будем выбирать в QComboBox
        query = """
        SELECT id, name FROM resources
        WHERE NOT EXISTS(
            SELECT res1_id from costs
            WHERE res1_id = resources.id
            )
        """
        lst_prod = read_table(query)
        zlst = list(zip(*lst_prod))  # транспонируем список
        self.ids = zlst[0]  # коды
        self.names = zlst[1]  # наименования
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

    def get_prods(self, date_):
        query = f"""
               SELECT resources.id, resources.name, shiftrep.count 
               FROM resources, shiftrep 
               WHERE shiftrep.daterep = DATE('{str(date_)}')
               AND resources.id = shiftrep.id
               """
        return read_table(query)

    def add_row(self):
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        self.insert_btn_choice(row_count, 2)

    def change_res_box(self):
        i = self.table.currentRow()
        j = self.names.index(self.res_box.currentText())
        self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(str(self.ids[j])))
        self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(self.res_box.currentText()))

    def delete_record(self):
        rowPosition = self.table.currentRow()
        self.table.removeRow(rowPosition)

    def insert_to_table(self, lst_table, tab):
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
                item_i = (str_today, id_)
                item = self.table.item(i, 3)
                item_i += (float(item.text()),) if item else (0.0,)
                items.append(item_i)

            query = "INSERT INTO shiftrep (daterep, id, count) VALUES (DATE(%s),%s,%s)"
            cursor.executemany(query, items)
            conn.commit()

            # удаляем списание
            query = f"""
            DELETE FROM inventory 
            WHERE date_purchase = DATE('{str_today}')
            AND count < 0
            """
            cursor.execute(query)
            conn.commit()
            ### списываем материалы по методу FIFO
            # ресурсы
            # 1. Затраты на ед.:
            zitems =  list(zip(*items))  # транспонируем список
            ids = zitems[1]     # коды
            costs = get_costs(ids) # затраты на ед.
            # 2. Умножаем на объемы производства и проставляем дату списания
            cost2 = []
            for row in costs:
                for val in items:
                    if row[1] == val[1]:
                        row1 = [row[0], row[2]*val[2], 0, val[0]]
                        cost2.append(row1)
            zcost2 = list(zip(*cost2))
            ids = str(zcost2[0])  # в строку
            # 3. Проставляем цены списания
            query = "SET SQL_MODE = ''"
            cursor.execute(query)
            query = f"""
            SELECT inventory.id, SUM(inventory.count) AS quantity, inventory.price, 
            inventory.date_purchase, resources.name, resources.measure, resources.typeres
            FROM inventory, resources
            WHERE inventory.id IN {ids}
            AND inventory.id = resources.id
            GROUP BY id, price 
            """
            cursor.execute(query)
            lst_inv = cursor.fetchall()
            conn.commit()
            cost3 = []
            lst_inv.sort(key=lambda date: date[3])  # сортируем по дате
            lst_inv.sort(key=lambda res_id: res_id[0])  # сортируем по коду
            for cost in cost2:  # затраты ресурсов для списания
                i = -1
                while i < len(lst_inv): # запасы
                    i += 1
                    if i == len(lst_inv):
                        break
                    if lst_inv[i][6] == 'р':    # работников не списываем
                        continue
                    if cost[0] == lst_inv[i][0]:
                        if lst_inv[i][1] >= cost[1]:   # строка запасов больше списания
                            row = (cost[0], -cost[1], lst_inv[i][2], cost[3])
                            cost3.append(row)
                            break
                        # строка запасов меньше списания
                        while cost[1] > 0:
                            if cost[0] == lst_inv[i][0]:
                                cost[1] -= lst_inv[i][1]
                                price = lst_inv[i][2]
                                date = cost[3]
                                row = [cost[0], -lst_inv[i][1], price, date]
                                cost3.append(row)
                                i += 1
                            elif cost[0] != lst_inv[i][0] and cost[1] > 0:
                                msg = QMessageBox()
                                msg.setWindowTitle("Недостаточно запасов")
                                msg.setText("Недостаточно запасов ресурса " +
                                            lst_inv[i][4] + ". Требуется ещё "+
                                            str(cost[1])) + lst_inv[i][5]
                                msg.setIcon(QMessageBox.Warning)
                                msg.exec_()
                                return

            # 3. Списываем
            query = '''
            INSERT INTO inventory (id, count, price, date_purchase)
            VALUES (%s, %s, %s, DATE(%s))
            '''
            cursor.executemany(query, cost3)
            conn.commit()

            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()

    def change_prod(self, lst_prod):
        pass
