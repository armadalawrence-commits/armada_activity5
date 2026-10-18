import requests

url = "https://YOUR-URL.onrender.com/student"

response = requests.get(url, timeout=60)

print("Status Code:", response.status_code)
print("Response:")
print(response.text)
