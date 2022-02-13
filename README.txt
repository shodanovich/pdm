1. Структура базы данных.
Используется СУБД MySql версии 8.0.28
База данных называется PDM
Таблицы:
	resources (ресурсы)
		 resources (
                    id INT PRIMARY KEY,		# id ресурса
                    name VARCHAR(256),		# наименование ресурса
                    measure VARCHAR(10)         # единица измерения
                    )
	costs (затраты)
		costs ( 
                    res1_id INT,		# id ресурса, который затрачивается
                    res2_id INT,		# id изделия
                    cost FLOAT			# затраты на единицу
                    )
	professions (профессии)
		professions (
		    id INT,			# id профессии
		    name VARCHAR(100)		# наименование
		    rate FLOAT			# расценка за 1 час
		    )
