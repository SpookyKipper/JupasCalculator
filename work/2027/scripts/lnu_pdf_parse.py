"""Parse Lingnan 2026 JUPAS Admission Scores PDF (2 pages, two column layout).

PDF: work/2027/raw/lnu_scores_2026.pdf
Output: work/2027/raw/lnu_pdf_parsed.json

Layout notes
------------
* The page is two independent columns (left x<421, right x>=421).
* Each programme block holds a weighted score for the Median and for the
  Lower Quartile, plus the per-subject median/LQ scores
  (Chinese, English, Math, Elective 1, Elective 2).
* The JS code sits roughly in the middle of its block: the Median row is
  usually just above it, the Lower Quartile row below it. Labels can be
  rendered letter by letter ("L o w e r" / "Q u a r t i l e") on their own
  rows, so labels are matched on whitespace-stripped text and value rows are
  attached to the nearest label row, then to the nearest code.
"""
import json
import os
import re
from collections import defaultdict

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PDF = os.path.join(ROOT, "work", "2027", "raw", "lnu_scores_2026.pdf")
OUT = os.path.join(ROOT, "work", "2027", "raw", "lnu_pdf_parsed.json")

CODE_RE = re.compile(r"^JS7\d{3}$")
NUM_RE = re.compile(r"^\d+([.,]\d+)?$")

# x windows: (score, chi, eng, math, e1, e2)
BANDS = {
    "left": [(208, 246), (250, 282), (288, 318), (325, 355), (358, 390), (392, 420)],
    "right": [(598, 642), (645, 678), (682, 712), (718, 748), (752, 783), (785, 815)],
}
NAMES = ["score", "chi", "eng", "math", "e1", "e2"]


def rows_of(words, tol=3):
    buckets = defaultdict(list)
    for w in words:
        buckets[round(w["top"] / tol) * tol].append(w)
    return [(y, sorted(ws, key=lambda w: w["x0"])) for y, ws in sorted(buckets.items())]


def label_kind(text):
    t = re.sub(r"\s+", "", text).lower()
    if "median" in t:
        return "median"
    if "lower" in t or "quartile" in t:
        return "lq"
    return None


def main():
    progs = {}
    skipped = []
    with pdfplumber.open(PDF) as pdf:
        for pno, pg in enumerate(pdf.pages, 1):
            words = pg.extract_words()
            for side in ("left", "right"):
                sub = [w for w in words if (w["x0"] < 421) == (side == "left")]
                rows = rows_of(sub)
                codes = []
                vals_rows = []
                label_rows = []
                for y, ws in rows:
                    text = " ".join(w["text"] for w in ws)
                    code = next((w["text"] for w in ws if CODE_RE.match(w["text"])), None)
                    if code:
                        codes.append((y, code))
                    got = {}
                    for name, (lo, hi) in zip(NAMES, BANDS[side]):
                        for w in ws:
                            if lo <= w["x0"] <= hi and NUM_RE.match(w["text"]):
                                got[name] = float(w["text"].replace(",", "."))
                                break
                    if "score" in got:
                        vals_rows.append((y, text, got))
                    elif label_kind(text):
                        label_rows.append((y, label_kind(text)))

                for y, text, got in vals_rows:
                    kind = label_kind(text)
                    if kind is None and label_rows:
                        ly, lk = min(label_rows, key=lambda lr: abs(lr[0] - y))
                        kind = lk if abs(ly - y) <= 14 else None
                    if kind is None:
                        skipped.append((pno, side, y, text[:60]))
                        continue
                    cy, code = min(codes, key=lambda c: abs(c[0] - y))
                    if abs(cy - y) > 30:
                        skipped.append((pno, side, y, f"no code: {text[:50]}"))
                        continue
                    rec = progs.setdefault(code, {})
                    prev = rec.get(kind)
                    if prev and abs(prev["y"] - y) <= abs(prev["y"] - cy):
                        continue
                    rec[kind] = {
                        "y": y,
                        "score": got["score"],
                        "grades": {n: got[n] for n in ("chi", "eng", "math", "e1", "e2") if n in got},
                    }
    out = {}
    for code, rec in sorted(progs.items()):
        out[code] = {
            "jupas_code": code,
            "median": rec.get("median", {}).get("score"),
            "lq": rec.get("lq", {}).get("score"),
            "grades_median": rec.get("median", {}).get("grades"),
            "grades_lq": rec.get("lq", {}).get("grades"),
        }
    json.dump(out, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("programmes:", len(out))
    print("missing median/lq:", [c for c, r in out.items() if r["median"] is None or r["lq"] is None])
    print("skipped rows:", skipped)
    for c, r in out.items():
        print(c, r["median"], r["lq"], r["grades_median"])


if __name__ == "__main__":
    main()
