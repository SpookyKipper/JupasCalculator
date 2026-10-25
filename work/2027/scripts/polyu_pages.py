"""Fetch PolyU 2027 JUPAS programme pages and extract mechanism / average / preferred subjects / requirements."""
import json, re, os, time
import requests
from bs4 import BeautifulSoup

codes = json.load(open("work/2027/raw/polyu_codes.json"))
os.makedirs("work/2027/raw/polyu_pages", exist_ok=True)
out = {}
S = requests.Session()
S.headers["User-Agent"] = "Mozilla/5.0"

for code in codes:
    path = f"work/2027/raw/polyu_pages/{code}.html"
    url = f"https://www.polyu.edu.hk/study/ug/jupas/2027/{code.lower()}"
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        html = open(path, encoding="utf-8").read()
    else:
        r = S.get(url, timeout=40, allow_redirects=True)
        html = r.text
        open(path, "w", encoding="utf-8").write(html)
        print(code, r.status_code, r.url, len(html))
        time.sleep(0.4)

json.dump(out, open("work/2027/raw/polyu_pages_index.json", "w"))
