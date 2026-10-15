import requests

from config import env


def reset_passwd_konosys(matricule, email=None):
    """Ask the KONOSYS API to send the student's login details to their academic e-mail.

    Returns the message shown on the kiosk (starts with ❌ on failure).
    """
    if not str(matricule or "").strip():
        return "❌ Matricule introuvable. Passez à nouveau votre carte."

    url = env("KONOSYS_API_URL", "https://universitic.ueuromed.org/API_KONOSYS_CompteEtudiant/api/etudiants/envoyer-identifiants")
    headers = {"Content-Type": "application/json", "X-API-Key": env("KONOSYS_API_KEY")}

    try:
        response = requests.post(url, json={"matricule": str(matricule)}, headers=headers, timeout=30)
    except requests.RequestException as e:
        print(f"KONOSYS API unreachable: {e}")
        return "❌ Le service Konosys est injoignable. Veuillez réessayer dans quelques instants."

    print(f"KONOSYS API matricule={matricule} -> HTTP {response.status_code}: {response.text[:300]}")

    if response.status_code == 202:
        where = f" :\n{email}" if email else "."
        return f"✅ Vos identifiants Konosys ont été envoyés à votre adresse e-mail académique{where}"
    if response.status_code == 404:
        return "❌ Votre matricule est introuvable dans Konosys. Rendez-vous à la DSI."
    if response.status_code in (401, 403):
        return "❌ Le service Konosys a refusé la demande. Contactez la DSI."
    return "❌ L'envoi des identifiants Konosys a échoué. Veuillez réessayer plus tard."
