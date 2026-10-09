from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from markupsafe import Markup
import datetime
import os
import requests
from msal import ConfidentialClientApplication

# Database and external service imports (assumed to be correct)
from databasebiostar import *
from konosys_reset import *
from solde_carte import *
from databasekonosys import *
from ADPasswd import *

###########################################################################
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or os.urandom(32)

# Initialize global variables
student_info = {"name": "", "matricule": "", "solde_carte": "", "e-mail": "", "solde_imp": "", "user_name": ""}
user_input = ""
error_code = ""

# Current date and time for logging
current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Microsoft Graph API credentials
# CLIENT_ID = "ff852716-f907-477e-8118-f6d7b13a3387"
# CLIENT_SECRET = "d3ed01e7-6fce-4072-8754-96796193c328"
# TENANT_ID = "503bb24f-b93f-45d6-8359-700a80b5cd0c"
# AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
# SCOPES = ["https://graph.microsoft.com/.default"]

###########################################################################

@app.route('/')
def index():
    return render_template('index.html')

###########################################################################

@app.route('/result', methods=['POST'])
def result():
    global user_input, error_code
    if request.method == 'POST':
        raw_input = request.form.get('user_input', '').strip()
        print(f"[{current_time}] Raw input received: '{repr(raw_input)}'")
        
        user_input = raw_input
        error_code = ""
        
        numeric_input = ''.join(char for char in user_input if char.isdigit())
        print(f"[{current_time}] Extracted numeric input: '{numeric_input}'")
        
        if not numeric_input:
            error_code = "Error: No valid number detected from card input!"
            return render_template("error.html", error_code=error_code, back_url=url_for('index'))
        
        user_input = numeric_input
        print(f"[{current_time}] Validated numeric input = {user_input}")
        return render_template('result.html')

###########################################################################

@app.route('/STUDENTBUTTON', methods=['POST'])
def STUDENTBUTTON():
    global student_info, error_code, user_input
    error_code = ""
    
    if not user_input or not user_input.isdigit():
        error_code = "Error: Invalid input detected!"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    
    try:
        student = get_data(int(user_input), "S")
        if student is None or not student["name"]:
            error_code = "Error 200: Student not found!"
            return render_template("error.html", error_code=error_code, back_url=url_for('index'))
        
        student_name = student["name"]
        student_matricule = student["id"] or ""
        student_email = student["e-mail"] or ""
    except Exception as e:
        error_code = f"Error 201: Failed to extract student data! {str(e)}"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    
    student_info["name"] = student_name
    student_info["e-mail"] = student_email
    student_info["matricule"] = student_matricule
    
    try:
        student_solde = solde(int(student_info["matricule"]))
    except Exception as e:
        error_code += "Error 300: Failed to fetch card balance! "
        student_solde = 0
    
    student_info["solde_carte"] = student_solde
    
    try:
        konosys_info = get_data_konosys(int(student_info["matricule"]))
        student_info["e-mail"] = konosys_info["e-mail"][0] if konosys_info["e-mail"] else student_email
        student_info["user_name"] = konosys_info["user_name"][0] if konosys_info["user_name"] else ""
    except Exception as e:
        error_code += f"Error 100: Failed to fetch Konosys info! {str(e)}"
    
    try:
        hist = get_history(int(student_info["matricule"]))
        hist = Markup(hist)
    except Exception as e:
        error_code += f"Error 400: Failed to fetch history! {str(e)}"
        hist = Markup("")
    
    return render_template('services.html', student_name=student_info["name"], solde_carte=student_info["solde_carte"], e_mail=student_info["e-mail"], hist=hist)

###########################################################################

@app.route('/TEACHERBUTTON', methods=['POST'])
def TEACHERBUTTON():
    global student_info, error_code, user_input
    error_code = ""
    
    if not user_input or not user_input.isdigit():
        error_code = "Error: Invalid input detected!"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    
    try:
        teacher = get_data(int(user_input), "T")
        if teacher is None or not teacher["name"]:
            error_code = "Error 200: Teacher not found!"
            return render_template("error.html", error_code=error_code, back_url=url_for('index'))
        
        student_name = teacher["name"]
        student_matricule = teacher["id"] or ""
        student_email = teacher["e-mail"] or ""
    except Exception as e:
        error_code = f"Error 201: Failed to extract teacher data! {str(e)}"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    
    student_info["name"] = student_name
    student_info["e-mail"] = student_email
    student_info["user_name"] = student_email.split("@")[0] if "@" in student_email else student_email
    student_info["matricule"] = student_matricule
    
    try:
        student_solde = solde(int(student_info["matricule"]))
    except Exception as e:
        error_code = "Error 300: Failed to fetch card balance!"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    
    student_info["solde_carte"] = student_solde
    
    try:
        hist = get_history(int(student_info["matricule"]))
        hist = Markup(hist)
    except Exception as e:
        error_code = f"Error 400: Failed to fetch history! {str(e)}"
        hist = Markup("")
    
    return render_template('services.html', student_name=student_info["name"], solde_carte=student_info["solde_carte"], e_mail=student_info["e-mail"], hist=hist)

###########################################################################

@app.route('/resetoutlook')
def resetoutlook():
    global error_code
    if "Error 100!" in error_code:
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    try:
        app_graph = ConfidentialClientApplication(
            CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
        )
        token = app_graph.acquire_token_for_client(scopes=SCOPES)

        if "access_token" not in token:
            raise Exception("Failed to acquire access token")

        headers = {
            "Authorization": f"Bearer {token['access_token']}",
            "Content-Type": "application/json"
        }
        new_password = "AutoGenerated123!"
        payload = {
            "passwordProfile": {
                "password": new_password,
                "forceChangePasswordNextSignIn": False
            }
        }

        response = requests.patch(
            f"https://graph.microsoft.com/v1.0/users/{student_info['e-mail']}",
            headers=headers,
            json=payload
        )

        if response.status_code != 204:
            raise Exception(f"Failed to reset password: {response.text}")

        return jsonify({'variable': new_password})
    except Exception as e:
        error_code = f"Error 500: Failed to reset Outlook password! {str(e)}"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))

###########################################################################

@app.route('/resetkonosys')
def resetkonosys():
    global error_code
    try:
        msg_konosys = reset_passwd_konosys(int(student_info["matricule"]))
        return jsonify({'variable': msg_konosys})
    except Exception as e:
        error_code = f"Error 501: Failed to reset Konosys password! {str(e)}"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))

###########################################################################

@app.route('/resetAD')
def resetAD():
    global error_code
    if "Error 100!" in error_code:
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))
    try:
        msg_AD = reset_passwd_AD(student_info["user_name"])
        return jsonify({'variable': msg_AD})
    except Exception as e:
        error_code = f"Error 502: Failed to reset AD password! {str(e)}"
        return render_template("error.html", error_code=error_code, back_url=url_for('index'))

###########################################################################
@app.errorhandler(Exception)
def handle_exception(e):
    # Optionally log the error here
    error_code = "An unexpected error occurred. Please contact support."
    return render_template("error.html", error_code=error_code, back_url=url_for('index')), 500

###########################################################################

if __name__ == '__main__':
    app.run(debug=False)
