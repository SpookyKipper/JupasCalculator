"""Parse HKUST '2026 JUPAS Admissions Scores' (one landscape page, two side-by-side tables).

Columns: JUPAS code | programme | HIGHEST ATTAINABLE | MEDIAN | LOWER QUARTILE |
         preferred subjects | average level of preferred subjects.
HKUST publishes no upper quartile, so uq is left null.

Output: work/2027/scripts/hkust_scores_2026.json
"""
import json
import re
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parents[3]
PDF = ROOT / "Reference(2027)/HKUST/HKUST-JUPAS-Admission-Scores-2026.pdf"
OUT = Path(__file__).resolve().parent / "hkust_scores_2026.json"

# score-column x centres for the left and right sub-tables
LEFT = (251, 308, 365)
RIGHT = (847, 904, 961)


def pick(ws, cx, y, tol=25):
    cand = [w for w in ws if abs(w["x0"] - cx) < tol and abs(w["top"] - y) < 6]
    return cand[0]["text"] if cand else None


def main() -> None:
    pdf = pdfplumber.open(PDF)
    ws = pdf.pages[0].extract_words()
    codes = [w for w in ws if re.fullmatch(r"JS\d{4}", w["text"])]
    rows = []
    for c in codes:
        left = c["x0"] < 600
        cols = LEFT if left else RIGHT
        rec = {
            "code": c["text"],
            "name": " ".join(sorted(
                [w["text"] for w in ws
                 if abs(w["top"] - c["top"]) < 6 and c["x0"] + 10 < w["x0"] < cols[0] - 10],
                key=lambda t: t)),
            "highest": pick(ws, cols[0], c["top"]),
            "median": pick(ws, cols[1], c["top"]),
            "lq": pick(ws, cols[2], c["top"]),
        }
        for k in ("highest", "median", "lq"):
            try:
                rec[k] = float(rec[k])
            except (TypeError, ValueError):
                rec[k] = None
        rows.append(rec)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, indent=1))
    print(len(rows), "->", OUT)
    for r in rows:
        print(r["code"], r["name"][:48], r["highest"], r["median"], r["lq"])


if __name__ == "__main__":
    main()
