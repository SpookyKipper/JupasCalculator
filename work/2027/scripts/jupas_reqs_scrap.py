"""Scrape official JUPAS 2027 programme pages for EdUHK + LingnanU.

Extracts, per programme: name_en, name_zh, quota, study level, interview text,
programme entrance requirements (core + elective tables) and the general
entrance requirements tables. Writes work/2027/raw/jupas_reqs_2027.json.
"""
import json
import os
import re
import time

import requests
from bs4 import BeautifulSoup

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW = os.path.join(ROOT, "work", "2027", "raw")
OUT = os.path.join(RAW, "jupas_reqs_2027.json")

SCHOOLS = {"EdUHK": "eduhk", "LingnanU": "lingnanu"}


def get_codes(institution):
    import csv
    codes = []
    with open(os.path.join(ROOT, "data/raw/2027 JUPAS Program Overview.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["Institution / Scheme"].strip() == institution:
                codes.append(row["JUPAS Catalogue No."].strip())
    return codes


def table_rows(tbl):
    out = []
    for tr in tbl.find_all("tr"):
        cells = [td.get_text(" ", strip=True) for td in tr.find_all(["td", "th"])]
        if cells:
            out.append(cells)
    return out


def parse_requirements(soup):
    """Return dict with programme-level and general-level requirement tables."""
    block = soup.find("div", class_="dsereg_tables_container")
    # The Requirements section holds tabs: programme ER then general ER.
    core = soup.select("table.dsereg_table-core")
    elec = soup.select("table.dsereg_table-elective")
    tabs = soup.select("div.js-tab-content")
    prog_text = tabs[0].get_text(" ", strip=True) if tabs else ""
    return {
        "programme_tab_text": prog_text[:400],
        "core_tables": [table_rows(t) for t in core],
        "elective_tables": [table_rows(t) for t in elec],
        "remarks_text": " ".join(
            d.get_text(" ", strip=True) for d in soup.select("div.remarks.ckec")
        )[:3000],
    }


def main():
    s = requests.Session()
    s.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"
    data = {}
    if os.path.exists(OUT):
        data = json.load(open(OUT))
    for inst, key in SCHOOLS.items():
        for code in get_codes(inst):
            if code in data:
                continue
            url = f"https://www.jupas.edu.hk/en/programme/{key}/{code}/"
            for attempt in range(3):
                try:
                    r = s.get(url, timeout=45)
                    r.raise_for_status()
                    break
                except Exception as e:  # noqa: BLE001
                    print("retry", code, e)
                    time.sleep(3)
            else:
                print("FAIL", code)
                continue
            soup = BeautifulSoup(r.content, "html.parser")
            name_en = soup.select_one(".program_title .before_label")
            name_zh = soup.select_one(".program_title_cn")
            info = {}
            for blk in soup.select(".programInfo_block"):
                label = blk.select_one(".programInfo_block-name")
                if label:
                    info[label.get_text(strip=True)] = blk.get_text(" ", strip=True).replace(
                        label.get_text(strip=True), "", 1
                    ).strip()
            rec = {
                "jupas_code": code,
                "institution": inst,
                "url": url,
                "name_en": name_en.get_text(" ", strip=True) if name_en else "",
                "name_zh": name_zh.get_text(" ", strip=True) if name_zh else "",
                "info": info,
                "requirements": parse_requirements(soup),
            }
            data[code] = rec
            print(code, rec["name_en"][:60])
            time.sleep(0.4)
    json.dump(data, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("total", len(data))


if __name__ == "__main__":
    main()
