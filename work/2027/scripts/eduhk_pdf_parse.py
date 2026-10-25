"""Parse EdUHK 2026 admission-scores PDF -> per-programme 2026 intake scores + 2027 weightings.

PDF: work/2027/raw/eduhk_scores_2026.pdf
  cols: code | title | 2026-weights | LQ | Median | mean | 2027-weights | remarks
Output: work/2027/raw/eduhk_pdf_parsed.json
"""
import json
import os
import re

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PDF = os.path.join(ROOT, "work", "2027", "raw", "eduhk_scores_2026.pdf")
OUT = os.path.join(ROOT, "work", "2027", "raw", "eduhk_pdf_parsed.json")

CODE_RE = re.compile(r"^JS\d{4}$")
W_RE = re.compile(r"^(?P<subj>.+?)\s*\(x\s*(?P<w>\d+(?:\.\d+)?)\)\s*\*?$")


def header_map(table):
    """Locate the columns we care about from the multi-row header."""
    hdr = {}
    for r in table[:8]:
        for i, cell in enumerate(r):
            if not cell:
                continue
            c = cell.replace("\n", " ").strip().lower()
            if "2027 entry" in c:
                hdr["w2027"] = i
            elif "admission score calculation" in c and "w2026" not in hdr:
                hdr["w2026"] = i
            elif c.startswith("median"):
                hdr["median"] = i
            elif c.startswith("lower"):
                hdr["lq"] = i
            elif "mean" in c and "mean" not in hdr:
                hdr["mean_specific"] = i
            elif c.startswith("programme title"):
                hdr["title"] = i
    return hdr


def main():
    records = {}
    with pdfplumber.open(PDF) as pdf:
        for pg in pdf.pages:
            tables = pg.extract_tables()
            if not tables:
                continue
            # main data table = the one with the most columns
            table = max(tables, key=lambda t: max((len(r) for r in t), default=0))
            if max(len(r) for r in table) < 10:
                continue
            hdr = header_map(table)
            if "w2027" not in hdr or "lq" not in hdr:
                print("header miss on page", hdr)
                continue
            ncol = max(len(r) for r in table)
            for row in table:
                row = list(row) + [None] * (ncol - len(row))
                code = (row[0] or "").strip()
                if not CODE_RE.match(code):
                    continue
                def cell(key):
                    i = hdr.get(key)
                    if i is None or i >= len(row):
                        return None
                    return (row[i] or "").replace("\n", " ").strip()

                def num(v):
                    if v is None:
                        return None
                    v = v.strip()
                    if re.fullmatch(r"\d+(\.\d+)?", v):
                        return float(v)
                    return None

                # LQ / median columns shift by one on some pages (merged header
                # cells), so read the first two pure numbers after the title and
                # before the 2027-weighting column.
                nums = [
                    num(row[i])
                    for i in range(3, hdr["w2027"])
                    if num(row[i]) is not None
                ]
                mean_txt = None
                for i in range(hdr["w2027"] - 1, 3, -1):
                    v = (row[i] or "").strip()
                    if v and v != "-" and num(v) is None:
                        mean_txt = v.replace("\n", " ")
                        break
                rec = {
                    "jupas_code": code,
                    "title": cell("title"),
                    "weights_2026_raw": (row[hdr["w2026"]] or "").strip() if hdr.get("w2026") is not None else None,
                    "weights_2027_raw": (row[hdr["w2027"]] or "").strip(),
                    "lq": nums[0] if len(nums) > 0 else None,
                    "median": nums[1] if len(nums) > 1 else None,
                    "mean_specific": mean_txt,
                    "remarks": cell("_remarks") or (row[-1] or "").strip(),
                }
                records[code] = rec
    json.dump(records, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("programmes:", len(records))
    for c, r in records.items():
        print(c, r["lq"], r["median"], r["mean_specific"], "|", (r["weights_2027_raw"] or "").replace("\n", "; ")[:90])


if __name__ == "__main__":
    main()
