"""Parse HKBU 'General Entrance Requirements and Programme Entrance Requirements (2027 Entry)' PDF."""
import json, re
import pdfplumber

PDF = "work/2027/raw/hkbu_GER_PER_2027.pdf"
CODE = re.compile(r"^JS\d{4}$")

ABBR = {
    "CHI": "Chinese Language",
    "ENG": "English Language",
    "MATH": "Mathematics (Compulsory Part)",
    "MAT1": "Mathematics Extended Part (Module 1)",
    "MAT2": "Mathematics Extended Part (Module 2)",
    "BIO": "Biology",
    "CHEM": "Chemistry",
    "PHY": "Physics",
    "ECON": "Economics",
    "GEOG": "Geography",
    "HIST": "History",
    "CHIS": "Chinese History",
    "CLIT": "Chinese Literature",
    "ELIT": "Literature in English",
    "EREL": "Ethics and Religious Studies",
    "I&CT": "Information and Communication Technology",
    "ICT": "Information and Communication Technology",
    "D&AT": "Design and Applied Technology",
    "BAFS": "Business, Accounting and Financial Studies",
    "HMSC": "Health Management and Social Care",
    "TLFC": "Technology and Living (Fashion, Clothing and Textiles)",
    "TLFS": "Technology and Living (Food Science and Technology)",
    "THS": "Tourism and Hospitality Studies",
    "VIS": "Visual Arts",
    "MUS": "Music",
    "PE": "Physical Education",
    "IS": "Integrated Science",
    "CS": "Combined Science",
    "VART": "Visual Arts",
    "MUSC": "Music",
}

WEIGHT_RE = re.compile(r"([A-Z&0-9]+(?:\s*,\s*[A-Z&0-9]+)*)\s*\(\s*x\s*([\d.]+)\s*\)")


def parse_weight_cell(cell):
    if not cell:
        return {}, ""
    txt = re.sub(r"\s+", " ", cell.replace("\n", " ")).strip()
    weights, unmapped = {}, []
    for m in WEIGHT_RE.finditer(txt):
        subs = [s.strip() for s in m.group(1).split(",")]
        w = float(m.group(2))
        for s in subs:
            canon = ABBR.get(s)
            if canon:
                weights[canon] = w
            else:
                unmapped.append(s)
    return weights, txt


progs = {}
with pdfplumber.open(PDF) as pdf:
    for pg in pdf.pages:
        for t in pg.extract_tables():
            header = None
            for row in t:
                cells = [(c or "").replace("\n", " ").strip() for c in row]
                if not any(cells):
                    continue
                if cells and cells[0] == "Prog. Code":
                    header = cells
                    continue
                # Some tables (School of Creative Arts) carry an extra empty cell
                # after the code because of a merged title cell.
                if len(cells) == 14 and cells[1] == "":
                    cells = [cells[0]] + cells[2:]
                if not CODE.match(cells[0] or ""):
                    continue
                code = cells[0]
                # columns: 0 code, 1 title, 2 approach, 3 CHI, 4 ENG, 5 CSD, 6 MATH, 7 1stX, 8 2ndX,
                #          9 M1/M2, 10 CatB, 11 CatC, 12 weights/remarks
                def g(i):
                    return cells[i] if len(cells) > i else ""
                weights, raw = parse_weight_cell(g(12))
                progs[code] = {
                    "title": g(1),
                    "approach": g(2),
                    "chi": g(3), "eng": g(4), "csd": g(5), "math": g(6),
                    "elect1": g(7), "elect2": g(8),
                    "m12": g(9), "catb": g(10), "catc": g(11),
                    "weights": weights, "weights_raw": raw,
                }

json.dump(progs, open("work/2027/raw/hkbu_ger_per_2027.json", "w"), indent=1, ensure_ascii=False)
print(len(progs))
for c, p in progs.items():
    print(c, "|", p["weights"], "|", p["weights_raw"][:80], "| e1:", p["elect1"][:40])
