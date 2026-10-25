"""Parse PolyU 2026 JUPAS admission figures PDF (table-cell based).

The PDF bundles three sections: 2026 (pp.1-5), 2025 (pp.6-10), 2024 (pp.11-13).
Only the 2026 section is used.

Output: work/2027/raw/polyu_figures_2026.json
  {code: {"average": float|None, "median": float|None, "lq": float|None, "mechanism": str}}
"""
import json, re
import pdfplumber

PDF = "work/2027/raw/polyu_admission_figures.pdf"
NUM = re.compile(r"^\d+(\.\d+)?$")


def parse_rows(rows, recs):
    cur = None
    for r in rows:
        cells = [(c or "").replace("\n", " ").strip() for c in r]
        joined = " | ".join(cells)
        codes = re.findall(r"JS\d{4}", joined)
        if codes:
            cur = codes[0]
            rec = recs.setdefault(cur, {"average": None, "median": None, "lq": None, "mechanism": ""})
            # average = first numeric cell after the code cell
            ci = next(i for i, c in enumerate(cells) if c == cur)
            for c in cells[ci + 1:]:
                if NUM.match(c):
                    rec["average"] = float(c)
                    break
        if cur is None:
            continue
        rec = recs[cur]
        for i, c in enumerate(cells):
            low = c.lower()
            if low == "median":
                for v in cells[i + 1:]:
                    if NUM.match(v):
                        rec["median"] = rec["median"] if rec["median"] is not None else float(v)
                        break
            elif low.startswith("lower quartile"):
                for v in cells[i + 1:]:
                    if NUM.match(v):
                        if rec["lq"] is None:
                            rec["lq"] = float(v)
                        break
        for c in cells:
            if re.search(r"Best \d Subjects|Core \+|Any Best|bonus score", c or "") and len(c) > 8:
                rec["mechanism"] = re.sub(r"\s+", " ", c).strip()
                break


recs = {}
with pdfplumber.open(PDF) as pdf:
    for pg in pdf.pages:
        head = (pg.extract_text() or "")[:90]
        if "2025 JUPAS (HKDSE) Admissions Figures" in head:
            break
        for t in pg.find_tables():
            rows = t.extract()
            if rows and len(rows) > 3:
                parse_rows(rows, recs)

json.dump(recs, open("work/2027/raw/polyu_figures_2026.json", "w"), indent=1, ensure_ascii=False)
print(len(recs), "codes")
for k, v in recs.items():
    print(k, v["average"], v["median"], v["lq"], "|", v["mechanism"][:64])
