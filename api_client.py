
import requests

name = input("Enter your first name: ")

url = "https://armadalawrence-activity4.onrender.com/hello"
params = {"name": name}

try:
    response = requests.get(url, params=params, timeout=60)

    print("Status Code:", response.status_code)

    if response.status_code == 200:
        data = response.json()
        print(data["message"])
    else:
        print("Request failed.")
        print("Response:", response.text)

except requests.exceptions.RequestException as e:
    print("Connection error:", e)
