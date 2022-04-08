import pandas as pd
from mysql.connector import connect, Error
from mysql_dbconf import get_db_params


it_lst = []

def read_table(param=''):
    result = ()
    db_config = get_db_params()
    try:
        with connect(**db_config) as conn:
            cursor = conn.cursor()
            cursor.execute(param)
            result = cursor.fetchall()  # читаем всё
    except Error as e:
        print("Error: ", e)
    finally:
        return result

# затраты на единицу продукции
def get_costs(ids):
    # читаем все нормативы затрат
    query = "SELECT res1_id, res2_id, cost FROM costs"
    lst = read_table(query)
    # собираем затраты на id_
    global it_lst
    it_lst = []
    for id_ in ids:
        cost = 1
        eval_costs(id_, lst, cost)
        # убираем из списка материалов полуфабрикаты
        zlst = list(zip(*it_lst))  # транспонируем список
        res_ids = zlst[1]  # коды ресурсов, куда входит res_id1
        it_lst = [x1 for x1 in it_lst if x1[0] not in res_ids]
        # заменяем вторые коды на id_
        for row in it_lst:
            if row[1] not in ids:
                row[1] = id_

    it_lst.sort(key=lambda res_id: res_id[1])  # сортируем по второму коду
    it_lst.sort(key=lambda res_id: res_id[0])  # сортируем по первому коду

    # свернем по этим кодам:
    lst_s = pack(it_lst,[0,1],*[2])
    return lst_s

# затраты покупных материалов на изделие
def eval_costs(id_, lst, cost = 1):
    lst1 = [list(x) for x in lst if x[1]==id_]
    if not lst1:
        return
    for i, row in enumerate(lst1):
        row[2] *= cost
        it_lst.append(row)
        id_ = row[0]
        eval_costs(id_, lst, row[2])

def pack(lst, lst_pack, numr_sum):
    """
    свернуть и подсуммировать по заданным полям
    :param lst: исходный список
    :param lst_pack: список коэффициентов lst для упаковки
    :param numr_sum: список коэффициентов lst для суммирования
    :return: lst_it: свернутый список
    """
    df = pd.DataFrame(lst)
    df = df.groupby(lst_pack)[numr_sum].sum()
    lst_s = list(dict(df).items())
    lst_it = []
    if len(lst_pack) > 1:
        for i in range(len(lst_s)):
            l1 = list(lst_s[i][0])
            for j in range(1,len(lst_s[i])):
                l1.append(lst_s[i][j])
            lst_it.append(l1)
    else:
        lst_it = [list(x) for x in lst_s]

    return lst_it

def get_resources():
    query = """
    SELECT DISTINCT resources.* from resources, costs
    WHERE resources.id = costs.res1_id 
    AND NOT EXISTS (SELECT * FROM costs WHERE resources.id = costs.res2_id) 
    """
    return(read_table(query))

def get_prod():
    # изделия
    query = """
       SELECT id, name, measure FROM resources
       WHERE NOT EXISTS(
          SELECT res1_id from costs
          WHERE res1_id = resources.id
          )
       ORDER BY name
       """
    return(read_table(query))

