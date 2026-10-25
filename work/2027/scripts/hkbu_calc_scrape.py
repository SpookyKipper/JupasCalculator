import json, re
from playwright.sync_api import sync_playwright

OUT = "work/2027/raw/hkbu_calc.json"
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    xhr = []
    pg.on("response", lambda r: xhr.append({"url": r.url, "status": r.status}) if "scorecalculator" in r.url else None)
    pg.goto("https://admissions.hkbu.edu.hk/ug/jupas_weighting", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(2500)
    prog = pg.query_selector("select[name=programme]")
    year = pg.query_selector("select[name=year]")
    opts = [(o.get_attribute("value"), o.inner_text().strip()) for o in prog.query_selector_all("option")]
    opts = [(v, t) for v, t in opts if v]
    print(len(opts), "programmes")
    results = {}
    for val, label in opts:
        prog.select_option(val)
        try:
            year.select_option("2026")
        except Exception as e:
            print("year select fail", e)
        pg.wait_for_timeout(1800)
        page_text = pg.inner_text("body")
        # section: Admission Scores .. Score Calculation
        m = re.search(r"Admission Scores(.*?)(Score Calculation 2027|$)", page_text, re.S)
        sec = m.group(1) if m else ""
        f = re.search(r"Score Calculation:?\s*(.*?)\n", page_text)
        results[val] = {"label": label, "scores_block": re.sub(r"\n{2,}", "\n", sec).strip()[:1200],
                        "formula": f.group(1).strip() if f else ""}
        print("==", val, label[:50])
        print(results[val]["scores_block"][:300].replace("\n", " / "))
    json.dump(results, open(OUT, "w"), indent=1, ensure_ascii=False)
    print("xhr", set(x["url"].split("?")[0] for x in xhr))
    b.close()
