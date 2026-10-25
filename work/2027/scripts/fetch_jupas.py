"""
Fetch JUPAS 2027 programme pages (HKMU + SSSDP) and parse entrance requirements,
weighted-subject hints and programme names.

Output: work/2027/raw/jupas_pages/<CODE>.html  (cache)
        work/2027/raw/jupas_parsed.json        (parsed)

Usage: .venv/bin/python work/2027/scripts/fetch_jupas.py
"""
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # work/2027
RAW = os.path.join(ROOT, "raw")
CACHE = os.path.join(RAW, "jupas_pages")
os.makedirs(CACHE, exist_ok=True)

HKMU_CODES = ['JS9009', 'JS9010', 'JS9011', 'JS9013', 'JS9016', 'JS9019', 'JS9210',
              'JS9220', 'JS9230', 'JS9240', 'JS9262', 'JS9266', 'JS9276', 'JS9280',
              'JS9291', 'JS9294', 'JS9520', 'JS9530', 'JS9540', 'JS9550', 'JS9560',
              'JS9580', 'JS9719', 'JS9720', 'JS9731', 'JS9732', 'JS9733', 'JS9776']

SSSDP_CODES = ['JSSA01', 'JSSA02', 'JSSA03', 'JSSA04', 'JSSA05', 'JSSA06', 'JSSC02',
               'JSSH01', 'JSSH02', 'JSSH03', 'JSSH04', 'JSSH05', 'JSSH06',
               'JSST01', 'JSST02', 'JSST03', 'JSST04', 'JSST05', 'JSST06', 'JSST07', 'JSST08',
               'JSSU12', 'JSSU14', 'JSSU15', 'JSSU18', 'JSSU40', 'JSSU50', 'JSSU55',
               'JSSU61', 'JSSU66', 'JSSU67', 'JSSU69', 'JSSU70', 'JSSU72', 'JSSU75',
               'JSSU77', 'JSSU78', 'JSSU79', 'JSSU90', 'JSSU93', 'JSSU95', 'JSSU96',
               'JSSU97',
               'JSSV01', 'JSSV02', 'JSSV03', 'JSSV04', 'JSSV05', 'JSSV07', 'JSSV08',
               'JSSV09', 'JSSV10', 'JSSV13', 'JSSV14',
               'JSSW01', 'JSSW02', 'JSSY01', 'JSSY02', 'JSSY03']

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def fetch(code, sector):
    path = os.path.join(CACHE, f"{code}.html")
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        return code, open(path, encoding="utf-8", errors="ignore").read()
    url = f"https://www.jupas.edu.hk/en/programme/{sector}/{code}/"
    for attempt in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=30)
            if r.status_code == 200 and len(r.text) > 5000:
                open(path, "w", encoding="utf-8").write(r.text)
                return code, r.text
        except Exception as e:
            print("ERR", code, e)
        time.sleep(1 + attempt)
    return code, None


def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()


def parse_rows(table):
    out = []
    for tr in table.select("tr"):
        cells = [clean(td.get_text(" ")) for td in tr.select("td")]
        if len(cells) >= 2 and cells[0]:
            out.append((cells[0], cells[1]))
    return out


def parse_page(code, html, sector):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text() if soup.title else ""
    name = clean(title.split(" - ")[0]) if title else ""

    # operator from name, e.g. "Offered by HKMU: Bachelor of ..."
    operator = None
    m = re.match(r"Offered by ([^:]+):\s*(.+)", name)
    if m:
        operator = m.group(1).strip()
        name = m.group(2).strip()

    containers = soup.select("div.dsereg_tables_container")
    core, elec, notes = [], [], []

    def absorb(container):
        for t in container.select("table.dsereg_table-core"):
            core.extend(parse_rows(t))
        for t in container.select("table.dsereg_table-elective"):
            elec.extend(parse_rows(t))

    if containers:
        # container 0 = programme-specific tab, container 1 = general tab
        txt0 = clean(containers[0].get_text(" "))
        if "Same as General Entrance Requirements" in txt0 and len(containers) > 1:
            absorb(containers[1])
        else:
            absorb(containers[0])
        if not core and len(containers) > 1:
            absorb(containers[1])

    # remarks / programme-specific note blocks
    for div in soup.select("div.remarks.ckec, div.remarks-larger.ckec")[:3]:
        t = clean(div.get_text(" "))
        if t and len(t) < 2000:
            notes.append(t)

    # weighted subjects: "will carry a greater weight ... " followed by "- Subject" lines
    weighted = []
    for node in soup.find_all(string=re.compile(r"carry a greater weight")):
        box = node.parent
        for _ in range(3):
            if box is None or box.name in ("p", "div"):
                break
            box = box.parent
        text = box.get_text("\n") if box else ""
        lines = [clean(x) for x in text.split("\n")]
        grab = False
        for ln in lines:
            if "greater weight" in ln:
                grab = True
                continue
            if grab:
                if ln.startswith("-"):
                    s = clean(ln.lstrip("-").strip())
                    if s and len(s) < 70:
                        weighted.append(s)
                elif ln and weighted:
                    break
        if weighted:
            break

    return {
        "code": code,
        "sector": sector,
        "name": name,
        "operator": operator,
        "core": core,
        "electives": elec,
        "weighted_subjects": weighted,
        "notes": notes,
    }


def main():
    jobs = [(c, "hkmu") for c in HKMU_CODES] + [(c, "sssdp") for c in SSSDP_CODES]
    pages = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        for code, html in ex.map(lambda j: fetch(*j), jobs):
            if html:
                pages[code] = html
            else:
                print("MISSING", code)

    parsed = {}
    for code, sector in jobs:
        if code in pages:
            parsed[code] = parse_page(code, pages[code], sector)

    with open(os.path.join(RAW, "jupas_parsed.json"), "w", encoding="utf-8") as f:
        json.dump(parsed, f, ensure_ascii=False, indent=1)

    print(f"parsed {len(parsed)} / {len(jobs)}")
    for code in ["JS9009", "JSSU40", "JSSA03", "JSSV01"]:
        p = parsed.get(code)
        if p:
            print("\n==", code, p["name"], "| operator:", p["operator"])
            print(" core:", p["core"])
            print(" elec:", p["electives"])
            print(" weighted:", p["weighted_subjects"])


if __name__ == "__main__":
    main()
