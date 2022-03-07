import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QWidget, QApplication
from PyQt5.QtGui import QIcon

import create_DB    # создание базы данных
from edit_res import EditRes     # редактирование ресурсов
from shift_rep import ShiftRep
import costs        # нормативы затрат
from prod_report import ProdReport

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
        plan_menu = menubar.addMenu('&Планирование')
        # план исходя из имеющихся запасов
        plan1_action = QAction('&План исходя из имеющихся запасов')
        plan_menu.addAction(plan1_action)
        # план и расчет потребностей в ресурсах
        plan2_action = QAction('&Расчет запасов по плану продукции')
        plan_menu.addAction(plan2_action)

        # # меню создание БД
        # db_menu = menubar.addMenu('&База данных')
        # db_action = QAction('&Создать базу данных', self)
        # db_action.triggered.connect(self.create_database)
        # db_menu.addAction(db_action)

        self.setGeometry(300, 300, 600, 200)
        self.setWindowTitle('Управление производственным участком')

    def edit_res(self):
        """Редактор ресурсов"""
        # упакуем параметры в словарь
        params={}
        # параметры QTableWidget
        params['table_params']={'title': 'Редактирование ресурсов',
                                'columnnames': 'Код, Наименование, Ед. изм., Цена(расц.)',
                                'unique': '0, 1'
                                }
        # параметры запросов к БД
        params['select_query'] = "SELECT * FROM resources ORDER BY name"

        edit_res = EditRes(params)
        edit_res.show()

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
        SELECT id, name  FROM resources WHERE price < 0.01 ORDER BY name
        """
        params['delete_query'] = "DELETE FROM shiftrep WHERE (id IN (%s) AND daterep IN(%s))"
        params['save_query'] = "INSERT INTO shiftrep (daterep, id, count) VALUES (%s,%s,%s)"

        self.edit_shif_rep = ShiftRep(params)

    def prod_report(self):
        self.prod_rep = ProdReport()
        self.prod_rep.show()

    # def create_database(self):
    #     self.createDBWindow = create_DB.CreateDB(self)
    #     self.createDBWindow.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pdm = Pdm()
    pdm.show()
    sys.exit(app.exec())
