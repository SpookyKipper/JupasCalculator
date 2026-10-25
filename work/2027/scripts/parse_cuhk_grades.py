"""Parse CUHK 'Admission Grades of JUPAS Applicants (2026 Entry)' PDF into structured records.

The PDF lays out each programme as three percentile rows (UQ / M / LQ); the JUPAS code
column may sit on the UQ or M row depending on vertical centring, so rows are grouped
into blocks that start at each 'UQ' row.

Output: work/2027/scripts/cuhk_grades_2026.json
"""
import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "Reference(2027)/CUHK/Admission-Grades-2026.pdf"
OUT = Path(__file__).resolve().parent / "cuhk_grades_2026.json"

CODE_RE = re.compile(r"^JS\d{4}$")


def clean(rows):
    out = []
    for r in rows:
        out.append([(c or "").replace("\n", " ").strip() for c in r])
    return out


def main() -> None:
    pdf = pdfplumber.open(PDF)
    rows = []
    for page in pdf.pages:
        rows.extend(clean(page.extract_table() or []))

    blocks = []
    cur = None
    for r in rows:
        if len(r) < 16:
            continue
        pct = r[2]
        if pct == "UQ":
            cur = {"rows": {}}
            blocks.append(cur)
        if cur is not None and pct in ("UQ", "M", "LQ"):
            cur["rows"][pct] = r
            continue
        # stray text rows (faculty headers / notes) are ignored

    out = []
    for b in blocks:
        data = list(b["rows"].values())
        code = next((x[0] for x in data if CODE_RE.match(x[0])), None)
        if not code:
            print("SKIP block without code:", [x[1] for x in data])
            continue
        names = [x[1] for x in data if x[1]]
        principle = " ".join(x[14] for x in data if x[14]).strip()
        weighting = " ".join(x[15] for x in data if x[15]).strip()
        rec = {
            "code": code,
            "name": " ".join(names),
            "principle": principle,
            "weighting_text": weighting,
            "totals": {},
            "grades": {},
        }
        for pct, row in b["rows"].items():
            try:
                rec["totals"][pct] = float(row[13])
            except ValueError:
                rec["totals"][pct] = None
            rec["grades"][pct] = {
                "chi": row[3],
                "eng": row[4],
                "math": row[5],
                "csd": row[6],
                "ls": row[7],
                "m1m2": row[8],
                "electives": [x for x in row[9:13] if x],
            }
        out.append(rec)

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(f"{len(out)} programmes -> {OUT}")
    for rec in out:
        missing = [k for k, v in rec["totals"].items() if v is None]
        if missing or len(rec["totals"]) != 3:
            print("CHECK", rec["code"], rec["name"], rec["totals"])


if __name__ == "__main__":
    main()
