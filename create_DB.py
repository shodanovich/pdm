from PyQt5 import QtCore, QtWidgets
from mysql.connector import connect, Error
from mysql_dbconf_io import get_db_params

class CreateDB(QtWidgets.QWidget):
    def __init__(self,parent=None):
        super().__init__(parent,QtCore.Qt.Window)
        # окно
        self.setGeometry(300,300,400,400)
        self.setWindowTitle('Создание ДБ')
        btn = QtWidgets.QPushButton("Create")
        btn.clicked.connect(self.create_db)

        self.info_label = QtWidgets.QLabel()
        vlayout = QtWidgets.QVBoxLayout()
        vlayout.addWidget(btn)
        vlayout.addStretch(1)
        vlayout.addWidget(self.info_label)

        self.setLayout(vlayout)

    def create_db(self):
        """Create Data Base pdm """
        db_config = get_db_params()
        try:
            conn = connect(**db_config)
        except Error as e:
            # находим в db_config базу данных и удаляем
            del db_config["database"]
            conn = connect(**db_config)
        finally:
            cursor = conn.cursor()
            cursor.execute("DROP DATABASE IF EXISTS pdm;")
            cursor.execute("CREATE DATABASE pdm;")
            conn.close()
        #Create Tables
        try:
            db_config = get_db_params()
            conn = connect(**db_config)
            cursor = conn.cursor()
            create_tables_query = """
                CREATE TABLE resources (
                    id INT PRIMARY KEY,
                    name VARCHAR(256),
                    measure VARCHAR(10)      
                    );
                CREATE TABLE costs ( 
                    res1_id INT,
                    res2_id INT,
                    cost FLOAT
                    );
                    """
            cursor.execute(create_tables_query)
            self.info_label.setText("БД создана")
        except Error as e:
            print("Error: ", e)
        finally:
            conn.close()