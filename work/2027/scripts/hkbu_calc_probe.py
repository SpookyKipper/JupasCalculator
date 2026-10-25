from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page()
    pg.goto("https://admissions.hkbu.edu.hk/ug/jupas_weighting", wait_until="networkidle", timeout=90000)
    pg.wait_for_timeout(3000)
    sels = pg.query_selector_all("select")
    print("selects", len(sels))
    for i, s in enumerate(sels):
        opts = s.query_selector_all("option")
        print(i, s.get_attribute("id"), s.get_attribute("name"), "opts", len(opts), [o.inner_text()[:40] for o in opts[:5]])
    # find elements mentioning Mean
    for el in pg.query_selector_all("[class*=score], [id*=score]"):
        t = (el.inner_text() or "").strip()
        if t and "Mean" in t:
            print("SCORE EL", el.get_attribute("id"), t[:300])
    b.close()
