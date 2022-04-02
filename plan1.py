from datetime import date
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from scipy.optimize import linprog
from commons import *

VBN = 9999.99   # very big bumber

class Plan1(QWidget):
    def __init__(self):
        super().__init__()
        # окно для выбора параметров плана
        self.setGeometry(300, 300, 900, 400)
        self.setWindowTitle('План выпуска')  # заголовок окна
        self.date_pl = QDateEdit(date.today())
        hbox1 = QHBoxLayout()
        hbox1.addWidget(QLabel("Период с "))
        hbox1.addWidget(self.date_pl)
        hbox1.addStretch()
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
        tab_prod = self.table_prod = QTableWidget()
        headers_list = ["Код", "Наименование изделия","План"]
        column_count = len(headers_list)
        tab_prod.setColumnCount(column_count)
        tab_prod.setHorizontalHeaderLabels(headers_list)
        tab_prod.setRowCount(0)
        tab_prod.setColumnWidth(0,40)
        header = tab_prod.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        tab_prod.verticalHeader().setHidden(True)   # нет боковым заголовкам

        hbox2 = QHBoxLayout()
        # пропорции 3:2
        hbox2.addWidget(tab_res,3)
        hbox2.addWidget(tab_prod,2)

        # всё в вертикальный бокс
        self.vbox = QVBoxLayout()
        self.vbox.addLayout(hbox1)
        self.vbox.addLayout(hbox2)
        #self.vbox.addStretch()
        self.setLayout(self.vbox)
        # заполняем таблицы запасов и изделий
        self.init_tables()

        # заполняем таблицу запасов
        self.show()

    def init_tables(self):
        lst_prod = self.get_prod()
        zlst = list(zip(*lst_prod))  # транспонируем список
        ids = zlst[0]  # коды изделий
        # заполняем таблицу плана
        for i in range(len(lst_prod)):
            self.table_prod.insertRow(i)
            for j in range(len(lst_prod[i])):
                self.table_prod.setItem(i, j, QTableWidgetItem(str(lst_prod[i][j])))

        # запасы ресурсов
        lst_inv = self.get_inventory(ids) # получить ресурсы, имеющиеся в наличии
        # это величина запасов
        rhs_ineq = list(map(lambda x: VBN if x[2] == 0 else x[2], lst_inv))
        # заполняем таблицу ресурсов
        for i in range(len(lst_inv)):
            self.table_res.insertRow(i)
            self.table_res.setItem(i,0, QTableWidgetItem(str(lst_inv[i][0])))
            self.table_res.setItem(i,1, QTableWidgetItem(lst_inv[i][1]))
            self.table_res.setItem(i,2,
                        QTableWidgetItem(str('{:>15.3f}'.format(rhs_ineq[i]))))

    def get_prod(self):
        # изделия
        query = """
           SELECT id, name FROM resources
           WHERE NOT EXISTS(
              SELECT res1_id from costs
              WHERE res1_id = resources.id
              )
           ORDER BY name
           """
        return(read_table(query))

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
        # 1. obj[]. Целевая функция
        lst_prod = self.get_prod()
        zlst = list(zip(*lst_prod))  # транспонируем список
        ids = zlst[0]  # коды изделий
        obj = [-1 for j in range(len(ids))]  # максимизируем величину выпуска
        # 2. lhs_ineq. Левая часть ограничений по ресурсам. Это затраты ресурсов.
        costs = get_costs(ids)  # затраты на ед.
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
        # 5. bnd. Область определения переменных  0 : +inf
        bnd = [(0, float('inf')) for j in range(len(ids))]

        # получаем план
        opt = linprog(c = obj,        # коэф. цф
                A_ub = lhs_ineq,      # левые коэф. из ограничений-неравенств
                b_ub = rhs_ineq,      # правые коэф. из ограничений-неравенств
                bounds = bnd,         # области значений переменных
                method="simplex")

        # заполнияем список продукции и таблицу плана
        lst_prod = self.get_prod()  # коды и наименования готовой продукции
        lst_prod = [list(x) for x in lst_prod]

        for i in range(len(lst_prod)):
            lst_prod[i].append(opt.x[i])    # дополняем их планом
            self.table_prod.setItem(i,2,
                QTableWidgetItem(str('{:>15.3f}'.format(opt.x[i]))))

        # вычисляем потребности в ресурсах на план
        it_lst = []
        for i, cost in enumerate(costs):
            prod_i = list(filter(lambda x: cost[1] in x if cost[1] == x[0]
                        else None, lst_prod))
            cost[2] *= prod_i[0][2]
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

    def flt(self,id1,id2):
        if id1 == id2:
            return True
        else:
            return None
