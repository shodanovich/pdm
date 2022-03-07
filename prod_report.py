from datetime import date
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QWidget, QDateEdit, QTableWidget, QHBoxLayout, QVBoxLayout,
                            QLabel, QPushButton, QTableWidgetItem )
from edit_tables import EditTables

class ProdReport(QWidget):
    def __init__(self):
        super().__init__()

        self.setGeometry(400,400,600,500)

        self.lst_costs = []

        # размещаем даты и кнопку в горизонтальном боксе
        self.date1 = QDateEdit(date.today())
        self.date2 = QDateEdit(date.today())
        hbox = QHBoxLayout()
        hbox.addWidget(QLabel("Период с "))
        hbox.addWidget(self.date1)
        hbox.addWidget(QLabel(" по "))
        hbox.addWidget(self.date2)
        hbox.addStretch()
        btn_start = QPushButton("Сформировать")
        btn_start.clicked.connect(self.start_rep)
        hbox.addWidget(btn_start)

        # таблица для вывода
        self.table = QTableWidget(self)

        # всё в вертикальный бокс
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(hbox)
        self.vbox.addWidget(self.table)
        self.setLayout(self.vbox)

        # читаем ресурсы
        query = "SELECT * FROM resources ORDER BY name"
        self.lst_res = EditTables.read_table(EditTables,query)
        zlst = list(zip(*self.lst_res))  # транспонируем список
        ids = zlst[0]   # коды
        names = zlst[1]  # наименования
        self.dict_res = dict(zip(ids, names))
        pass

    def start_rep(self):
        # ищем готовую продукцию. Это та, которая уже никуда не входит как затраты
        query = """
        SELECT id, name FROM resources
        WHERE NOT EXISTS(
            SELECT res1_id from costs 
            WHERE res1_id = resources.id
            ) 
        """
        lst_products = EditTables.read_table(EditTables,query)
        # получаем список кодов и наименований
        zlst = list(zip(*lst_products))  # транспонируем список
        ids_products = zlst[0]      # коды
        names_products = zlst[1]

        # выработка
        str_date1 = str(self.date1.date().toPyDate())
        str_date2 = str(self.date2.date().toPyDate())
        query = f"""
                SELECT id, count FROM shiftrep 
                WHERE daterep BETWEEN CAST('{str_date1}' AS DATE) 
                                      AND CAST('{str_date2}' AS DATE);
                """
        production = EditTables.read_table(EditTables, query)
        dict_production = dict(production)

        # к наименованию добавляем выработку:
        headers = []
        for i, row in enumerate(names_products):
            row += ("(" + str(dict_production[ids_products[i]]) + ")")
            headers += [row]

        # формируем заголовки таблицы вывода
        headers = [x.replace(' ','\n') for x in headers]    # перенос длинных строк
        headers = (["Ресурсы"] + headers)
        # заголовки таблицы  и число строк
        self.table.setColumnCount(len(ids_products) + 1)   # количество колонок в QTableWidget
        self.table.setHorizontalHeaderLabels(headers)  # заголовки столбцов
        self.table.setRowCount(0)  # количество строк = 0
        # ширина столбцов
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)

        # затраты на единицу
        self.lst_costs = self.get_costs(ids_products)

        # вывод
        i = 0
        while i  < len(self.lst_costs):
            id0 = self.lst_costs[i][0]
            j = 1   # столбец для вывода затрат
            self.table.insertRow(self.table.rowCount())
            self.table.insertRow(self.table.rowCount())
            row  = self.table.rowCount() - 2
            # достаем ресурс из lst_res
            res = list(filter(lambda x: self.lst_costs[i][0] in x
                             if self.lst_costs[i][0] == x[0] else None, self.lst_res))
            ## - формируем строку для вывода
            name_measure = res[0][1]+" ("+res[0][2]+")" # наименование+ед. изм
            self.table.setItem(row, 0, QTableWidgetItem(name_measure))
            self.table.setItem(row + 1, 0, QTableWidgetItem('Стоимость (руб)'))
            while id0 == self.lst_costs[i][0]:
                # затраты в натуральном выражении
                cost_res = self.lst_costs[i][2] * dict_production[self.lst_costs[i][1]]
                value_res = res[0][3] * cost_res
                self.table.setItem(row, j, QTableWidgetItem('{:>15.3f}'.format(cost_res)))
                self.table.setItem(row+1, j, QTableWidgetItem('{:>15.2f}'.format(value_res)))
                i += 1
                if i >= len(self.lst_costs): break
                j += 1

        lst_itg = []
        for row in lst_products:
            lst_row = list(row)
            lst_row[0] = dict_production[lst_row[0]]
            lst_itg.append(lst_row)
        zip_products = list(zip(*lst_itg))

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

