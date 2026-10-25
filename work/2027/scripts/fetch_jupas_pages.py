"""Fetch JUPAS programme pages (2027 cycle) for CUHK and HKUST and extract the
'Programme Entrance Requirements' tables.

Output: work/2027/scripts/jupas_pages_<inst>.json
"""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings()

OUT = Path(__file__).resolve().parent
HEAD = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"}


def fetch(inst: str, code: str) -> dict:
    url = f"https://www.jupas.edu.hk/en/programme/{inst}/{code}/"
    r = None
    for attempt in range(4):
        try:
            r = requests.get(url, headers=HEAD, timeout=60, verify=False)
            if r.status_code == 200:
                break
        except requests.RequestException as exc:
            print("retry", code, attempt, type(exc).__name__)
        time.sleep(2 + attempt * 3)
    if r is None or r.status_code != 200:
        return {"code": code, "url": url, "status": getattr(r, "status_code", None)}
    s = BeautifulSoup(r.text, "html.parser")
    title = s.select_one(".program_title")
    rec = {
        "code": code,
        "url": url,
        "status": 200,
        "title": title.get_text(" ", strip=True) if title else "",
        "core": {},
        "elective": [],
        "remarks": "",
    }
    core = s.select_one("table.dsereg_table-core")
    if core:
        for tr in core.select("tr"):
            tds = tr.select("td")
            if len(tds) == 2:
                rec["core"][tds[0].get_text(" ", strip=True)] = tds[1].get_text(" ", strip=True)
    for tbl in s.select("table.dsereg_table-elective"):
        for tr in tbl.select("tr"):
            tds = tr.select("td")
            if len(tds) == 2:
                rec["elective"].append([tds[0].get_text(" ", strip=True),
                                        tds[1].get_text(" ", strip=True)])
    rem = s.select_one(".remarks.ckec")
    if rem:
        rec["remarks"] = rem.get_text(" ", strip=True)[:1200]
    return rec


def main() -> None:
    inst = sys.argv[1].lower()
    codes = sys.argv[2:]
    with ThreadPoolExecutor(max_workers=3) as ex:
        recs = list(ex.map(lambda c: fetch(inst, c), codes))
    path = OUT / f"jupas_pages_{inst}.json"
    path.write_text(json.dumps(recs, ensure_ascii=False, indent=1))
    print(len(recs), "->", path)


if __name__ == "__main__":
    main()
