import requests
import secrets

from config import env

# Config Azure
client_id = env("AZURE_CLIENT_ID")
tenant_id = env("AZURE_TENANT_ID")
client_secret = env("AZURE_CLIENT_SECRET")


def generate_password():
    # Format: uemf@ + 8 random digits (e.g. uemf@45488259)
    random_numbers = ''.join(secrets.choice("0123456789") for _ in range(8))
    return f"uemf@{random_numbers}"

def get_token():
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "https://graph.microsoft.com/.default"
    }
    response = requests.post(url, data=data, timeout=15)
    if response.status_code != 200:
        print("Token error:", response.status_code)
    return response.json().get("access_token")

def reset_passwd_outlook(user_email):
    token = get_token()
    if not token:
        return "❌ Auth error"

    new_password = generate_password()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}"
    payload = {
        "passwordProfile": {
            "forceChangePasswordNextSignIn": True,
            "password": new_password
        }
    }

    r = requests.patch(url, headers=headers, json=payload, timeout=15)
    if r.status_code == 204:
        print("✅ Reset done for", user_email)
        return new_password
    else:
        print("❌ Error:", r.status_code, r.text)
        return None
