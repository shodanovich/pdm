import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication
from PyQt5.QtGui import QIcon
from mysql.connector import connect, Error

from mysql_dbconf import get_db_params
from create_db import create_db    # создание базы данных
from edit_res import EditRes     # редактирование ресурсов
from shift_rep import ShiftRep
import costs        # нормативы затрат
from prod_report import ProdReport
from purchases import Purchases
from plan import Plan
from price import Price

class Pdm(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
    def initUI(self):
        # строка меню
        menubar = self.menuBar()
        # строка статуса
        self.statusBar()

        # --- пункты меню ---
        # меню выход
        exit_action = QAction(QIcon('exit.png'), '&Выход', self)
        exit_action.setShortcut('Esc')
        exit_action.setStatusTip('Выход из приложения')
        exit_action.triggered.connect(qApp.quit)
        file_menu = menubar.addMenu('&Файл')
        file_menu.addAction(exit_action)

        # меню ресурсов
        res_menu = menubar.addMenu('&Ресурсы')
        # редактирование ресурсов
        edit_res_action = QAction('&Редактирование ресурсов', self)
        edit_res_action.triggered.connect(self.edit_res)
        res_menu.addAction(edit_res_action)
        # закупки
        purchases_action = QAction('&Закупки, списание', self)
        purchases_action.triggered.connect(self.purchases)
        res_menu.addAction(purchases_action)
        # цена изделий
        price_action = QAction('&Цена изделий', self)
        price_action.triggered.connect(self.price)
        res_menu.addAction(price_action)

        # меню нормативов
        norm_menu = menubar.addMenu('&Нормативы')
        # нормативы затрат
        costs_action = QAction('&Нормативы затрат', self)
        costs_action.triggered.connect(self.costs)
        norm_menu.addAction(costs_action)

        # меню Производство
        production_menu = menubar.addMenu('&Производство')
        # сменный отчет
        shift_report_action = QAction('&Сменный отчет участка',self)
        shift_report_action.triggered.connect(self.shift_rep)
        production_menu.addAction(shift_report_action)
        # отчет по производству и затратам
        prod_report_action = QAction('&Отчет по производству и затратам',self)
        prod_report_action.triggered.connect(self.prod_report)
        production_menu.addAction(prod_report_action)

        # меню Планирование
        plan_menu = menubar.addMenu('Планирование')
        # план исходя из имеющихся запасов
        plan1_action = QAction('План выпуска',self)
        plan1_action.triggered.connect(self.plan1)
        plan_menu.addAction(plan1_action)

        self.setGeometry(300, 300, 600, 200)
        self.setWindowTitle('Управление производственным участком')


    def edit_res(self):
        """Редактор ресурсов"""
        # упакуем параметры в словарь
        params = {}
        # параметры QTableWidget
        params['table_params'] = {'title': 'Редактирование ресурсов (работ)',
                                'columnnames': 'Код, Наименование, Ед. изм., Тип рес.',
                                'unique': '0, 1'
                                }
        # параметры запросов к БД
        params['select_query'] = "SELECT * FROM resources ORDER BY name"

        edit_res = EditRes(params)
        edit_res.show()

    def purchases(self):
        params = {}
        params['table_params'] = {'title': 'Закупки и списание материалов, прием сотрудников',
                                  'columnnames':
                                      'Код, Наименование, , Ед.\nизм., Количество,Цена'
                                  }
        params['select_query'] = ''
        self.purchases = Purchases(params)

    def price(self):
        params = {}
        params['table_params'] = {'title': 'Цены изделий',
                                  'columnnames':
                                      'Код, Наименование, , Ед.\nизм., Цена'
                                  }
        params['select_query'] = ''
        self.price = Price(params)

    def costs(self):
        """
        Нормативы затрат
        :return:
        """
        params = {}
        # параметры таблицы
        params['table_params'] = {'title': 'Нормативы затрат на единицу изделия',
                                  'columnnames': 'Код, Ресурс,,Ед. изм.,Расход на ед.',
                                  'unique': '0, 1'
                                  }
        params['select_query'] = {}
        self.costs_window = costs.Costs(params)

    def shift_rep(self):
        """Сменный отчет"""
        # упакуем параметры в словарь
        params = {}
        # параметры QTableWidget
        params['table_params'] = {'title': 'Сменный отчет участка',
                                  'columnnames': 'Код, Наименование, , Количество',
                                  'unique': '0, 1'
                                  }
        # параметры запросов к БД
        params['select_query'] = """
        SELECT id, name  FROM resources ORDER BY name
        """
        params['delete_query'] = "DELETE FROM shiftrep WHERE (id IN (%s) AND daterep IN(%s))"
        params['save_query'] = "INSERT INTO shiftrep (daterep, id, count) VALUES (%s,%s,%s)"

        self.edit_shif_rep = ShiftRep(params)

    def prod_report(self):
        self.prod_rep = ProdReport()
        self.prod_rep.show()

    def plan1(self):
        self._plan1 = Plan()
        self._plan1.show()


def first_launch():
    db_config = get_db_params()
    try:
        # при успешном соединении ничего не делаем
        conn = connect(**db_config)
        return
    except Error:
        # создаем базу данных
       create_db()


if __name__ == '__main__':
    first_launch()
    app = QApplication(sys.argv)
    pdm = Pdm()
    pdm.show()
    sys.exit(app.exec())
