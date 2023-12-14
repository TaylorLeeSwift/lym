import requests

url = 'http://127.0.0.1:8081/data?city_name="New Rome"'
res = requests.delete(url)

print(res.text)