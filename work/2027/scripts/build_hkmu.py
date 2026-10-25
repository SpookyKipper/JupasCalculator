"""
Build work/2027/HKMU.json

Sources
-------
* Scores + subject weighting multipliers: HKMU "2026 JUPAS Admission Scores"
  https://www.hkmu.edu.hk/REG/reg_ftae/Admission/Scores_JUPAS.pdf
  (published Sept 2026 -> scores of students admitted to the 2026 intake)
* 2027 entrance requirements + weighted-subject hints: JUPAS 2027 programme pages
  https://www.jupas.edu.hk/en/programme/hkmu/JS9009/ (parsed by fetch_jupas.py)

Formula: HKMU "Best 5" = best 5 subjects among Category A / B / C
(Cat A 5**=7 ... 2=2; Cat B Attained w/ Distinction (II)=4, (I)=3, Attained=2;
Cat C A=7..E=2). See the PDF's Grade Conversion Tables.
"""
import json
import os
import re

import pdfplumber

from fetch_jupas import HKMU_CODES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
PDF = os.path.join(RAW, "Scores_JUPAS.pdf")
OUT = os.path.join(ROOT, "HKMU.json")

CODE_RE = re.compile(r"^(JS[A-Z]{0,2}\d{2,4})\^?$")
NUM_RE = re.compile(r"^\d+$")
W_RE = re.compile(r"([A-Za-z][A-Za-z &/\-\.]*?)\s*\(x\s*([\d.]+)\)")

ABBREV = {
    "chi lang": "Chinese Language",
    "eng lang": "English Language",
    "chi literature": "Chinese Literature",
    "chinese literature": "Chinese Literature",
    "math": "Mathematics (Compulsory Part)",
    "mathematics": "Mathematics (Compulsory Part)",
    "math (compulsory part)": "Mathematics (Compulsory Part)",
    "biology": "Biology",
    "chemistry": "Chemistry",
    "physics": "Physics",
    "economics": "Economics",
    "geography": "Geography",
    "history": "History",
    "chinese history": "Chinese History",
    "ict": "Information and Communication Technology",
    "bafs": "Business, Accounting and Financial Studies",
    "visual arts": "Visual Arts",
    "music": "Music",
    "physical education": "Physical Education",
    "health management and social care": "Health Management and Social Care",
    "technology and living": "Technology and Living (Food Science and Technology)",
    "design and applied technology": "Design and Applied Technology",
    "tourism and hospitality studies": "Tourism and Hospitality Studies",
    "ethics and religious studies": "Ethics and Religious Studies",
    "integrated science": "Integrated Science",
    "combined science": "Combined Science: Biology + Chemistry",
    "child care & edu": "Child Care and Education",
    "child care & dev": "Child Care and Development",
    "health management & social care": "Health Management and Social Care",
}


def canon(name):
    n = re.sub(r"\s+", " ", name).strip()
    low = n.lower()
    if low in ABBREV:
        return ABBREV[low]
    for k, v in ABBREV.items():
        if low.startswith(k):
            return v
    return n


def parse_pdf():
    """Return {code: {name, median, lq, weights_raw}} using word x-positions."""
    programmes = {}
    order = []
    cur = None
    school = ""

    with pdfplumber.open(PDF) as pdf:
        for page in pdf.pages[1:]:
            words = page.extract_words(keep_blank_chars=False, use_text_flow=False)
            rows = {}
            for w in words:
                key = round(w["top"] / 6.0)
                rows.setdefault(key, []).append(w)
            for key in sorted(rows):
                ws = sorted(rows[key], key=lambda w: w["x0"])
                col = {0: [], 1: [], 2: [], 3: [], 4: []}
                for w in ws:
                    x = w["x0"]
                    if x < 90:
                        col[0].append(w["text"])
                    elif x < 362:
                        col[1].append(w["text"])
                    elif x < 420:
                        col[2].append(w["text"])
                    elif x < 460:
                        col[3].append(w["text"])
                    else:
                        col[4].append(w["text"])
                c0 = " ".join(col[0]).strip()
                name_t = " ".join(col[1]).strip()
                med = " ".join(col[2]).strip()
                lq = " ".join(col[3]).strip()
                wgt = " ".join(col[4]).strip()

                mcode = CODE_RE.match(c0)
                if mcode:
                    code = mcode.group(1)
                    cur = {"code": code, "school": school, "name_parts": [],
                           "median": None, "lq": None, "wgt_parts": []}
                    if name_t:
                        cur["name_parts"].append(name_t)
                    if NUM_RE.match(med):
                        cur["median"] = int(med)
                    if NUM_RE.match(lq):
                        cur["lq"] = int(lq)
                    if wgt and wgt != "-":
                        cur["wgt_parts"].append(wgt)
                    programmes[code] = cur
                    order.append(code)
                elif c0 and not name_t and not med and not lq:
                    school = c0  # school section header
                    cur = None
                elif cur is not None:
                    if name_t:
                        cur["name_parts"].append(name_t)
                    if NUM_RE.match(med) and cur["median"] is None:
                        cur["median"] = int(med)
                    if NUM_RE.match(lq) and cur["lq"] is None:
                        cur["lq"] = int(lq)
                    if wgt and wgt != "-":
                        cur["wgt_parts"].append(wgt)

    out = {}
    for code in order:
        p = programmes[code]
        raw = " ".join(p.pop("wgt_parts"))
        raw = re.sub(r"\s*\(x\s*", " (x", raw)
        weights = {}
        for subj, val in W_RE.findall(raw):
            cname = canon(subj)
            weights[cname] = float(val)
        p["name"] = re.sub(r"\s+", " ", " ".join(p["name_parts"])).strip()
        p.pop("name_parts")
        p["weights"] = weights
        p["weights_raw"] = raw
        out[code] = p
    return out


def to_minreq(page):
    """JUPAS page -> min_requirements_2027 dict."""
    if not page:
        return None
    core = {re.sub(r"\s*Note\d+\s*", "", k).lower(): v for k, v in page.get("core", [])}
    req = {
        "chi": core.get("chinese language"),
        "eng": core.get("english language"),
        "math": core.get("mathematics compulsory part"),
        "csd": "A" if (core.get("citizenship and social development", "").lower()
                       .startswith("attained")) else core.get("citizenship and social development"),
    }
    ele = page.get("electives", [])
    slots = []
    for subj, lvl in ele:
        s = re.sub(r"\s*Note\d+\s*", "", subj).strip()
        lvl_clean = "2" if lvl.strip().lower().startswith("note") is False else lvl
        count = 1
        m = re.match(r"ANY\s+(\d+)\s+SUBJECTS?", s, re.I)
        if m:
            count = int(m.group(1))
            subjects = ["Any"]
        elif re.match(r"ANY\s+1\s+SUBJECT", s, re.I):
            subjects = ["Any"]
        else:
            subjects = [canon(x.strip()) for x in re.split(r"[/,;]| OR ", s) if x.strip()]
        note = None
        if "EXCLUDING APPLIED LEARNING, OTHER LANGUAGE" in s.upper():
            subjects = ["Any"]
            note = "Excluding Applied Learning and Other Language subjects"
        for _ in range(count):
            slot = {"count": 1, "subjects": subjects, "grade": lvl_clean}
            if note:
                slot["note"] = note
            slots.append(slot)
    if slots:
        req["elect1"] = slots[0]
    if len(slots) > 1:
        req["elect2"] = slots[1]
    return req


def main():
    pdf_data = parse_pdf()
    pages = json.load(open(os.path.join(RAW, "jupas_parsed.json"), encoding="utf-8"))

    records = []
    for code in HKMU_CODES:
        p = pdf_data.get(code)
        page = pages.get(code, {})
        if p is None:
            # offered in the 2027 catalogue but absent from the 2026 score document (new)
            records.append({
                "jupas_code": code,
                "institution": "HKMU",
                "name": page.get("name", ""),
                "formula_2027": "Best 5 Subjects",
                "formula_2027_id": "best5",
                "subject_weights_2027": {},
                "best_of_weights_2027": [],
                "min_requirements_2027": to_minreq(page),
                "scores_2026": {"uq": None, "median": None, "lq": None, "mean": None},
                "score_grades_2026": None,
                "sources": [
                    "https://www.hkmu.edu.hk/REG/reg_ftae/Admission/Scores_JUPAS.pdf",
                    f"https://www.jupas.edu.hk/en/programme/hkmu/{code}/",
                ],
                "confidence": "partial",
                "notes": ("Offered in the 2027 JUPAS catalogue but not listed in HKMU's 2026 "
                          "JUPAS Admission Scores document (new programme; no 2026 intake)."),
            })
            continue
        weights = p["weights"]
        # programmes listed by JUPAS as carrying heavier weight (2027 page) that the
        # 2026 score PDF does not show explicitly are recorded as nominal x1.0? No --
        # keep only published multipliers, but note the mismatch in "notes".
        rec = {
            "jupas_code": code,
            "institution": "HKMU",
            "name": p["name"],
            "formula_2027": "Best 5 Subjects",
            "formula_2027_id": "best5",
            "subject_weights_2027": weights,
            "best_of_weights_2027": [],
            "min_requirements_2027": to_minreq(page),
            "scores_2026": {"uq": None, "median": float(p["median"]) if p["median"] is not None else None,
                            "lq": float(p["lq"]) if p["lq"] is not None else None,
                            "mean": None},
            "score_grades_2026": None,
            "sources": [
                "https://www.hkmu.edu.hk/REG/reg_ftae/Admission/Scores_JUPAS.pdf",
                f"https://www.jupas.edu.hk/en/programme/hkmu/{code}/",
            ],
            "confidence": "official",
        }
        records.append(rec)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    print(f"{len(records)} HKMU programmes -> {OUT}")
    for r in records:
        w = ", ".join(f"{k} x{v}" for k, v in r["subject_weights_2027"].items()) or "-"
        print(f"  {r['jupas_code']} med={r['scores_2026']['median']} lq={r['scores_2026']['lq']} | {w} | {r['name'][:60]}")


if __name__ == "__main__":
    main()
