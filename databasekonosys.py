import pyodbc

from config import env


def connect_to_db_konosys():
    try:
        cnxn = pyodbc.connect(
            driver="{SQL Server}",
            server=env("KONOSYS_SERVER"),
            database=env("KONOSYS_DATABASE", "Konosys_UEMF_Production"),
            uid=env("KONOSYS_USER"),
            pwd=env("KONOSYS_PASSWORD"),
            timeout=5,
        )
        print("Connected to the Konosys database successfully.")
        return cnxn
    except pyodbc.Error as e:
        print(f"Error connecting to the Konosys database: {str(e)}")
        return None


def get_data_konosys(id):
    student_konsys = {"e-mail":"","user_name":""}

    # Create connection for each query
    cnxn = connect_to_db_konosys()
    if not cnxn:
        return student_konsys

    cursor = cnxn.cursor()

    try:
        # Get username and email
        query = "select Username, MailGEM from dbo.ERP_User u inner join dbo.ERP_Etudiant e on u.id_user = e.id_user where MatriculeEtudiant = ?"
        cursor.execute(query, str(id))
        row = cursor.fetchone()
        if row is not None:
            student_konsys["user_name"] = [row[0]]
            student_konsys["e-mail"] = [row[1]]

    except pyodbc.Error as e:
        print(f"Error executing query: {str(e)}")
    finally:
        cursor.close()
        cnxn.close()

    return student_konsys
