from PyQt5 import QtWidgets
from PyQt5.QtWidgets import *

import edit_res
from commons import *

class EditTables(QWidget):
    """
    Чтение таблицы из БД, вывод на экран и редактирование
    :param params: параметры таблицы в БД и QTableWidget
    """
    def __init__(self, params):
        super().__init__()
        # разбор параметров
        table_params = params['table_params']
        select_query = params['select_query']

        ### --- таблица ---
        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle(table_params['title'])    # заголовок окна
        tab = self.table = QtWidgets.QTableWidget(self)
        # Устанавливаем заголовки таблицы
        headers = table_params['columnnames']
        headers_list = [x.strip() for x in headers.split(',')]
        column_count = len(headers_list)  # количество колонок в QTableWidget
        tab.setColumnCount(column_count)
        tab.setHorizontalHeaderLabels(headers_list) # заголовки столбцов
        tab.setRowCount(0)  # количество строк = 0

        # первая колонка с кодом имеет фиксированную ширину
        tab.setColumnWidth(0,40)
        # вторую колонку (наименование) растягиваем по содержимому
        header = tab.horizontalHeader()
        header.setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        # событие изменения значения в клетке: будет проверка на уникальность
        if isinstance(self,edit_res.EditRes):
            unique = table_params['unique']   #колонки, в которых значение д. б. уникальным
            unique_list = [int(x.strip()) for x in unique.split(',')]
            tab.itemChanged.connect(lambda: self.check_unique(unique_list))

        lst_table = read_table(select_query)
        # i - число записей, вставленных в QTableWidget
        i = self.insert_to_table(lst_table, tab)
        # строка состояния
        self.info_label = QtWidgets.QLabel()
        self.info_label.setText(f"Прочитано записей: {i}")

        ### --- управляющие кнопки ---
        self.btn_insert = QPushButton("Добавить (Ins)")
        self.btn_insert.setShortcut('Ins')
        self.btn_insert.clicked.connect(self.add_row)
        self.btn_delete = QPushButton('Удалить (Shift+Del)')
        self.btn_delete.setShortcut('Shift+Del')
        self.btn_delete.clicked.connect(self.delete_record)
        self.btn_save = QPushButton('Сохранить (Ctrl+S)')
        self.btn_save.setShortcut('ctrl+s')
        self.btn_save.clicked.connect(self.save_table)
        self.btn_exit = QPushButton('Выйти (Esc)')
        self.btn_exit.setShortcut('Esc')
        self.btn_exit.clicked.connect(self.out)

        # расположение виджетов в окне
        # кнопки располагаем по горизонтали:
        hbtnbox = QHBoxLayout()
        hbtnbox.addStretch(1)
        hbtnbox.addWidget(self.btn_insert)
        hbtnbox.addWidget(self.btn_delete)
        hbtnbox.addWidget(self.btn_save)
        hbtnbox.addWidget(self.btn_exit)
        # сначала таблица, потом кнопки, внизу статус:
        self.vbox = QVBoxLayout()
        self.vbox.addWidget(tab)

        self.vbox.addLayout(hbtnbox)
        self.vbox.addWidget(self.info_label)
        # помещаем всё в QWidget
        self.setLayout(self.vbox)

        self.show()

    # добавляем строку в QTableWidget
    def add_row(self):
        row_count = self.table.rowCount()
        # собираем коды ресурсов QTableWidget в кортеж
        ids = tuple(int(self.table.item(i,0).text()) for i in range(row_count))
        self.table.insertRow(row_count)
        # добавляем код
        ids1 = tuple(i for i in range(row_count) if not(i in ids))
        id = ids1[0] if ids1 else row_count
        self.table.setItem(row_count,0,QtWidgets.QTableWidgetItem(str(id)))
        self.table.setCurrentCell(row_count,1)

    # проверка на уникальность
    def check_unique(self,col_list=[]):
        tab = self.table
        if tab.rowCount() == 1:
            return
        if tab.currentColumn() not in col_list:
            return
        current_column = tab.currentColumn()
        current_row = tab.currentRow()
        current_text = tab.currentItem().text()

        not_unique = [row for row in range(tab.rowCount()-1) if(
                row != current_row
                and tab.currentItem()
                and tab.item(row, current_column).text() == current_text)]
        if not_unique:
            QMessageBox.warning(self, "Поле не уникально!",
                                "Запись не будет добавлена в таблицу.")
            tab.setRowCount(tab.rowCount()-1)

    def out(self):
        self.save_table()
        self.close()

    def insert_to_table(self,lst_table,tab):
        """
         вставляем данные из БД в QTableWidget
        :param lst_table: записи из БД, которые нужно вставить
        :param tab: QTableWidget, куда вставляем
        :return i: количество вставленных записей
        """
        i = 0  # на случай, если в базе пусто
        tab.blockSignals(True)  # блокируем сигналы в QWidgetTable
        for i,row in enumerate(lst_table):
            tab.insertRow(i)
            for j in range(0,tab.columnCount()):
                tab.setItem(i, j, QtWidgets.QTableWidgetItem(str(row[j])))
        tab.blockSignals(False)  # разблокируем сигналы
        return 0 if i == 0 else i+1

    def insert_btn_choice(self, i, j):
        self.btn_choice = QPushButton('...')
        self.btn_choice.setSizePolicy(QtWidgets.QSizePolicy.Ignored,
                                      QtWidgets.QSizePolicy.Maximum)
        self.table.setCellWidget(i, j, self.btn_choice)
        self.btn_choice.clicked.connect(self.btn_choice_clicked)

    # по нажатию кнопки (...)
    # вставляем в 1 столбец таблицы QComboBox со значениями
    def btn_choice_clicked(self):
        # вставляем в текущую строку QComboBox()
        row_position = self.table.currentRow()
        self.res_box = QComboBox()
        self.table.setCellWidget(row_position, 1, self.res_box)
        self.res_box.activated.connect(self.change_res_box)
        # формируем список для выбора
        # nonames - этих наименований не должно быть в списке для выбора
        nonames = [self.res_box.currentText()]
        for row in range(row_position):
            if self.table.item(row, 1):
                txt = self.table.item(row, 1).text()
                nonames += [txt]
        #nonames += [self.table.item(row, 1).text() for row in range(row_position)]
        fnames = [x for x in self.names if x not in nonames]
        self.res_box.addItems(fnames)

