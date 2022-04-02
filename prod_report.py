from datetime import date
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import *
from commons import *

class ProdReport(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Отчет по производству, затратам и заработной плате')
        self.setGeometry(400,400,900,500)

        self.lst_costs = [] # для рекурсивной функции

        # размещаем даты, кнопку и QRadioButton в горизонтальном боксе
        self.date1 = QDateEdit(date.today())
        self.date2 = QDateEdit(date.today())
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(QLabel("Период с "))
        self.hbox.addWidget(self.date1)
        self.hbox.addWidget(QLabel(" по "))
        self.hbox.addWidget(self.date2)
        self.hbox.addStretch()
        # выбор вида отчета
        self.rb1 = QRadioButton("Заработная плата")
        self.rb2 = QRadioButton("Материалы")
        self.rb3 = QRadioButton("Полный отчет")
        self.rb3.setChecked(True)
        self.hbox.addWidget(self.rb1)
        self.hbox.addWidget(self.rb2)
        self.hbox.addWidget(self.rb3)
        btn_start = QPushButton("Сформировать")
        btn_start.clicked.connect(self.start_rep)
        self.hbox.addWidget(btn_start)

        # всё в вертикальный бокс
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(self.hbox)

        # Заголовок таблицы
        self.header_table = QTableWidget(self)
        self.vbox.addWidget(self.header_table)
        self.vbox.setSpacing(0) # не будет расстояния между заголовком и таблицей

        # таблица для вывода
        self.table = QTableWidget(self)

        self.vbox.addWidget(self.table)
        self.setLayout(self.vbox)

    def start_rep(self):
        str_date1 = str(self.date1.date().toPyDate())
        str_date2 = str(self.date2.date().toPyDate())
        typeres = 'р'
        if self.rb1.isChecked():
            sal = f" AND resources.typeres = '{typeres}' "
        elif self.rb2.isChecked():
            sal = f" AND resources.typeres <> '{typeres}' "
        else:
            sal = " "
        # читаем ресурсы
        query = f"""
        SELECT resources.id, resources.name, resources.measure, inventory.price,
        resources.typeres 
        FROM resources, inventory
        WHERE resources.id = inventory.id """ + sal +\
        f"""AND inventory.date_purchase <= CAST('{str_date2}' AS DATE) 
        ORDER BY name
        """
        self.lst_res = read_table(query)
        if not self.lst_res:
            msg = QMessageBox()
            msg.setWindowTitle("Нет данных")
            msg.setText("Нет данных по ресурсам. Возможно, не было закупок до "+
                        str_date2)
            msg.setIcon(QMessageBox.Warning)
            msg.exec_()
            return
        zlst = list(zip(*self.lst_res))  # транспонируем список
        ids = zlst[0]  # коды
        names = zlst[1]  # наименования
        self.dict_res = dict(zip(ids, names)) # в словарь их

        # запасы ресурсов
        db_config = get_db_params()
        conn = connect(**db_config)
        cursor = conn.cursor()
        query = "SET SQL_MODE = ''"
        cursor.execute(query)
        query = f"""
        SELECT inventory.id, SUM(inventory.count) AS quantity, inventory.price
        FROM inventory, resources
        WHERE inventory.id IN {ids}
        AND inventory.id = resources.id
        AND resources.typeres <> 'р' 
        AND date_purchase <= CAST('{str_date2}' AS DATE)
        GROUP BY id, price 
        """
        cursor.execute(query)
        lst_inv = cursor.fetchall()
        lst_inv.sort(key=lambda _id: _id[0])

        # выработка
        query = f"""
        SELECT shiftrep.id, resources.name, resources.measure, shiftrep.count 
        FROM shiftrep, resources
        WHERE  shiftrep.id = resources.id 
        AND shiftrep.daterep BETWEEN CAST('{str_date1}' AS DATE) 
                              AND CAST('{str_date2}' AS DATE);
        """
        production = read_table(query)
        production.sort(key=lambda pr_id: pr_id[0])  # сортируем по коду
        zlst = list(zip(*production))  # транспонируем список
        ids_products = zlst[0]  # коды
        # свернем production
        production = pack(production,[0,1,2],*[3])

        # к наименованию добавляем выработку:
        headers = []
        for i, row in enumerate(production):
            headers += [row[1] + "(" + str(row[3]) + ")"]

        # количество колонок в таблицах вывода
        # 1 на наим., по 2 колонки на продукцию, 2 на итоги и 2 на остатки материалов
        columnCount = 1 + 2*len(headers) + 2 + 2
        # формируем заголовки таблицы вывода
        self.header_table.horizontalHeader().setHidden(True)
        self.header_table.verticalHeader().setHidden(True)
        self.header_table.setColumnCount(columnCount)
        self.header_table.setRowCount(0)

        # первая строка заголовка
        self.header_table.insertRow(self.header_table.rowCount())
        item = QTableWidgetItem("Ресурсы")
        item.setTextAlignment(Qt.AlignCenter)
        self.header_table.setItem(0, 0, item)
        # растягиваем первый столбец
        self.header_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch);
        # затраты ресурсов
        for i, head in enumerate(headers):
            self.header_table.setSpan(0, 1+i*2, 1, 2);  # объединить ячейки
            item = QTableWidgetItem(headers[i])
            item.setTextAlignment(Qt.AlignCenter)
            self.header_table.setItem(0, 1+i*2, item)

        self.header_table.setSpan(0, 1+(i+1)*2, 1, 2)
        item = QTableWidgetItem("Итого")
        item.setTextAlignment(Qt.AlignCenter)
        self.header_table.setItem(0, 1 + i * 2 +2, item)

        self.header_table.setSpan(0, 1+(i+1)*2+2, 1, 2)
        item = QTableWidgetItem("Остатки ресурсов")
        item.setTextAlignment(Qt.AlignCenter)
        self.header_table.setItem(0, 1 + i*2 + 4, item)

        # вторая строка заголовка
        self.header_table.insertRow(self.header_table.rowCount())
        self.header_table.setSpan(0, 0, 2, 1);
        for j in range(1, columnCount - 1, 2):
            self.header_table.setItem(1, j, QTableWidgetItem('В нат. выр.'))
            self.header_table.setItem(1, j+1, QTableWidgetItem('Стоимость'))
        # высота заголовка
        height = 2
        for i in range(self.header_table.rowCount()):
            height += self.header_table.rowHeight(0)
        self.header_table.setFixedHeight(height)
        self.header_table.setAutoScroll(False)

        # таблица
        self.table.horizontalHeader().setHidden(True)
        self.table.verticalHeader().setHidden(True)
        self.table.setColumnCount(columnCount)   # количество колонок
        # ширина колонок
        for j in range(columnCount):
            self.table.setColumnWidth(j,self.header_table.columnWidth(j))
        self.table.setRowCount(0)  # количество строк = 0
        # растягиваем первую колонку
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch);

        # затраты на единицу
        self.lst_costs = get_costs(ids_products)

        # вывод
        its = [0.0 for j in range(columnCount)]
        i = 0
        while True:
            # достаем ресурс из lst_res
            res = list(filter(lambda x: self.lst_costs[i][0] in x
                            if self.lst_costs[i][0] == x[0] else None, self.lst_res)
                       )
            if not res:
                i += 1
                if i >= len(self.lst_costs):
                    break
                continue

            ## - формируем строку для вывода
            id0 = self.lst_costs[i][0]
            j = 1   # столбец для вывода затрат
            self.table.insertRow(self.table.rowCount())
            row  = self.table.rowCount() - 1
            name_measure = res[0][1]+" ("+res[0][2]+")" # наименование+ед. изм
            self.table.setItem(row, 0, QTableWidgetItem(name_measure))
            sum_cost, sum_value = 0.0, 0.0
            while id0 == self.lst_costs[i][0]:
                # затраты в натуральном выражении
                # достаем выработку из production
                id_prod = self.lst_costs[i][1]
                prod_i = [x for x in production if x[0] == id_prod]
                cost_res = self.lst_costs[i][2] * prod_i[0][3]
                sum_cost += cost_res
                # по стоимости
                value_res = res[0][3] * cost_res
                sum_value += value_res
                # итоги
                its[j+1] += value_res
                # выводим
                self.table.setItem(row, j, QTableWidgetItem('{:>15.3f}'.format(cost_res)))
                self.table.setItem(row, j+1, QTableWidgetItem('{:>15.2f}'.format(value_res)))
                i += 1
                j += 2
                if i >= len(self.lst_costs):
                    break
            # суммы по строке
            its[j+1] += sum_value
            self.table.setItem(row, j, QTableWidgetItem('{:>15.3f}'.format(sum_cost)))
            self.table.setItem(row, j + 1, QTableWidgetItem('{:>15.2f}'.format(sum_value)))
            # остатки материалов
            j += 2
            inv = list(filter(lambda x: id0 in x
                        if id0 == x[0] else None, lst_inv))
            if inv and (res[0][4] != 'р'):
                self.table.setItem(row, j, QTableWidgetItem('{:>15.3f}'.format(inv[0][1])))
                value = inv[0][1] * inv[0][2]
                its[j+1] += value
                self.table.setItem(row,j+1,QTableWidgetItem('{:>15.2f}'.format(value)))
            else:
                self.table.setItem(row,j, QTableWidgetItem('{:>15s}'.format('---')))
                self.table.setItem(row, j+1, QTableWidgetItem('{:>15s}'.format('---')))
            if i >= len(self.lst_costs):
                break
        # суммы по столбцам
        self.table.insertRow(self.table.rowCount())
        row = self.table.rowCount() - 1
        self.table.setItem(row, 0, QTableWidgetItem('Итого:'))
        for j in range(1, columnCount):
            if its[j] != 0.0:
                self.table.setItem(row, j, QTableWidgetItem('{:>15.2f}'.format(its[j])))
            else:
                self.table.setItem(row, j, QTableWidgetItem('{:>15s}'.format('---')))
        # Затраты на единицу продукции
        self.table.insertRow(self.table.rowCount())
        row = self.table.rowCount() - 1
        self.table.setItem(row, 0, QTableWidgetItem('Затраты на единицу продукции:'))
        for j in range(1, columnCount):
            if j < columnCount - 4:
                if its[j] != 0.0:
                    count = production[j // 2 - 1][3]
                    its1 = its[j] / count
                    self.table.setItem(row, j, QTableWidgetItem('{:>15.2f}'.format(its1)))
                else:
                    self.table.setItem(row, j, QTableWidgetItem('{:>15s}'.format('---')))
            else:
                self.table.setItem(row, j, QTableWidgetItem('{:>15s}'.format('---')))

