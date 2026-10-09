import mysql.connector
from mysql.connector import Error
import sys
import traceback

def connect_to_mysql():
    import socket
    import signal
    
    def timeout_handler(signum, frame):
        raise TimeoutError("MySQL connection timeout")
    
    try:
        print(f"[DB] Testing network connectivity to 172.16.80.161:3306...")
        sys.stdout.flush()
        
        # Test if we can reach the host first (with short timeout)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(3)  # 3 second timeout
        result = sock.connect_ex(('172.16.80.161', 3306))
        sock.close()
        
        if result != 0:
            print(f"[DB] Cannot reach database server (port closed or host unreachable)")
            sys.stdout.flush()
            return None
        
        print(f"[DB] Network connection OK, attempting MySQL connection...")
        sys.stdout.flush()
        
        # Try connection with multiple fallback options
        connection_configs = [
            # First try: with SSL disabled
            {
                'host': "172.16.80.161",
                'port': 3306,
                'user': "datashap",
                'password': "datashap@2026",
                'database': "collectivite",
                'connect_timeout': 3,
                'autocommit': True,
                'ssl_disabled': True,
                'use_pure': True  # Use pure Python implementation
            },
            # Second try: force no SSL
            {
                'host': "172.16.80.161",
                'port': 3306,
                'user': "datashap",
                'password': "datashap@2026",
                'database': "collectivite",
                'connect_timeout': 3,
                'autocommit': True,
                'ssl_disabled': True
            }
        ]
        
        for idx, config in enumerate(connection_configs):
            try:
                print(f"[DB] Attempt {idx + 1}/2...")
                sys.stdout.flush()
                mydb = mysql.connector.connect(**config)
                print("[DB] Database connected successfully!")
                sys.stdout.flush()
                return mydb
            except Exception as conn_err:
                print(f"[DB] Attempt {idx + 1} failed: {conn_err}")
                sys.stdout.flush()
                if idx < len(connection_configs) - 1:
                    continue
                else:
                    raise
        
        return None
        
    except socket.timeout:
        print(f"[DB] Connection timeout - database server not responding")
        sys.stdout.flush()
        return None
    except socket.error as se:
        print(f"[DB] Network error: {se}")
        sys.stdout.flush()
        return None
    except TimeoutError as te:
        print(f"[DB] MySQL connection timeout: {te}")
        sys.stdout.flush()
        return None
    except Error as e:
        print(f"[DB] MySQL connection failed: {e}")
        sys.stdout.flush()
        return None
    except Exception as e:
        print(f"[DB] Unexpected error: {e}")
        traceback.print_exc()
        sys.stdout.flush()
        return None

def solde(mat):
    try:
        print(f"[solde] Getting balance for matricule: {mat}")
        sys.stdout.flush()
        
        mydb = connect_to_mysql()
        if mydb is None:
            print("[solde] Database connection returned None - returning 0.00")
            sys.stdout.flush()
            return "0.00"
        
        mycursor = mydb.cursor()
        
        print(f"[solde] Executing SQL query...")
        sys.stdout.flush()
        
        mycursor.execute(
            "SELECT nouveau_solde FROM collectivite.compte ce "
            "INNER JOIN collectivite.compt c ON ce.matricule = c.matricule "
            "WHERE matricule_Societe = %s", (mat,)
        )
        
        print(f"[solde] Query executed, fetching results...")
        sys.stdout.flush()
        
        result_string = ""
        row_count = 0
        for row in mycursor:
            nouveau_solde = row[0]
            result_string += f"{float(nouveau_solde):.2f}\n"
            row_count += 1
        
        mycursor.close()
        mydb.close()
        
        print(f"[solde] Found {row_count} records. Result: {result_string.strip()}")
        sys.stdout.flush()
        
        return result_string.strip() if result_string else "0.00"
        
    except Error as e:
        print(f"[solde] MySQL ERROR: {e}")
        traceback.print_exc()
        sys.stdout.flush()
        return "0.00"
    except Exception as e:
        print(f"[solde] UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        sys.stdout.flush()
        return "0.00"
    
def historique(mat):
    try:
        print(f"[historique] Getting history for matricule: {mat}")
        sys.stdout.flush()
        
        mydb = connect_to_mysql()
        if mydb is None:
            print("[historique] Database connection returned None - returning empty")
            sys.stdout.flush()
            return ""
        
        mycursor = mydb.cursor()
        
        print(f"[historique] Executing SQL query...")
        sys.stdout.flush()
        
        mycursor.execute(
            "SELECT num_ticket, nom_article, qut_article, famille_art, "
            "prix_total_S, prix_total_P, date_jour, heure_vente "
            "FROM collectivite.ventes v "
            "INNER JOIN collectivite.compt c ON v.num_compte = c.matricule "
            "WHERE matricule_Societe = %s", (mat,)
        )
        
        result_string = ""
        row_count = 0
        for row in mycursor:
            result_string += f"{row}\n"
            row_count += 1
        
        mycursor.close()
        mydb.close()
        
        print(f"[historique] Found {row_count} records")
        sys.stdout.flush()
        
        return result_string
        
    except Error as e:
        print(f"[historique] MySQL ERROR: {e}")
        traceback.print_exc()
        sys.stdout.flush()
        return ""
    except Exception as e:
        print(f"[historique] UNEXPECTED ERROR: {e}")
        traceback.print_exc()
        sys.stdout.flush()
        return ""







def string_data_to_html(data):
    rows = [line.split(", ") for line in data.split("\n") if line.strip()]
    if not rows:
        return "<table></table>"

    headers = ["num_ticket", "nom_article", "quantite", "famille", "prix_total", "prix_total_P", "date_jour", "heure_vente"]
    html_table = "<table border='1'>\n"

    # Add headers
    html_table += "<tr>"
    for header in headers:
        html_table += f"<th>{header}</th>"
    html_table += "</tr>\n"

    # Reverse the rows (excluding header)
    for row in reversed(rows):
        html_table += "<tr>"
        for cell in row:
            html_table += f"<td>{cell.strip('()')}</td>"
        html_table += "</tr>\n"

    html_table += "</table>"
    return html_table


def get_history(id):
    data = str(historique(id))
    data=data.replace(")", "")
    data=data.replace("(", "")
    html_table = string_data_to_html(data)
    return html_table
