"""Build work/2027/CUHK.json from official CUHK 2027-cycle sources.

Sources
  * CUHK JUPAS score calculator data feed (2027 cycle):
    https://admission.cuhk.edu.hk/wp-content/uploads/data.json
    -> 2027 scoring formula, subject weightings, minimum entrance requirements
  * CUHK "Admission Grades of JUPAS Applicants (2026 Entry)" PDF (Oct 2026)
    https://admission.cuhk.edu.hk/wp-content/uploads/2026/10/Admission-Grades-2026.pdf
    -> 2026-intake UQ / median / LQ programme weighted totals (+ grades at those percentiles)
  * JUPAS programme pages (2027 exercise) used to cross-check every requirement.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
DATA_URL = "https://admission.cuhk.edu.hk/wp-content/uploads/data.json"
GRADES_PDF = "https://admission.cuhk.edu.hk/wp-content/uploads/2026/10/Admission-Grades-2026.pdf"
CALC_PAGE = ("https://admission.cuhk.edu.hk/application/jupas/"
             "programme-specific-requirements-and-score-calculator/")

SUBJ = {
    "ACHIN": "Chinese Language",
    "AENGL": "English Language",
    "AMATH": "Mathematics (Compulsory Part)",
    "AMTH1": "Mathematics Extended Part (Module 1)",
    "AMTH2": "Mathematics Extended Part (Module 2)",
    "ABIOL": "Biology",
    "ACHEM": "Chemistry",
    "APHYS": "Physics",
    "AECON": "Economics",
    "AINCT": "Information and Communication Technology",
    "ABAFS": "Business, Accounting and Financial Studies",
    "AGEOG": "Geography",
    "ADATE": "Design and Applied Technology",
    "ATLFS": "Technology and Living (Food Science and Technology)",
    "AHMSC": "Health Management and Social Care",
}


def canon(code: str) -> str:
    return SUBJ.get(code.strip(), code.strip())


def split_top(text: str):
    """Split on commas that are outside parentheses / brackets."""
    parts, depth, buf = [], 0, ""
    for ch in text:
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(buf)
            buf = ""
        else:
            buf += ch
    parts.append(buf)
    return [p.strip() for p in parts if p.strip()]


def parse_weight(weight: str):
    """Return (subject_weights, best_of_weights) from CUHK's weight string."""
    flat, groups = {}, []
    for item in split_top(weight):
        if ":" not in item:
            continue
        term, val = item.rsplit(":", 1)
        val = float(val)
        m = re.fullmatch(r"Best\((\d+),\[([A-Z0-9,]+)\]\)", term)
        if m:
            groups.append({
                "count": int(m.group(1)),
                "subjects": [canon(c) for c in m.group(2).split(",")],
                "weight": val,
            })
        else:
            flat[canon(term)] = val
    return flat, groups


def parse_formula(formula: str):
    """Return (total_subjects, compulsory [codes], groups [(n,[codes])], plain_best)."""
    total, compulsory, groups = 0, [], []
    for tok in formula.split("+"):
        tok = tok.strip()
        m = re.fullmatch(r"Best\((\d+)\)", tok)
        if m:
            total += int(m.group(1))
            continue
        m = re.fullmatch(r"Best\((\d+),\[([A-Z0-9,]+)\]\)", tok)
        if m:
            total += int(m.group(1))
            groups.append((int(m.group(1)), m.group(2).split(",")))
            continue
        compulsory.append(tok)
        total += 1
    return total, compulsory, groups


def formula_text(principle: str, compulsory, groups, total: int) -> str:
    if principle == "5 Subjects":
        base = "Best 5 Subjects"
    else:
        base = principle or f"Best {total} Subjects"
    notes = []
    if compulsory:
        names = [canon(c) for c in compulsory]
        if len(names) == 1:
            notes.append(f"{names[0]} must be included")
        elif len(names) == 2:
            notes.append(f"{names[0]} and {names[1]} must be included")
        else:
            notes.append(", ".join(names[:-1]) + f" and {names[-1]} must be included")
    for n, codes in groups:
        names = [canon(c) for c in codes]
        if n == 1:
            which = "one of "
        elif n == 2:
            which = "two of "
        else:
            which = f"{n} of "
        if len(names) == 2:
            joined = f"{names[0]} or {names[1]}"
        else:
            joined = ", ".join(names[:-1]) + f" or {names[-1]}"
        notes.append(f"{which}{joined} must be included")
    if not notes:
        return base
    return f"{base} ({'; '.join(notes)})"


def main() -> None:
    feed = json.loads((HERE / "cuhk_data.json").read_text())
    by_code = {}
    for row in feed:
        by_code.setdefault(row["code"], row)

    grades = {r["code"]: r for r in json.loads((HERE / "cuhk_grades_2026.json").read_text())}
    jupas = {r["code"]: r for r in json.loads((HERE / "jupas_pages_cuhk.json").read_text())}

    out = []
    for code in sorted(by_code):
        row = by_code[code]
        total, compulsory, groups = parse_formula(row["formula"])
        flat, best_of = parse_weight(row["weight"] or "")
        # drop any best-of group whose weight is not >1 (never happens, defensive)
        best_of = [g for g in best_of if g["weight"] > 1]
        flat = {k: v for k, v in flat.items() if v > 1}

        req = row["requirement"]
        elect = []
        for slot in req["ELECT"]:
            subjects = ["Any"] if slot["subject"] == "*" else [
                canon(s) for s in slot["subject"].replace(" ", "").split(",")]
            elect.append({"count": 1, "subjects": subjects, "grade": slot["score"]})
        while len(elect) < 2:
            elect.append({"count": 1, "subjects": ["Any"], "grade": "3"})

        g = grades.get(code)
        scores = None
        score_grades = None
        if g:
            scores = {
                "uq": g["totals"].get("UQ"),
                "median": g["totals"].get("M"),
                "lq": g["totals"].get("LQ"),
                "mean": None,
            }
            score_grades = {}
            for key, label in (("UQ", "uq"), ("M", "median"), ("LQ", "lq")):
                gr = g["grades"].get(key)
                if not gr:
                    continue
                score_grades[label] = {
                    "chi": gr["chi"] or None,
                    "eng": gr["eng"] or None,
                    "math": gr["math"] or None,
                    "csd": "A" if gr["csd"] == "TT" else (gr["csd"] or None),
                    "m1m2": gr["m1m2"] or None,
                    "electives": gr["electives"],
                }

        constrained = bool(compulsory or groups)
        if not constrained and total == 5:
            fid = "best5"
        elif not constrained and total == 6:
            fid = "best6"
        elif not constrained and total == 4:
            fid = "best4"
        else:
            fid = "custom"

        sources = [CALC_PAGE, DATA_URL, GRADES_PDF]
        if code in jupas:
            sources.append(jupas[code]["url"])

        out.append({
            "jupas_code": code,
            "institution": "CUHK",
            "name": row["name"],
            "formula_2027": formula_text(row["principle"], compulsory, groups, total),
            "formula_2027_id": fid,
            "subject_weights_2027": flat,
            "best_of_weights_2027": best_of,
            "min_requirements_2027": {
                "chi": req["CHI"],
                "eng": req["ENG"],
                "math": req["MATH"].replace("^", ""),
                "csd": "A",
                "elect1": elect[0],
                "elect2": elect[1],
            },
            "scores_2026": scores,
            "score_grades_2026": score_grades,
            "sources": sources,
            "confidence": "official" if g else "partial",
        })

    dest = ROOT / "work/2027/CUHK.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {len(out)} CUHK programmes -> {dest}")
    print("no 2026 grades:", [r["jupas_code"] for r in out if r["scores_2026"] is None])


if __name__ == "__main__":
    main()
