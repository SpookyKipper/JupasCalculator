import json
from playwright.sync_api import sync_playwright

url = "https://admissions.hkbu.edu.hk/ug/jupas_weighting"
captured = []
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    def on_resp(r):
        ct = r.headers.get("content-type", "")
        if "json" in ct or ".json" in r.url:
            try:
                body = r.text()
            except Exception:
                body = ""
            captured.append({"url": r.url, "status": r.status, "len": len(body), "body": body[:3000]})
    pg.on("response", on_resp)
    pg.goto(url, wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(3000)
    print("responses", len(captured))
    for c in captured:
        print(c["status"], c["len"], c["url"][:160])
    json.dump(captured, open("work/2027/raw/hkbu_xhr.json", "w"), indent=1)
    b.close()
