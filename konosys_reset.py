import requests

from config import env


KONOSYS_API_BASE_DEFAULT = "https://universitic.ueuromed.org/API_KONOSYS_CompteEtudiant"


def get_mail_professionnel(matricule):
    """Return the student's professional e-mail from the KONOSYS API (ERP_User.MailGEM), or None.

    Read-only lookup: GET /api/etudiants/{matricule}/mail-professionnel (header X-API-Key).
    Never raises: any failure (400/401/404/409/503, network error) returns None so the
    caller can fall back to another source.
    """
    matricule = str(matricule or "").strip()
    if not matricule:
        return None

    base = env("KONOSYS_API_BASE", KONOSYS_API_BASE_DEFAULT).rstrip("/")
    url = f"{base}/api/etudiants/{matricule}/mail-professionnel"

    try:
        response = requests.get(url, headers={"X-API-Key": env("KONOSYS_API_KEY")}, timeout=10)
    except requests.RequestException as e:
        print(f"KONOSYS mail API unreachable: {e}")
        return None

    if response.status_code != 200:
        print(f"KONOSYS mail API matricule={matricule} -> HTTP {response.status_code}: {response.text[:200]}")
        return None

    try:
        mail = (response.json().get("mailProfessionnel") or "").strip()
    except ValueError:
        print(f"KONOSYS mail API returned invalid JSON: {response.text[:200]}")
        return None
    return mail or None


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
