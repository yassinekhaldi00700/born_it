import subprocess
import os

def reset_passwd_AD(username):
    """
    Reset Active Directory password using PowerShell
    """
    if not username or username.strip() == "":
        return "❌ Nom d'utilisateur manquant"
    
    # Generate a simple password: test + 6 random digits
    import random
    random_digits = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    new_password = f"test{random_digits}"
    
    # Path to PowerShell script
    script_path = os.path.join(os.path.dirname(__file__), "Reset-ADPassword.ps1")
    
    if not os.path.exists(script_path):
        return f"❌ Script PowerShell introuvable: {script_path}"
    
    try:
        # Execute PowerShell script
        cmd = [
            "powershell.exe",
            "-ExecutionPolicy", "Bypass",
            "-File", script_path,
            "-login", username,
            "-motdepasse", new_password
        ]
        
        print(f"DEBUG: Executing AD reset for user: {username}")
        print(f"DEBUG: Generated password format: test######")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8',
            errors='replace'
        )
        
        print(f"DEBUG: Return code: {result.returncode}")
        print(f"DEBUG: PowerShell stdout: '{result.stdout.strip()}'")
        
        # Parse the output
        output = result.stdout.strip()
        
        # Check for success
        if result.returncode == 0 and "SUCCESS:" in output:
            return f"✅ Mot de passe AD réinitialisé avec succès pour {username}\n🔑 Nouveau mot de passe: {new_password}"
        
        # Handle various error cases...
        if "User" in output and "not found" in output:
            return f"❌ Utilisateur '{username}' introuvable dans Active Directory"
        
        if "Connection failed" in output:
            return "❌ Impossible de se connecter au contrôleur de domaine"
        
        if "ERROR:" in output:
            error_lines = [line for line in output.split('\n') if 'ERROR:' in line]
            if error_lines:
                error_msg = error_lines[-1].replace('ERROR:', '').strip()
                return f"❌ Erreur AD: {error_msg}"
        
        if result.returncode != 0:
            return f"❌ Échec de la réinitialisation AD (code: {result.returncode})"
        
        return f"⚠️ Statut incertain pour la réinitialisation AD de {username}"
        
    except subprocess.TimeoutExpired:
        return "❌ Timeout lors de la réinitialisation AD (60s)"
    except Exception as e:
        print(f"ERROR in reset_passwd_AD: {e}")
        return f"❌ Erreur système AD: {str(e)[:100]}..."