import requests
import json
from bs4 import BeautifulSoup
def reset_passwd_konosys(matricule):
    url = "https://universitic.ueuromed.org/InitPassword/Home/Init"
    params = {"Matricule": matricule}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        Dict = json.loads(response.text)
        response_text=Dict["Message"]
        soup = BeautifulSoup(response_text, 'html.parser')
        message_without_html = soup.get_text()
        return message_without_html.strip()
    else:
        print(f"Request failed with status code {response.status_code}")
   # print(reset_passwd_konosys(2301087))
   