from mysql.connector import connect, Error
from mysql_dbconf import get_db_params

def create_db():
    """ Create Data Base pdm """
    db_config = get_db_params()
    # находим в db_config базу данных и удаляем
    db_name = db_config["database"]
    del db_config["database"]
    try:
        conn = connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE " + db_name)
        conn.close()
    except Error as e:
        print(e)

    #Create Tables
    try:
        db_config = get_db_params()
        conn = connect(**db_config)
        cursor = conn.cursor()
        create_tables_query = """
            CREATE TABLE resources (
                id INT PRIMARY KEY,
                name VARCHAR(256),
                measure VARCHAR(10),
                typeres CHAR(1)
                );
            CREATE TABLE costs ( 
                res1_id INT,
                res2_id INT,
                cost FLOAT
                );
            CREATE TABLE shiftrep (
                daterep DATE,
                id INT,
                count FLOAT
                );
            CREATE TABLE inventory (
                id INT,
                count FLOAT,
                price FLOAT,
                date_purchase DATE);    
                """
        cursor.execute(create_tables_query)
    except Error as e:
        print("Error: ", e)
    finally:
        conn.close()