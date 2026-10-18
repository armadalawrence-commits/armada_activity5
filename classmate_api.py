
import requests

url = "https://CLASSMATE-URL.onrender.com/YOUR-ENDPOINT"

try:
    response = requests.get(url, timeout=60)

    if response.status_code == 200:
        data = response.json()
        print("API request successful!")
        print(data)
    else:
        print("Request failed.")
        print("Status Code:", response.status_code)

except requests.exceptions.RequestException as error:
    print("Connection error:", error)
