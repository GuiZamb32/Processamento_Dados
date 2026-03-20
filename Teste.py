from sqlite3 import dbapi2 as dbapi

try:
    db_connection = dbapi.connect('BancoCentral.db')
    cursor = db_connection.cursor()
    cursor2 = db_connection.cursor()

    # cursor.execute("""CREATE TABLE produto (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             nome VARCHAR(250),
    #             categoria VARCHAR(200),
    #             unidade_medida VARCHAR(2))""")
    

    # cursor.execute("""CREATE TABLE cesta_basica (
    #             id INTEGER PRIMARY KEY AUTOINCREMENT,
    #             tipo VARCHAR(50),
    #             valor_total (float)""")
    
    cursor.execute("""CREATE TABLE item_produto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome VARCHAR(250),
                preco_unidade FLOAT,
                quantidade_embalagem FLOAT,
                data_coleta DATE)""")

    db_connection.commit()


finally:

    db_connection.close()


