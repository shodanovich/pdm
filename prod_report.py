from datetime import date
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from edit_tables import EditTables

class ProdReport(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle('Отчет по производству и затратам')
        self.setGeometry(400,400,900,500)

        self.lst_costs = [] # для рекурсивной функции

        # размещаем даты и кнопку в горизонтальном боксе
        self.date1 = QDateEdit(date.today())
        self.date2 = QDateEdit(date.today())
        self.hbox = QHBoxLayout()
        self.hbox.addWidget(QLabel("Период с "))
        self.hbox.addWidget(self.date1)
        self.hbox.addWidget(QLabel(" по "))
        self.hbox.addWidget(self.date2)
        self.hbox.addStretch()
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
        # читаем ресурсы
        query = f"""
        SELECT resources.*, inventory.price 
        FROM resources, inventory
        WHERE resources.id = inventory.id
        AND inventory.date_purchase <= CAST('{str_date2}' AS DATE) 
        ORDER BY name
        """
        self.lst_res = EditTables.read_table(EditTables, query)
        zlst = list(zip(*self.lst_res))  # транспонируем список
        ids = zlst[0]  # коды
        names = zlst[1]  # наименования
        self.dict_res = dict(zip(ids, names)) # в словарь их

        # выработка
        query = f"""
        SELECT shiftrep.id, resources.name, resources.measure, shiftrep.count 
        FROM shiftrep, resources
        WHERE  shiftrep.id = resources.id 
        AND shiftrep.daterep BETWEEN CAST('{str_date1}' AS DATE) 
                              AND CAST('{str_date2}' AS DATE);
        """
        production = EditTables.read_table(EditTables, query)
        production.sort(key=lambda pr_id: pr_id[0])  # сортируем по коду
        zlst = list(zip(*production))  # транспонируем список
        ids_products = zlst[0]  # коды
        # свернем production
        i = 0;
        lst_s = []
        while i < len(production):
            id0 = production[i][0]
            name = production[i][1]
            measure = production[i][2]
            sum = 0.0
            while (i < len(production)) and (id0 == production[i][0]):
                sum += production[i][3]
                i += 1
            lst_i = [id0, name, measure, sum]
            lst_s.append(lst_i)
        production = lst_s

        # к наименованию добавляем выработку:
        headers = []
        for i, row in enumerate(production):
            headers += [row[1] + "(" + str(row[3]) + ")"]

        # количество колонок в таблицах вывода
        columnCount = 1 + 2*len(headers) + 2
        # формируем заголовки таблицы вывода
        self.header_table.horizontalHeader().setHidden(True)
        self.header_table.verticalHeader().setHidden(True)
        self.header_table.setColumnCount(columnCount)
        self.header_table.setRowCount(0)

        self.header_table.insertRow(self.header_table.rowCount())
        # первая строчка
        item = QTableWidgetItem("Ресурсы")
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.header_table.setItem(0, 0, item)
        self.header_table.horizontalHeader().setSectionResizeMode(0,QHeaderView.Stretch);

        # затраты ресурсов
        # первая строка заголовка
        for i, head in enumerate(headers):
            self.header_table.setSpan(0, 1+i*2, 1, 2);  # объединить ячейки
            item = QTableWidgetItem(headers[i])
            item.setTextAlignment(QtCore.Qt.AlignCenter)
            self.header_table.setItem(0, 1+i*2, item)
        self.header_table.setSpan(0, 1+(i+1)*2, 1, 2)
        item = QTableWidgetItem("Итого")
        item.setTextAlignment(QtCore.Qt.AlignCenter)
        self.header_table.setItem(0, 1 + i * 2 +2, item)

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

        # затраты на единицу
        self.lst_costs = self.get_costs(ids_products)

        # вывод
        its = [0.0 for j in range(columnCount)]
        i = 0
        while True:
            id0 = self.lst_costs[i][0]
            j = 1   # столбец для вывода затрат
            self.table.insertRow(self.table.rowCount())
            row  = self.table.rowCount() - 1
            # достаем ресурс из lst_res
            res = list(filter(lambda x: self.lst_costs[i][0] in x
                             if self.lst_costs[i][0] == x[0] else None, self.lst_res))
            ## - формируем строку для вывода
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
        for j in range(1, columnCount-2):
            if its[j] != 0.0:
                count = production[j // 2 - 1][3]
                its1 = its[j] / count
                self.table.setItem(row, j, QTableWidgetItem('{:>15.2f}'.format(its1)))
            else:
                self.table.setItem(row, j, QTableWidgetItem('{:>15s}'.format('---')))

    # затраты на единицу продукции
    def get_costs(self, ids):
        # читаем все нормативы затрат
        query = "SELECT res1_id, res2_id, cost FROM costs"
        lst = EditTables.read_table(EditTables,query)
        # собираем затраты на id_
        self.it_lst = []
        for id_ in ids:
            cost = 1
            self.eval_costs(id_, lst, cost)
            # убираем из списка материалов полуфабрикаты
            zlst = list(zip(*self.it_lst))  # транспонируем список
            res_ids = zlst[1]  # коды ресурсов, куда входит res_id1
            self.it_lst = [x1 for x1 in self.it_lst if x1[0] not in res_ids]
            # заменяем вторые коды на id_
            for row in self.it_lst:
                if row[1] not in ids:
                    row[1] = id_

        self.it_lst.sort(key=lambda res_id: res_id[1])  # сортируем по второму коду
        self.it_lst.sort(key=lambda res_id: res_id[0])  # сортируем по первому коду

        # свернем по этим кодам:
        i = 0; lst_s = []
        while i < len(self.it_lst):
            id0 = self.it_lst[i][0]
            while (i < len(self.it_lst)) and (id0 == self.it_lst[i][0]):
                sum = 0.0
                id1 = self.it_lst[i][1]
                while i < len(self.it_lst) and (id0 == self.it_lst[i][0]) \
                        and (id1 == self.it_lst[i][1]):
                    sum += self.it_lst[i][2]
                    i += 1
                lst_i = [id0, id1, sum]
                lst_s.append(lst_i)

        return lst_s

    # затраты покупных материалов на изделие
    def eval_costs(self, id_, lst, cost = 1):
        lst1 = [list(x) for x in lst if x[1]==id_]
        if not lst1:
            return
        for i, row in enumerate(lst1):
            row[2] *= cost
            self.it_lst.append(row)
            id_ = row[0]
            self.eval_costs(id_, lst, row[2])

