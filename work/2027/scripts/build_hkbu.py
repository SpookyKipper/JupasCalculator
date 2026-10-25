"""Build work/2027/HKBU.json from the official 2027 GER/PER PDF plus the HKBU JUPAS score
calculator (2026 admission scores)."""
import json, re

pdf = json.load(open("work/2027/raw/hkbu_ger_per_2027.json"))
calc = json.load(open("work/2027/raw/hkbu_calc.json"))

SUBJ_KEYS = {"CHIN": "Chinese Language", "ENGL": "English Language",
             "MATH": "Mathematics (Compulsory Part)", "CSD": "Citizenship and Social Development"}


def parse_scores(block):
    """Extract mean and median/LQ grade profiles from the calculator block."""
    mean = None
    m = re.search(r"Study Programme's Mean\s*\n?\s*([\d.]+)", block)
    if m:
        mean = float(m.group(1))
    grades = {}
    for label, key in (("Median", "median"), ("Lower Quartile", "lq")):
        seg = re.search(label + r"(.*?)(?:Lower Quartile|The calculation of|$)", block, re.S)
        if not seg:
            continue
        toks = [t.strip() for t in seg.group(1).split("\n") if t.strip()]
        prof, i = {}, 0
        while i + 1 < len(toks):
            name, val = toks[i], toks[i + 1]
            if name in ("CHIN", "ENGL", "MATH", "CSD"):
                prof[SUBJ_KEYS[name]] = "Attained" if val == "Attained" else val
            elif name.startswith("Elec"):
                if val not in ("0", ""):
                    prof[f"Elective {name[-1]}"] = val
            i += 2
        if prof:
            grades[key] = prof
    return mean, (grades or None)


def parse_electives(p):
    e1, e2 = p["elect1"], p["elect2"]
    note = ""
    m = re.search(r"\((.*?)\)", e1)
    if m:
        note = m.group(1).strip()
    subjects = ["Any"]
    if note:
        if "Biology or Chemistry" in note:
            subjects = ["Biology", "Chemistry"]
        elif "Chemistry" in note:
            subjects = ["Chemistry"]
    grade = re.match(r"\s*(\d)", e1)
    out = {
        "elect1": {"count": 1, "subjects": subjects, "grade": grade.group(1) if grade else "3", "note": note},
        "elect2": {"count": 1, "subjects": ["Any"], "grade": "3", "note": ""},
    }
    return out


out = []
for code, p in sorted(pdf.items()):
    name = re.sub(r"\s+", " ", p["title"].replace("\uf072", "")).strip()
    elect = parse_electives(p)
    score = calc.get(code, {})
    mean, grades = parse_scores(score.get("scores_block", ""))

    out.append({
        "jupas_code": code,
        "institution": "HKBU",
        "name": name,
        "formula_2027": "Best 5 Subjects",
        "formula_2027_id": "best5",
        "subject_weights_2027": {k: v for k, v in sorted(p["weights"].items()) if v > 1},
        "best_of_weights_2027": [],
        "min_requirements_2027": {
            "chi": re.match(r"\s*(\d)", p["chi"]).group(1) if re.match(r"\s*(\d)", p["chi"]) else "3",
            "eng": re.match(r"\s*(\d)", p["eng"]).group(1) if re.match(r"\s*(\d)", p["eng"]) else "3",
            "math": re.match(r"\s*(\d)", p["math"]).group(1) if re.match(r"\s*(\d)", p["math"]) else "2",
            "csd": "A",
            **elect,
        },
        "scores_2026": {"uq": None, "median": None, "lq": None, "mean": mean},
        "score_grades_2026": grades,
        "sources": [
            "https://admissions.hkbu.edu.hk/content/dam/ao-assets/document/news/JUPAS_GER_PER.pdf",
            "https://admissions.hkbu.edu.hk/ug/jupas_weighting",
        ],
        # JS2030 / JS2050 were split out of the 2026 combined BA/BM (JS2060) entry; HKBU
        # republishes the same 2026 statistics for both, so treat them as inherited.
        "confidence": "partial" if code in ("JS2030", "JS2050") else ("official" if mean is not None else "partial"),
    })

json.dump(out, open("work/2027/HKBU.json", "w"), indent=1, ensure_ascii=False)
print("entries", len(out))
print("no mean:", [r["jupas_code"] for r in out if r["scores_2026"]["mean"] is None])
print("no grades:", [r["jupas_code"] for r in out if not r["score_grades_2026"]])
for r in out:
    print(r["jupas_code"], r["scores_2026"]["mean"], "|", r["subject_weights_2027"] or "{}", "|", r["confidence"])
