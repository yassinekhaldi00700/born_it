import pyodbc
import pandas as pd
from databasekonosys import connect_to_db_konosys

def dump_planning_procedure_data(matricule):
    """
    Dump header and data from getplanningStudent procedure for a given matricule
    """
    cnxn = connect_to_db_konosys()
    if not cnxn:
        print("Failed to connect to database")
        return
    
    cursor = cnxn.cursor()
    
    try:
        # Call the stored procedure
        print(f"Calling getplanningStudent procedure for matricule: {matricule}")
        print("=" * 60)
        
        # Execute the stored procedure
        cursor.execute("EXEC getplanningStudent ?", matricule)
        
        # Get column information (header)
        columns = [column[0] for column in cursor.description]
        print("PROCEDURE HEADER:")
        print("-" * 40)
        for i, col in enumerate(columns, 1):
            print(f"{i:2d}. {col}")
        
        print("\n" + "=" * 60)
        print("PROCEDURE DATA:")
        print("-" * 40)
        
        # Fetch all data
        rows = cursor.fetchall()
        
        if rows:
            # Print data in a formatted way
            for row_num, row in enumerate(rows, 1):
                print(f"\nRow {row_num}:")
                for col_name, value in zip(columns, row):
                    print(f"  {col_name}: {value}")
                print("-" * 30)
            
            print(f"\nTotal rows returned: {len(rows)}")
            
            # Also create a pandas DataFrame for better visualization
            df = pd.DataFrame.from_records(rows, columns=columns)
            print("\nData as DataFrame:")
            print(df.to_string(index=False))
            
            # Save to CSV for further analysis
            csv_filename = f"planning_data_{matricule}.csv"
            df.to_csv(csv_filename, index=False)
            print(f"\nData saved to: {csv_filename}")
            
        else:
            print("No data returned from the procedure")
            
    except pyodbc.Error as e:
        print(f"Error executing procedure: {str(e)}")
        
        # Try to get more information about the procedure
        try:
            print("\nAttempting to get procedure information...")
            cursor.execute("""
                SELECT 
                    ROUTINE_NAME,
                    ROUTINE_DEFINITION,
                    ROUTINE_TYPE
                FROM INFORMATION_SCHEMA.ROUTINES 
                WHERE ROUTINE_NAME = 'getplanningStudent'
            """)
            proc_info = cursor.fetchall()
            if proc_info:
                print("Procedure found in database:")
                for info in proc_info:
                    print(f"Name: {info[0]}")
                    print(f"Type: {info[2]}")
                    if info[1]:
                        print(f"Definition: {info[1][:500]}...")
            else:
                print("Procedure 'getplanningStudent' not found in INFORMATION_SCHEMA.ROUTINES")
                
        except Exception as info_error:
            print(f"Could not retrieve procedure information: {info_error}")
            
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        
    finally:
        cursor.close()
        cnxn.close()

def check_procedure_exists():
    """
    Check if the getplanningStudent procedure exists in the database
    """
    cnxn = connect_to_db_konosys()
    if not cnxn:
        print("Failed to connect to database")
        return
    
    cursor = cnxn.cursor()
    
    try:
        # Check for stored procedures
        cursor.execute("""
            SELECT name, type_desc, create_date, modify_date
            FROM sys.objects 
            WHERE type IN ('P', 'PC') 
            AND name LIKE '%planning%'
            ORDER BY name
        """)
        
        procedures = cursor.fetchall()
        print("Procedures containing 'planning':")
        print("-" * 50)
        
        if procedures:
            for proc in procedures:
                print(f"Name: {proc[0]}")
                print(f"Type: {proc[1]}")
                print(f"Created: {proc[2]}")
                print(f"Modified: {proc[3]}")
                print("-" * 30)
        else:
            print("No procedures found containing 'planning'")
            
        # Also check for any procedure with 'student' in the name
        cursor.execute("""
            SELECT name, type_desc, create_date, modify_date
            FROM sys.objects 
            WHERE type IN ('P', 'PC') 
            AND name LIKE '%student%'
            ORDER BY name
        """)
        
        student_procedures = cursor.fetchall()
        print("\nProcedures containing 'student':")
        print("-" * 50)
        
        if student_procedures:
            for proc in student_procedures:
                print(f"Name: {proc[0]}")
                print(f"Type: {proc[1]}")
                print(f"Created: {proc[2]}")
                print(f"Modified: {proc[3]}")
                print("-" * 30)
        else:
            print("No procedures found containing 'student'")
            
    except Exception as e:
        print(f"Error checking procedures: {str(e)}")
        
    finally:
        cursor.close()
        cnxn.close()

if __name__ == "__main__":
    matricule = "2500478"
    
    print("Checking if procedure exists...")
    check_procedure_exists()
    
    print("\n" + "=" * 80)
    print("Attempting to dump planning procedure data...")
    print("=" * 80)
    
    dump_planning_procedure_data(matricule)