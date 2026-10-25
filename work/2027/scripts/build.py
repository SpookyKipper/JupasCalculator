"""Build work/2027/EdUHK.json and work/2027/LingnanU.json from the parsed raw sources.

Inputs (work/2027/raw/):
  eduhk_pdf_parsed.json   - EdUHK 2026 intake LQ/median + 2027 weightings (official EdUHK PDF)
  lnu_pdf_parsed.json     - Lingnan 2026 intake median/LQ + per-subject scores (official Lingnan PDF)
  lnu_weights_2027.json   - Lingnan 2027 Category A weightings (official Admission Requirements PDF)
  jupas_reqs_2027.json    - JUPAS 2027 programme pages: names + entrance requirements
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
RAW = os.path.join(ROOT, "work", "2027", "raw")
OUT = os.path.join(ROOT, "work", "2027")

CANON = json.load(open(os.path.join(ROOT, "data/raw/subjects.canonical.json")))
ALIASES = {k.lower(): v for k, v in CANON["aliases"].items()}
CANONICAL = set(CANON["core"] + CANON["category_a"] + CANON["category_c"] + CANON["category_b"])
CANONICAL |= set(CANON["math_extended"].values())

# extra spellings seen in EdUHK / Lingnan documents
EXTRA = {
    "english": "English Language",
    "math": "Mathematics (Compulsory Part)",
    "maths": "Mathematics (Compulsory Part)",
    "m1/m2": "Mathematics Extended Part (Module 1 or 2)",
    "mathematics extended m1/m2": "Mathematics Extended Part (Module 1 or 2)",
    "m1": "Mathematics Extended Part (Module 1)",
    "m2": "Mathematics Extended Part (Module 2)",
    "mathematics extended part module 1": "Mathematics Extended Part (Module 1)",
    "mathematics extended part module 2": "Mathematics Extended Part (Module 2)",
    "mathematics extended part module 1 (calculus & statistics)": "Mathematics Extended Part (Module 1)",
    "mathematics extended part module 2 (algebra & calculus)": "Mathematics Extended Part (Module 2)",
    "combined science": "Combined Science",
    "integrated science": "Integrated Science",
    "ict": "Information and Communication Technology",
    "dat": "Design and Applied Technology",
    "bafs (accounting/ business management)": "Business, Accounting and Financial Studies",
    "bafs (accounting/business management)": "Business, Accounting and Financial Studies",
    "specified apl subject(s)": "Specified ApL subject(s)",
    "technology and living": "Technology and Living (Food Science and Technology)",
}


def canon(name):
    n = re.sub(r"\s+", " ", name).strip()
    key = n.lower()
    if n in CANONICAL:
        return n
    if key in EXTRA:
        return EXTRA[key]
    if key in ALIASES:
        return ALIASES[key]
    title = n.title()
    for c in CANONICAL:
        if c.lower() == key:
            return c
    # last resort: return the title-cased source text (flagged by caller)
    return title


def parse_weight_text(text):
    """EdUHK weight cell -> (weights dict, best-of groups, unparsed leftovers)."""
    weights, groups, leftover = {}, [], []
    if not text:
        return weights, groups, leftover
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    block = []
    for ln in lines:
        block.append(ln)
        if ln.lower().startswith("(no subject weighting"):
            block = []
            continue
        m = re.match(r"^(?P<subj>.+?)\s*\(x\s*(?P<w>\d+(?:\.\d+)?)\s*\*?\)\s*$", ln)
        if not m:
            continue
        w = float(m.group("w"))
        body = " ".join(block).strip()
        best_of = False
        if body.lower().startswith("the best one subject of"):
            best_of = True
            body = re.sub(r"(?i)^the best one subject of", "", body)
        body = re.sub(r"(?i)\(\s*x\s*[\d.]+\s*\*?\s*\)", "", body).strip()
        body = re.sub(r"(?i)\s+or\s+$", "", body)
        body = re.sub(r"(?i)module\s*1\s+or\s*2", "M1/M2", body)
        parts = re.split(r"\s*(?:,|\bor\b)\s*", body)
        subs = []
        for p in parts:
            p = p.strip().rstrip(".").strip()
            if not p or p.lower() in ("and",):
                continue
            subs.append(canon(p))
        for s in subs:
            weights[s] = w
        if best_of and len(subs) > 1:
            groups.append(subs)
        block = []
    if block:
        leftover.append(" ".join(block))
    return weights, groups, leftover


def core_map(rows):
    out = {"chi": None, "eng": None, "math": None, "csd": None}
    for cells in rows[1:]:
        if len(cells) < 2:
            continue
        subj = cells[0].upper()
        grade = cells[1].strip()
        if grade.upper() == "ATTAINED":
            grade = "A"
        if "CHINESE" in subj and "CHI" not in subj.replace("CHINESE", "CHI"):
            pass
        if subj.startswith("CHINESE"):
            out["chi"] = grade
        elif subj.startswith("ENGLISH"):
            out["eng"] = grade
        elif subj.startswith("MATHEMATIC"):
            out["math"] = grade
        elif "CITIZENSHIP" in subj:
            out["csd"] = grade
    return out


def parse_electives(tables):
    """-> list of groups: {'subjects': [...], 'grade': g, 'count': n}"""
    groups = []
    for table in tables[:1]:  # first (programme-level) table only
        rows = [r for r in table[1:] if any(r)]
        i = 0
        option_block = False
        while i < len(rows):
            cells = rows[i]
            subj = cells[0].strip() if cells else ""
            grade = cells[1].strip() if len(cells) > 1 and cells[1] else ""
            if not grade:
                option_block = True
                i += 1
                continue
            up = subj.upper()
            m = re.match(r"ANY\s+(\d+)\s+SUBJECT", up)
            if m:
                option_block = False
                groups.append({"subjects": ["Any"], "grade": grade, "count": int(m.group(1))})
            else:
                subs = []
                norm = re.sub(r"(?i)module\s*1\s+or\s*2", "M1/M2", up)
                for p in re.split(r"\s+OR\s+", norm):
                    p = re.sub(r"\s*NOTE\d*$", "", p.strip()).strip()
                    if p:
                        subs.append(canon(p.title()))
                if option_block and groups and groups[-1].get("_option"):
                    groups[-1]["subjects"].extend(s for s in subs if s not in groups[-1]["subjects"])
                else:
                    groups.append({"subjects": subs, "grade": grade, "count": 1, "_option": option_block})
            i += 1
    return groups


def elect_slots(groups):
    """Assemble the 2-slot schema from parsed groups."""
    constrained = [g for g in groups if g["subjects"] != ["Any"]]
    anyg = [g for g in groups if g["subjects"] == ["Any"]]
    elect1 = elect2 = None
    if constrained:
        c = constrained[0]
        elect1 = {"count": 1, "subjects": c["subjects"], "grade": c["grade"]}
        rest = sum(g["count"] for g in anyg)
        if rest == 2:
            elect2 = {"count": 1, "subjects": ["Any"], "grade": anyg[0]["grade"]}
        elif rest >= 1:
            elect2 = {"count": rest, "subjects": ["Any"], "grade": anyg[0]["grade"]}
        else:
            elect2 = {"count": 0, "subjects": [], "grade": ""}
    elif anyg:
        total = sum(g["count"] for g in anyg)
        grade = anyg[0]["grade"]
        if total == 2:
            elect1 = {"count": 1, "subjects": ["Any"], "grade": grade}
            elect2 = {"count": 1, "subjects": ["Any"], "grade": grade}
        else:
            elect1 = {"count": total, "subjects": ["Any"], "grade": grade}
            elect2 = {"count": 0, "subjects": [], "grade": ""}
    return elect1, elect2


EDUHK_FORMULA = (
    "Best 5: sum of the five highest-scoring HKDSE subjects (core or elective; Citizenship and "
    "Social Development excluded), each subject's level value multiplied by its 2027 subject "
    "weighting. Category A conversion: 5**=7, 5*=6, 5=5, 4=4, 3=3, 2=2, 1=1 (EdUHK scale, not 8.5)."
)
LNU_FORMULA = (
    "Best 5: sum of the five highest weighted HKDSE subject scores (level value x 2027 subject "
    "weighting; subjects without a listed weighting count at x1). Conversion: 5**=7, 5*=6, 5=5, "
    "4=4, 3=3, 2=2, 1=1. Citizenship and Social Development is not counted."
)

SOURCES_EDUHK = [
    "https://www.eduhk.hk/acadprog/downloads/EdUHK_admission_scores_2026.pdf",
    "https://www.apply.eduhk.hk/ug/jupas_scores",
]
SOURCES_LNU = [
    "https://www.ln.edu.hk/admissions/ug/f/upload/642/3418/2026_Admissions%20Scores.pdf",
    "https://www.ln.edu.hk/admissions/ug/f/upload/629/3362/Admission%20Requirements_JUPAS%20(UG%20Website)%2026-27.pdf",
    "https://www.ln.edu.hk/admissions/ug/page/detail/114",
]

REQ_PDF_EDUHK = "https://www.eduhk.hk/acadprog/downloads/EdUHK_Entrance_Requirements.pdf"


def build_eduhk():
    scores = json.load(open(os.path.join(RAW, "eduhk_pdf_parsed.json")))
    reqs = json.load(open(os.path.join(RAW, "jupas_reqs_2027.json")))
    out = []
    issues = []
    for code, rec in scores.items():
        j = reqs.get(code, {})
        r = j.get("requirements", {})
        mins = core_map(r.get("core_tables", [[]])[0]) if r.get("core_tables") else {}
        e1, e2 = elect_slots(parse_electives(r.get("elective_tables", [])))
        weights, groups, leftover = parse_weight_text(rec["weights_2027_raw"])
        if leftover:
            issues.append((code, "unparsed weight text", leftover))
        out.append({
            "jupas_code": code,
            "institution": "EdUHK",
            "name": j.get("name_en") or rec["title"],
            "formula_2027": EDUHK_FORMULA,
            "formula_2027_id": "best5",
            "subject_weights_2027": weights,
            "best_of_weights_2027": groups,
            "min_requirements_2027": {
                "chi": mins.get("chi"),
                "eng": mins.get("eng"),
                "math": mins.get("math"),
                "csd": mins.get("csd"),
                "elect1": e1,
                "elect2": e2,
            },
            "scores_2026": {
                "uq": None,
                "median": rec["median"],
                "lq": rec["lq"],
                "mean": None,
            },
            "score_grades_2026": None,
            "sources": SOURCES_EDUHK + ([j["url"]] if j.get("url") else []),
            "confidence": "official",
        })
    out.sort(key=lambda x: x["jupas_code"])
    return out, issues


def build_lnu():
    scores = json.load(open(os.path.join(RAW, "lnu_pdf_parsed.json")))
    weights = json.load(open(os.path.join(RAW, "lnu_weights_2027.json")))
    reqs = json.load(open(os.path.join(RAW, "jupas_reqs_2027.json")))
    out, issues = [], []
    for code in sorted(scores):
        pass
    codes = sorted(set(scores) | set(weights))
    for code in codes:
        j = reqs.get(code, {})
        r = j.get("requirements", {})
        mins = core_map(r.get("core_tables", [[]])[0]) if r.get("core_tables") else {}
        e1, e2 = elect_slots(parse_electives(r.get("elective_tables", [])))
        w = {canon(k): v for k, v in weights.get(code, {}).items()}
        s = scores.get(code, {})
        grades = None
        if s.get("grades_median") or s.get("grades_lq"):
            grades = {
                "median": s.get("grades_median"),
                "lq": s.get("grades_lq"),
            }
        if not s.get("median"):
            issues.append((code, "missing 2026 score"))
        out.append({
            "jupas_code": code,
            "institution": "LingnanU",
            "name": j.get("name_en") or "",
            "formula_2027": LNU_FORMULA,
            "formula_2027_id": "best5",
            "subject_weights_2027": w,
            "best_of_weights_2027": [],
            "min_requirements_2027": {
                "chi": mins.get("chi"),
                "eng": mins.get("eng"),
                "math": mins.get("math"),
                "csd": mins.get("csd"),
                "elect1": e1,
                "elect2": e2,
            },
            "scores_2026": {
                "uq": None,
                "median": s.get("median"),
                "lq": s.get("lq"),
                "mean": None,
            },
            "score_grades_2026": grades,
            "sources": SOURCES_LNU + ([j["url"]] if j.get("url") else []),
            "confidence": "official",
        })
    return out, issues


CONVERSION_EDUHK = {
    "category_a": "5**=7, 5*=6, 5=5, 4=4, 3=3, 2=2, 1=1 (EdUHK 7-point scale, NOT the 8.5 scale)",
    "category_b_apl": "Attained with Distinction (II)=4, Attained with Distinction / (I)=3, Attained=0",
    "category_c_from_2025": "Japanese N1=7/N2=5/N3=4; Korean L6=7/L5=6/L4=5/L3=4; French/German/Spanish C2=7/C1=6/B2=5/B1=4/A2=3; Urdu A++/A+/A=7, B++=6, B+/B=5, C=4, D=3, E=2",
    "csd": "Citizenship and Social Development is excluded from the admission score",
    "best_five": "Sum of the best five subjects (core or elective, CSD excluded), subject weightings applied per programme",
}
CONVERSION_LNU = {
    "category_a": "5**=7, 5*=6, 5=5, 4=4, 3=3, 2=2, 1=1 (Lingnan 7-point scale)",
    "category_c": "Japanese N1=7/N2=6/N3=5; Korean L6=7/L5=6/L4=5/L3=4; French/German/Spanish C1,C2=7/B2=6/B1=5/A2=4; Urdu A++/A+/A=7, B++=6, B+=5, B=4, C=3, D=2, E=1",
    "apl": "Category B subjects may be recognised as electives, bonus scores or tie-breakers by individual programmes",
    "csd": "Citizenship and Social Development is not counted in the admission score",
    "best_five": "ANY Best Five Subject mechanism; each subject's level points multiplied by the programme's 2027 weighting",
}

META_EDUHK = {
    "dataset": "JUPAS 2027 entry (admission cycle 2027)",
    "generated": "2026-10-25",
    "scores_basis": "2026 intake (main round), weighted Best-5 scores as published by EdUHK on 15 Oct 2026",
    "weights_basis": "2027-entry weighting column of the same EdUHK PDF (authoritative for 2027 entry)",
    "requirements_basis": "official JUPAS 2027 programme pages (fetched 25 Oct 2026)",
    "not_published": "EdUHK publishes Lower Quartile and Median only: no UQ and no overall mean (the PDF's 'mean score of specific HKDSE subject' is a per-subject figure, not an overall mean) -> uq/mean are null",
    "revised_2027_weights_reference_scores": {
        "JS8012": "EdUHK also prints 2027-weighted reference scores: Lower Quartile 26.5, Median 27.5",
        "JS8702": "EdUHK also prints 2027-weighted reference scores: Lower Quartile 26.4, Median 26.6",
    },
    "high_proficiency_note": "JS8003/JS8004/JS8005/JS8674/JS8675 carry an EdUHK remark that the programme requires high Chinese or English proficiency and that the subject requirement cannot be substituted; the formal JUPAS table still lists level 3, which is what is recorded here",
    "subject_note": "'Specified ApL subject(s)' is EdUHK's placeholder for its list of weighted Applied Learning subjects (see EdUHK_ApL_Recognition_and_Subject_Weightings.pdf); ApL is not a Category A subject so no canonical name applies",
    "elective_note": "elect1/elect2 hold the two elective slots of the 332A22 baseline; a constrained slot lists the accepted subjects, 'Any' means any elective. JS8507 (Higher Diploma) requires any 3 electives, expressed as elect1.count=3 with elect2 empty",
    "best_of_note": "best_of_weights_2027 lists groups where only the best ONE subject of the group earns the weighting",
    "source_files": [
        "https://www.eduhk.hk/acadprog/downloads/EdUHK_admission_scores_2026.pdf",
        "https://www.apply.eduhk.hk/ug/jupas_scores",
    ],
}
META_LNU = {
    "dataset": "JUPAS 2027 entry (admission cycle 2027)",
    "generated": "2026-10-25",
    "scores_basis": "2026 intake (main round) weighted admission scores, Lingnan '2026 JUPAS Admission Scores (Main Round)' PDF",
    "weights_basis": "Lingnan 'JUPAS Admissions (2027 Entry)' PDF, section 5 Category A Subject Weighting for 2027 Entry",
    "requirements_basis": "official JUPAS 2027 programme pages (fetched 25 Oct 2026); BSc Data Science needs Maths level 3",
    "not_published": "Lingnan publishes Median and Lower Quartile only: no UQ, no mean -> uq/mean are null",
    "score_grades_note": "score_grades_2026 holds the per-subject median/LQ weighted scores (chi/eng/math/e1/e2) exactly as printed; these are separate per-subject figures and must not be summed as one candidate",
    "anomaly_note": "JS7305 Lower Quartile is printed as 21.5 against a Median of 28.5 - reproduced as published, worth re-checking against the 2027 cycle publication",
    "subject_note": "'Technology and Living' as printed by Lingnan is mapped to the canonical 'Technology and Living (Food Science and Technology)' via data/raw/subjects.canonical.json aliases; the Fashion, Clothing and Textiles strand is not separately identified in the source",
    "source_files": [
        "https://www.ln.edu.hk/admissions/ug/f/upload/642/3418/2026_Admissions%20Scores.pdf",
        "https://www.ln.edu.hk/admissions/ug/f/upload/629/3362/Admission%20Requirements_JUPAS%20(UG%20Website)%2026-27.pdf",
        "https://www.ln.edu.hk/admissions/ug/page/detail/114",
    ],
}


META_DIR = os.path.join(OUT, "meta")


def write(name, programmes, conversion, meta):
    """Programme list as a bare JSON array (same shape as PolyU.json / HKBU.json /
    CUHK.json, which validate.py expects).  The score-conversion table and the
    provenance notes live in work/2027/meta/<Institution>.json so that the
    institution files stay arrays."""
    with open(os.path.join(OUT, name), "w") as f:
        json.dump(programmes, f, ensure_ascii=False, indent=1)
    os.makedirs(META_DIR, exist_ok=True)
    payload = {"_conversion": conversion, "_meta": meta, "programme_count": len(programmes)}
    with open(os.path.join(META_DIR, name), "w") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    eduhk, ei = build_eduhk()
    lnu, li = build_lnu()
    write("EdUHK.json", eduhk, CONVERSION_EDUHK, META_EDUHK)
    write("LingnanU.json", lnu, CONVERSION_LNU, META_LNU)
    print("EdUHK", len(eduhk), "issues", ei)
    print("LingnanU", len(lnu), "issues", li)
