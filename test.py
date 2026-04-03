import urllib.request
try:
    urllib.request.urlopen("http://127.0.0.1:8000/analytics/category/1/")       
except Exception as e:
    with open("error.html", "w", encoding="utf-8") as f:
        f.write(e.read().decode("utf-8"))
