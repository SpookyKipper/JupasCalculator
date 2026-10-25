"""Extract the HKUST 2027 JUPAS admissions requirements + score formulae PDF.

The PDF is a landscape two-level table; cells are vertically centred and several cells
span multiple visual lines, so pdfplumber's table detection merges rows. Instead we use
word coordinates: column x-ranges come from the header row, and each programme's row band
is the midpoint between neighbouring JUPAS-code y positions.

Output: work/2027/scripts/hkust_req_2027.json
"""
import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "Reference(2027)/HKUST/HKUST-Requirements-and-Score-Formulae-2027.pdf"
OUT = Path(__file__).resolve().parent / "hkust_req_2027.json"

COLS = [
    ("code", 100, 143),
    ("choice", 143, 265),
    ("options", 265, 468),
    ("eng", 468, 500),
    ("chin", 500, 527),
    ("math", 527, 553),
    ("csd", 553, 600),
    ("elect1", 600, 626),
    ("elect2", 626, 660),
    ("specific", 660, 745),
    ("formula", 745, 1016),
    ("max", 1016, 1085),
    ("bonus", 1085, 1195),
]


def extract_page(page):
    words = page.extract_words(keep_blank_chars=False)
    codes = sorted(
        [w for w in words if re.fullmatch(r"JS\d{4}", w["text"]) and 100 <= w["x0"] < 143],
        key=lambda w: w["top"],
    )
    rows = []
    for i, cw in enumerate(codes):
        top = 95 if i == 0 else (codes[i - 1]["top"] + cw["top"]) / 2
        bottom = (cw["top"] + codes[i + 1]["top"]) / 2 if i + 1 < len(codes) else 830
        band = [w for w in words if top <= (w["top"] + w["bottom"]) / 2 < bottom]
        rec = {"code": cw["text"]}
        for name, x0, x1 in COLS:
            cell = [w for w in band if x0 <= w["x0"] < x1]
            cell.sort(key=lambda w: (round(w["top"], 1), w["x0"]))
            rec[name] = " ".join(w["text"] for w in cell).strip()
        rows.append(rec)
    return rows


def main() -> None:
    pdf = pdfplumber.open(PDF)
    rows = []
    for page in pdf.pages:
        rows.extend(extract_page(page))
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(len(rows), "programme rows ->", OUT)
    for r in rows:
        print(r["code"], "|", r["eng"], r["chin"], r["math"], r["csd"],
              "|", r["elect1"], "|", r["elect2"], "|", r["specific"][:60],
              "|", r["max"])


if __name__ == "__main__":
    main()
