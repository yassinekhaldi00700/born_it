import pyodbc
from databasekonosys import connect_to_db_konosys

def get_planning_student_result(matricule):
    """
    Call getplanningStudent procedure and return results
    """
    cnxn = connect_to_db_konosys()
    if not cnxn:
        print("Failed to connect to database")
        return
    
    cursor = cnxn.cursor()
    
    try:
        # Call the procedure
        cursor.execute("EXEC getplanningStudent ?", matricule)
        
        # Get column headers
        columns = [column[0] for column in cursor.description]
        print("HEADER:")
        for i, col in enumerate(columns, 1):
            print(f"{i}. {col}")
        
        # Get data
        rows = cursor.fetchall()
        print(f"\nDATA ({len(rows)} records):")
        
        for row_num, row in enumerate(rows, 1):
            print(f"\nRow {row_num}:")
            for col_name, value in zip(columns, row):
                print(f"  {col_name}: {value}")
                
    except Exception as e:
        print(f"Error: {str(e)}")
        
    finally:
        cursor.close()
        cnxn.close()

if __name__ == "__main__":
    get_planning_student_result('2501101')