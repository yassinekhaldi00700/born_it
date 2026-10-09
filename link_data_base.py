import pyodbc
import ast
def connect_to_data_base():
    DRIVER_NAME = 'ODBC Driver 17 for SQL Server'
    SERVER_NAME = 'ZAMO'
    DATABASE_NAME = 'Students'
  
    connection_string = f'''
    DRIVER={DRIVER_NAME};
    SERVER={SERVER_NAME};
    DATABASE={DATABASE_NAME};
    Trusted_Connection=yes;
    '''
    cnxn = pyodbc.connect(connection_string)
    print(cnxn)
    global cursor
    cursor = cnxn.cursor()

def (get_data)(id):
    query = "SELECT * FROM Student where id={}".format(id)
    cursor.execute(query)
    row = cursor.fetchone()
    if row == None :
        return "Contacter DSI"
    return row


