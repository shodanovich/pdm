from mysql.connector import connect, Error
from PyQt5 import QtWidgets
from edit_tables import EditTables
from mysql_dbconf import get_db_params

class EditRes(EditTables):
    """    местная специфика    """
    def delete_record(self):
        # удаляем строку из QTableWidget
        rowPosition = self.table.currentRow()
        if not self.table.item(rowPosition, 1):
            self.table.removeRow(rowPosition)
            return
        # проверяем ссылки на этот ресурс в таблице нормативов
        db_config = get_db_params()
        id = self.table.item(rowPosition, 0).text()  # код ресурса
        name = self.table.item(rowPosition, 1).text()
        select_query = """
            SELECT * from costs WHERE (res1_id=%s) OR (res2_id=%s) 
            """
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            cursor.execute(select_query, (id, id,))
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

    def save_table(self):
        """сохраняем QTableWidget в MySql"""
        db_config = get_db_params()
        try:
            conn = connect(**db_config)
            cursor = conn.cursor()
            ### --- заменяем таблицу ---
            cursor.execute("DELETE FROM resources")
            conn.commit()
            # формируем список значений для вставки
            row_count = self.table.rowCount()
            column_count = self.table.columnCount()
            if row_count and column_count:
                items = []
                for i in range(row_count):
                    items_i = ()
                    for j in range(column_count):
                        item = self.table.item(i, j)
                        if item:
                            items_i += (item.text(),)
                        else:
                            items_i += ('',)
                    items += (items_i,)

            save_query = """
            INSERT INTO resources (id, name, measure, typeres) 
            VALUES (%s,%s,%s,%s)
            """
            cursor.executemany(save_query,items)
            conn.commit()

            self.info_label.setText("Сохранено.")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()


