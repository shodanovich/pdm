import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QWidget, QApplication
from PyQt5.QtGui import QIcon

import create_DB    # создание базы данных
import edit_res     # редактирование ресурсов
import costs        # нормативы затрат
import shift_rep          # сменный отчет участка

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
        edit_res_action.triggered.connect(self.editRes)
        res_menu.addAction(edit_res_action)

        # меню нормативов
        norm_menu = menubar.addMenu('&Нормативы')
        # нормативы затрат
        costs_action = QAction('&Нормативы затрат', self)
        costs_action.triggered.connect(self.costs)
        norm_menu.addAction(costs_action)

        # меню Производство
        prodaction_menu = menubar.addMenu('&Производство')
        # сменный отчет
        shift_report_action = QAction('&Сменный отчет участка',self)
        shift_report_action.triggered.connect(self.shift_rep)
        prodaction_menu.addAction(shift_report_action)

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

    def editRes(self):
        self.edit_res = edit_res.EditRes()
        self.edit_res.build('resources')
        self.edit_res.show()

    def costs(self):
        self.costs_window = costs.Costs()

    def shift_rep(self):
        self.sou_window = shift_rep.ShiftRep()

    # def create_database(self):
    #     self.createDBWindow = create_DB.CreateDB(self)
    #     self.createDBWindow.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    pdm = Pdm()
    pdm.show()
    sys.exit(app.exec())
