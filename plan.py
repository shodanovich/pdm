from datetime import date
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from scipy.optimize import linprog
from commons import *

VBN = 9999.99   # very big bumber

class Plan(QWidget):
    def __init__(self):
        super().__init__()
        # окно для выбора параметров плана
        self.setGeometry(300, 300, 900, 400)
        self.setWindowTitle('План выпуска')  # заголовок окна
        self.date_pl = QDateEdit(date.today())
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("План на "))
        hbox1.addWidget(self.date_pl)
        hbox1.addStretch()
        # кнопки выбора критерия оптимизации
        self.rb1 = QRadioButton('Максимум выпуска')
        self.rb2 = QRadioButton('Максимум прибыли')
        self.rb1.setChecked(True)

        hbox2 = QHBoxLayout()
        hbox2.addWidget(self.rb1)
        hbox2.addWidget(self.rb2)
        hbox1.addLayout(hbox2)
        btn_start = QPushButton("Сформировать")
        btn_start.clicked.connect(self.start_pl)
        hbox1.addWidget(btn_start)

        # таблица ресурсов
        tab_res = self.table_res = QTableWidget(self)
        headers_list = ["Код","Наименование ресурса","Запас","Потребность","Остаток"]
        column_count = len(headers_list)  # количество колонок в QTableWidget
        tab_res.setColumnCount(column_count)
        tab_res.setHorizontalHeaderLabels(headers_list)  # заголовки столбцов
        tab_res.setRowCount(0)  # количество строк = 0
        # первая колонка с кодом имеет фиксированную ширину
        tab_res.setColumnWidth(0, 40)
        # вторую колонку (наименование) растягиваем по содержимому
        header = tab_res.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        # убираем боковые заголовки
        self.table_res.verticalHeader().setHidden(True)

        # план продукции
        tab_plan = self.table_plan = QTableWidget()
        headers_list = ["Код", "Наименование изделия","План"]
        column_count = len(headers_list)
        tab_plan.setColumnCount(column_count)
        tab_plan.setHorizontalHeaderLabels(headers_list)
        tab_plan.setRowCount(0)
        tab_plan.setColumnWidth(0,40)
        header = tab_plan.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        tab_plan.verticalHeader().setHidden(True)   # нет боковым заголовкам
        self.table_plan.itemChanged.connect(self.on_change_plan)
        # вывод целевой функции
        self.label_fun = QLabel()
        vbox1 = QVBoxLayout()
        vbox1.addWidget(tab_plan)
        vbox1.addWidget(self.label_fun)

        hbox2 = QHBoxLayout()
        # пропорции 3:2
        hbox2.addWidget(tab_res,3)
        hbox2.addLayout(vbox1,2)

        # всё в вертикальный бокс
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(hbox1)
        self.vbox.addLayout(hbox2)
        #self.vbox.addStretch()
        self.setLayout(self.vbox)
        # заполняем таблицы запасов и изделий
        self.init_tables()

        self.show()

    def init_tables(self):
        lst_prod = get_prod()
        zlst = list(zip(*lst_prod))  # транспонируем список
        ids = zlst[0]  # коды изделий
        # заполняем таблицу плана
        self.table_plan.blockSignals(True)  # блокируем сигналы в QWidgetTable
        for i in range(len(lst_prod)):
            self.table_plan.insertRow(i)
            for j in range(len(lst_prod[i])):
                self.table_plan.setItem(i, j, QTableWidgetItem(str(lst_prod[i][j])))
        self.table_plan.blockSignals(False)


        # запасы ресурсов
        self.lst_inv = self.get_inventory(ids) # получить ресурсы, имеющиеся в наличии
        # это величина запасов
        rhs_ineq = list(map(lambda x: VBN if x[2] == 0 else x[2], self.lst_inv))
        # заполняем таблицу ресурсов
        for i in range(len(self.lst_inv)):
            self.table_res.insertRow(i)
            self.table_res.setItem(i,0, QTableWidgetItem(str(self.lst_inv[i][0])))
            self.table_res.setItem(i,1, QTableWidgetItem(self.lst_inv[i][1]))
            self.table_res.setItem(i,2,
                        QTableWidgetItem(str('{:>15.3f}'.format(rhs_ineq[i]))))

    def on_change_plan(self):
        # пересчитываем потребность в ресурсах
        lst_prod = get_prod()
        ids = list(zip(*lst_prod))[0]  # коды изделий
        costs = get_costs(ids)  # затраты на ед.
        self.res_plan(costs, lst_prod)  # затраты ресурсов на план
        pass


    def get_inventory(self, ids):
        read_table("SET SQL_MODE = ''")
        str_date_pl = str(self.date_pl.date().toPyDate())
        query = f"""
        SELECT inventory.id, resources.name, SUM(inventory.count) AS quantity, 
                inventory.price
        FROM inventory, resources
        WHERE inventory.id NOT IN {ids}
        AND inventory.id = resources.id
        AND date_purchase <= CAST('{str_date_pl}' AS DATE)
        GROUP BY id, price 
        ORDER BY resources.name
        """
        return(read_table(query))

    def start_pl(self):
        # 1. obj[]. Целевая функция.
        lst_prod = get_prod()
        zlst = list(zip(*lst_prod))  # транспонируем список
        ids = zlst[0]  # коды изделий
        costs = get_costs(ids)  # затраты на ед.

        if self.rb1.isChecked():    # максимизируем величину выпуска
            obj = [-1 for j in range(len(ids))]
        elif self.rb2.isChecked():  # максимизируем прибыль
            # затраты на изделия
            lst_costs = []
            for id in ids:
                for row in costs:
                    if row[1] == id:
                        # стоимость затрат:
                        c = list(filter(lambda x: row[0] in x if row[0] == x[0]
                        else None, self.lst_inv))
                        lst_i = [row[0], row[1], row[2]*c[0][3]]
                        lst_costs.append(lst_i)
            # суммируем по изделию
            lst_costs = pack(lst_costs,[1],*[2])
            # находим цены изделий
            date_ = self.date_pl.date().toPyDate()
            query = f"""
            SELECT id, price, date_price FROM prices 
            WHERE date_price <= DATE('{str(date_)}')
            ORDER BY date_price DESC
            """
            prices = read_table(query)
            # финальная obj:
            obj = []
            for id in ids:
                for j in range(len(lst_costs)):
                    if id == lst_costs[j][0]:
                        obj.append(-prices[j][1] + lst_costs[j][1])
        # 2. lhs_ineq. Левая часть ограничений по ресурсам. Это затраты ресурсов.
        # формируем матрицу затрат
        lhs_ineq = []
        i = 0
        while i < len(costs):
            id0 = costs[i][0]
            lst_i = []
            while i < len(costs) and id0 == costs[i][0]:
                lst_i.append(costs[i][2])
                i += 1
            lhs_ineq.append(lst_i)
        # 3. rhs_ineq. Правая часть ограничений по ресурсам. Берём из QTableWidget
        rhs_ineq = []
        for i in range(self.table_res.rowCount()):
            row = float(self.table_res.item(i,2).text())
            rhs_ineq.append(row)

        # 4. Ограничений-равенств не будет
        # 5. bnd. Область определения переменных  0 ... +inf
        bnd = [(0, float('inf')) for j in range(len(ids))]

        # получаем план
        opt = linprog(c = obj,        # коэф. цф
                A_ub = lhs_ineq,      # левые коэф. из ограничений-неравенств
                b_ub = rhs_ineq,      # правые коэф. из ограничений-неравенств
                bounds = bnd,         # области значений переменных
                method="revised simplex")

        # заполнияем список продукции и таблицу плана
        lst_prod = get_prod()  # коды и наименования готовой продукции

        self.table_plan.blockSignals(True)
        for i in range(len(lst_prod)):
            # дополняем их планом
            self.table_plan.setItem(i, 2,
                      QTableWidgetItem(str('{:>15.3f}'.format(opt.x[i]))))

        self.table_plan.blockSignals(False)
        # # дополняем таблицу плана значением целевой функции
        self.label_fun.setText("Значение целевой функции:" +
                               '{:>15.3f}'.format(-opt.fun))
        # потребности в ресурсах на план
        self.res_plan(costs, lst_prod)

    def res_plan(self, costs, lst_prod):
        # вычисляем потребности в ресурсах на план
        lst_prod = [list(x) for x in lst_prod]
        for i in range(self.table_plan.rowCount()):
            lst_prod[i].append(float(self.table_plan.item(i,2).text()))
        it_lst = []
        for i, cost in enumerate(costs):
            prod_i = list(filter(lambda x: cost[1] in x if cost[1] == x[0]
                        else None, lst_prod))
            cost[2] *= prod_i[0][3]
            it_lst.append(cost)

        it_lst = pack(it_lst,[0],*[2])

        # заполняем table_res
        for i in range(self.table_res.rowCount()):
            # из it_list получаем затраты по коду self.table_res[i][0]
            id1 = int(self.table_res.item(i,0).text())
            lst_i = list(filter(lambda x: id1 in x if id1 == x[0]
                                 else None, it_lst))
            self.table_res.setItem(i,3,
                    QTableWidgetItem(str('{:>15.3f}'.format(lst_i[0][1]))))
        pass
