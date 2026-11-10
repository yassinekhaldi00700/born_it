from flask import Flask, render_template, request, redirect, url_for, request, session,jsonify, abort
#just for test 
from werkzeug.exceptions import HTTPException
# from link_data_base import *
from databasebiostar import *
from microsoft365 import *
from konosys_reset import *
from solde_carte import *
from databasekonosys import *
from ADPasswd import *
from markupsafe import Markup
import time
import traceback
import json
import sys
import os

# Debug function like Laravel's dd()
def dd(variable, message="DEBUG"):
    """Debug and die - like Laravel's dd() function"""
    debug_info = f"""
    <h1>{message}</h1>
    <pre style='background: #f8f9fa; padding: 20px; border: 1px solid #ddd; font-family: monospace;'>
    Type: {type(variable)}
    Value: {json.dumps(variable, indent=2, default=str)}
    </pre>
    """
    abort(500, debug_info)

###########################################################################deas
app = Flask(__name__)

# Technical details (card numbers, Python errors) are for the DSI, not for users.
# They always go to the console; set KIOSK_SHOW_ERRORS=1 in .env to also show them on screen.
SHOW_ERROR_DETAILS = os.environ.get("KIOSK_SHOW_ERRORS", "0") == "1"

MSG_NOT_FOUND = "Carte non reconnue. Vérifiez que vous avez choisi le bon profil, puis passez à nouveau votre carte."
MSG_UNAVAILABLE = "Le service est momentanément indisponible. Veuillez réessayer dans quelques instants."

def error_page(message, technical=None, exc=None, status=200):
    """Error screen: a simple message for the user, the details for the console."""
    trace = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__)) if exc else None
    print(f"[ERREUR] {message}" + (f" | {technical}" if technical else ""))
    if trace:
        print(trace)
    sys.stdout.flush()
    if SHOW_ERROR_DETAILS:
        return render_template("error.html", error_code=technical or message, error_detail=trace), status
    return render_template("error.html", error_code=message), status
###########################################################################

student_info = {"name":"","matricule":"","solde_carte":"","e-mail":"","solde_imp":"","user_name":""}
requestSQL=""
###########################################################################
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)
@app.route('/')
def index():
    return render_template('index.html')    
###########################################################################


###########################################################################
user_input=""
@app.route('/result', methods=['POST'])
def result():
    try:
        global user_input
        if request.method == 'POST':
            user_input = request.form.get('user_input', '')
            print(f"Card ID received: {user_input}")
            sys.stdout.flush()  # Force output to show immediately
            return render_template('result.html')
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"ERROR in /result route:")
        print(f"{'='*50}")
        print(traceback.format_exc())
        print(f"{'='*50}\n")
        sys.stdout.flush()
        return error_page("Lecture de la carte impossible. Veuillez passer à nouveau votre carte.",
                          f"Erreur lecture carte : {e}", exc=e, status=500)
###########################################################################
#############STUDENTBUTTON
@app.route('/STUDENTBUTTON', methods=['POST'])
def STUDENTBUTTON():
    try:
        print(f"\n{'='*50}")
        print(f"STUDENTBUTTON route called")
        print(f"User input: {user_input}")
        print(f"{'='*50}\n")
        sys.stdout.flush()
        
        global student_info
        student=get_data(user_input,"S")
        
        print(f"Student data retrieved: {student}")
        sys.stdout.flush()
        
        if student is None or not student["name"]:
            print("Student not found in database")
            sys.stdout.flush()
            msb = swap_byte_order(user_input) if str(user_input).strip().isdigit() else "?"
            return error_page(MSG_NOT_FOUND, f"Étudiant introuvable dans BioStar 2 (carte lue : {user_input}, MSB : {msb})")
        
        student_name = student["name"]
        student_matricule = student["id"]
        student_email = student["e-mail"] or ""
        
        print(f"Student info - Name: {student_name}, Matricule: {student_matricule}")
        sys.stdout.flush()
        
        #info fill:
        student_info["name"]=student_name
        student_info["e-mail"]=student_email
        student_info["matricule"]=student_matricule
        
        # Try to get student balance
        try:
            print(f"Fetching balance for matricule: {student_info['matricule']}")
            sys.stdout.flush()
            student_solde = (solde(int(student_info["matricule"])))
            print(f"Balance retrieved: {student_solde}")
            sys.stdout.flush()
        except ValueError as ve:
            print(f"ValueError getting balance: {ve}")
            traceback.print_exc()
            sys.stdout.flush()
            student_solde = "0.00"
        except Exception as e:
            print(f"Error getting balance: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            student_solde = "0.00"
        
        student_info["solde_carte"]=student_solde

        # --- DISABLED: Konosys SQL lookup (replaced by the KONOSYS API below). Kept for reference. ---
        # try:
        #     print("Fetching Konosys data...")
        #     sys.stdout.flush()
        #     konosys_info=get_data_konosys(int(student_info["matricule"]))
        #     try:
        #         USERNAME =  [elem for elem in konosys_info["e-mail"]]
        #         student_info["e-mail"]=USERNAME[0]
        #     except (TypeError, IndexError):
        #         # Keep the original email if Konosys fails
        #         student_info["e-mail"] = student_email
        #
        #     try:
        #         Email =  [elem for elem in konosys_info["user_name"]]
        #         student_info["user_name"]=Email[0]
        #     except (TypeError, IndexError):
        #         student_info["user_name"] = ""
        # except Exception as e:
        #     # If Konosys completely fails, use default values
        #     print(f"Konosys error (non-critical): {e}")
        #     sys.stdout.flush()
        #     student_info["e-mail"] = student_email
        #     student_info["user_name"] = ""

        # Professional e-mail from the KONOSYS API (falls back to the BioStar e-mail)
        mail_pro = get_mail_professionnel(student_info["matricule"])
        if mail_pro:
            print(f"KONOSYS API professional e-mail: {mail_pro}")
        student_info["e-mail"] = mail_pro or student_email
        # AD username = part before @ (same rule as the teacher route /resetAD1)
        email = student_info["e-mail"] or ""
        student_info["user_name"] = email.split("@")[0] if "@" in email else ""
        sys.stdout.flush()

        # Try to get history, but don't fail if it doesn't work
        try:
            print("Fetching purchase history...")
            sys.stdout.flush()
            hist=get_history(int(student_info["matricule"]))
            hist = Markup(hist)
            print("History retrieved successfully")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error getting history (non-critical): {e}")
            traceback.print_exc()
            sys.stdout.flush()
            hist = Markup("<p>Historique non disponible</p>")

        print("Rendering services.html template")
        sys.stdout.flush()
        return render_template('services.html', student_name=student_info["name"],matricule=student_info["matricule"],solde_carte=student_info["solde_carte"],e_mail=student_info["e-mail"],hist=hist,student=student,user_type="student")
        
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"FATAL ERROR in /STUDENTBUTTON route:")
        print(f"{'='*50}")
        print(traceback.format_exc())
        print(f"{'='*50}\n")
        sys.stdout.flush()
        return error_page(MSG_UNAVAILABLE, f"{type(e).__name__} : {e}", exc=e, status=500)
#############TEACHERBUTTON
@app.route('/TEACHERBUTTON', methods=['POST'])
def TEACHERBUTTON():
    try:
        print(f"\n{'='*50}")
        print(f"TEACHERBUTTON route called")
        print(f"User input: {user_input}")
        print(f"{'='*50}\n")
        sys.stdout.flush()
        
        global student_info
        student=get_data(user_input,"T")
        
        print(f"Teacher data retrieved: {student}")
        sys.stdout.flush()
        
        if student is None or not student["name"]:
            print("Teacher not found in database")
            sys.stdout.flush()
            return error_page(MSG_NOT_FOUND, f"Enseignant introuvable dans BioStar 1 (carte lue : {user_input})")
        
        student_name = student["name"]
        student_matricule = student["id"]
        student_email = student["e-mail"] or ""
        
        print(f"Teacher info - Name: {student_name}, Matricule: {student_matricule}")
        sys.stdout.flush()
        
        #info fill:
        student_info["name"]=student_name
        student_info["e-mail"]=student_email
        student_info["matricule"]=student_matricule
        
        # Try to get balance
        try:
            print(f"Fetching balance for matricule: {student_info['matricule']}")
            sys.stdout.flush()
            student_solde = (solde(int(student_info["matricule"])))
            print(f"Balance retrieved: {student_solde}")
            sys.stdout.flush()
        except (ValueError, Exception) as e:
            print(f"Error getting balance: {e}")
            traceback.print_exc()
            sys.stdout.flush()
            student_solde = "0.00"
        
        student_info["solde_carte"]=student_solde
        
        # Try to get history
        try:
            print("Fetching purchase history...")
            sys.stdout.flush()
            hist=get_history(int(student_info["matricule"]))
            hist = Markup(hist)
            print("History retrieved successfully")
            sys.stdout.flush()
        except Exception as e:
            print(f"Error getting history (non-critical): {e}")
            traceback.print_exc()
            sys.stdout.flush()
            hist = Markup("<p>Histoire non disponible</p>")
        
        print("Rendering services.html template")
        sys.stdout.flush()
        return render_template('services.html', student_name=student_info["name"],matricule=student_info["matricule"],solde_carte=student_info["solde_carte"],e_mail=student_info["e-mail"],hist=hist,user_type="teacher")
        
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"FATAL ERROR in /TEACHERBUTTON route:")
        print(f"{'='*50}")
        print(traceback.format_exc())
        print(f"{'='*50}\n")
        sys.stdout.flush()
        return error_page(MSG_UNAVAILABLE, f"{type(e).__name__} : {e}", exc=e, status=500)
#---------------------------------------#

#############B1
@app.route('/SOLDECARTE', methods=['POST'])
def SOLDECARTE():
    return render_template('solde_carte_page.html',solde_carte=0)
#############B2
@app.route('/RESETOUTLOOK', methods=['POST'])
def RESETOUTLOOK():
    return render_template('reset_outlook.html', msg_outlook="")
#############B3
@app.route('/HISTORY', methods=['POST'])
def HISTORY():
    return render_template('historique_achat.html', history="")
#############B4
@app.route('/PLANNING', methods=['POST'])
def PLANNING():
    return render_template('planning.html', planning="")
#############B5
@app.route('/RESETKONOSYS', methods=['POST'])
def RESETKONOSYS():
    return render_template('reset_konosys.html', msg_konosys="")
#############B6
@app.route('/SOLDEIMP', methods=['POST'])
def SOLDEIMP():
    return render_template('solde_imp_page.html', solde_imp=0)




@app.route('/resetoutlook')
def resetoutlook():
    try:
        result = reset_passwd_outlook(student_info["e-mail"])
        if result is None:
            return jsonify({'variable': '❌ Password reset failed. Please check backend logs for details.'})
        return jsonify({'variable': result})
    except Exception as e:
        print(f"Error in resetoutlook: {e}")
        return jsonify({'variable': '❌ Service temporarily unavailable. Please try again later.'})

@app.route('/resetkonosys')
def resetkonosys():
    try:
        msg_konosys = reset_passwd_konosys(student_info["matricule"], student_info.get("e-mail"))
        return jsonify({'variable': msg_konosys})
    except Exception as e:
        print(f"Error in resetkonosys: {e}")
        return jsonify({'variable': '❌ Service temporarily unavailable. Please try again later.'})

@app.route('/resetAD')
def resetAD():
    try:
        msg_AD = reset_passwd_AD(student_info["user_name"])
        return jsonify({'variable': msg_AD})
    except Exception as e:
        print(f"Error in resetAD: {e}")
        return jsonify({'variable': '❌ Service temporarily unavailable. Please try again later.'})

@app.route('/resetAD1')
def resetAD1():
    try:
        # For teachers, extract username from email (part before @)
        email = student_info["e-mail"]
        username = email.split('@')[0] if '@' in email else email
        msg_AD = reset_passwd_AD(username)
        return jsonify({'variable': msg_AD})
    except Exception as e:
        print(f"Error in resetAD1: {e}")
        return jsonify({'variable': '❌ Service temporarily unavailable. Please try again later.'})

@app.route('/getplanning')
def getplanning():
    try:
        # Get current student matricule
        matricule = student_info.get("matricule", "2501101")  # Use stored matricule or working default
        
        # Connect to Konosys database
        cnxn = connect_to_db_konosys()
        if not cnxn:
            return jsonify({'error': 'Database connection failed'})
        
        cursor = cnxn.cursor()
        
        try:
            # Call the actual getplanningStudent procedure
            cursor.execute("EXEC getplanningStudent ?", matricule)
            
            # Get column headers  
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            
            cursor.close()
            cnxn.close()
            
            # Format the data for frontend
            formatted_planning = []
            
            # Day names mapping
            day_names = {
                1: 'Lundi',
                2: 'Mardi', 
                3: 'Mercredi',
                4: 'Jeudi',
                5: 'Vendredi',
                6: 'Samedi',
                7: 'Dimanche'
            }
            
            for row in rows:
                row_dict = dict(zip(columns, row))
                
                # Calculate actual start and end times
                hd = row_dict.get('HD', '')
                min_deb = row_dict.get('minDeb', 0) or 0
                duree_min = row_dict.get('DureeMin', 0) or 0
                
                # Calculate start time with delay
                start_time = hd
                if hd and min_deb > 0:
                    try:
                        from datetime import datetime, timedelta
                        time_obj = datetime.strptime(hd, '%H:%M')
                        start_with_delay = time_obj + timedelta(minutes=min_deb)
                        start_time = start_with_delay.strftime('%H:%M')
                    except:
                        pass
                
                # Calculate end time
                end_time = "Open"
                if hd and duree_min > 0:
                    try:
                        from datetime import datetime, timedelta
                        time_obj = datetime.strptime(start_time, '%H:%M')
                        end_time_obj = time_obj + timedelta(minutes=duree_min)
                        end_time = end_time_obj.strftime('%H:%M')
                    except:
                        end_time = "Open"
                
                formatted_planning.append({
                    'day_num': row_dict.get('numDay', 0),
                    'day_name': day_names.get(row_dict.get('numDay', 0), 'Inconnu'),
                    'heure_debut': start_time,
                    'heure_fin': end_time,
                    'titre': row_dict.get('Titre', '').strip() or 'Information',
                    'salle': row_dict.get('Salle', '').strip() or '',
                    'prof': row_dict.get('Prof', '').strip() or '',
                    'duree_min': duree_min,
                    'min_delay': min_deb
                })
            
            return jsonify({
                'matricule': matricule,
                'planning': formatted_planning,
                'total_records': len(formatted_planning)
            })
            
        except Exception as proc_error:
            cursor.close()
            cnxn.close()
            print(f"Procedure error: {proc_error}")
            return jsonify({'error': f'Procedure execution failed: {str(proc_error)}'})
        
    except Exception as e:
        print(f"Error in getplanning: {e}")
        return jsonify({'error': 'Service temporarily unavailable'})


###########################################################################

@app.errorhandler(Exception)
def handle_exception(e):
    # Print full error to console/logs
    print(f"\n{'='*50}")
    print(f"GLOBAL EXCEPTION HANDLER TRIGGERED:")
    print(f"{'='*50}")
    traceback.print_exc()
    print(f"{'='*50}\n")
    sys.stdout.flush()

    from werkzeug.exceptions import HTTPException
    if isinstance(e, HTTPException):
        return e

    return error_page(MSG_UNAVAILABLE, f"{type(e).__name__} : {e}", exc=e, status=500)


# ...existing code...

if __name__ == '__main__':
    try:
        print("\n" + "="*50)
        print("Starting Flask Application")
        print("="*50)
        print("Server running on http://0.0.0.0:5000")
        print("Press CTRL+C to quit")
        print("="*50 + "\n")
        sys.stdout.flush()
        
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    except KeyboardInterrupt:
        print("\n\nServer stopped by user (CTRL+C)")
        sys.stdout.flush()
    except Exception as e:
        print(f"\n{'='*50}")
        print(f"FATAL SERVER ERROR:")
        print(f"{'='*50}")
        print(traceback.format_exc())
        print(f"{'='*50}\n")
        sys.stdout.flush()
        raise

