import json, sys
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "https://www.polyu.edu.hk/study/ug/admissions/jupas"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto(url, wait_until="networkidle", timeout=90000)
    raw = pg.evaluate("() => typeof drupalSettings !== 'undefined' && drupalSettings.jupas_calculator ? JSON.stringify(drupalSettings.jupas_calculator) : null")
    print("len", len(raw) if raw else None)
    if raw:
        open("work/2027/raw/polyu_drupal_2027.json","w",encoding="utf-8").write(raw)
        d = json.loads(raw)
        print("top keys:", list(d)[:20])
        for k in list(d)[:5]:
            v = d[k]
            print(k, type(v), (list(v)[:5] if isinstance(v, dict) else (len(v) if isinstance(v,list) else v)))
    b.close()
