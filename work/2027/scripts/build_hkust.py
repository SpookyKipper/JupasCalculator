"""Build work/2027/HKUST.json from official HKUST 2027-cycle sources.

Sources
  * HKUST "Undergraduate Programs & 2027 JUPAS Admissions Requirements"
    (https://join.hkust.edu.hk/docs/ADMISSIONS REQUIREMENTS AND SCORE FORMULAE.pdf)
    -> 2027 minimum entrance requirements, 2027 Best-5 score formulae + subject weightings
  * HKUST "2026 HKUST JUPAS Admissions Scores"
    (https://join.hkust.edu.hk/docs/2026_HKUST_JUPAS_ADMISSIONS_SCORES.pdf)
    -> 2026-intake median / lower quartile weighted scores (no upper quartile is published)
  * JUPAS 2027 programme pages -> cross-check of core requirements + programme-specific
    elective groups; used for programmes whose row in the PDF is a merged cell.

Formulae are transcribed from the PDF table; every programme's weighting multipliers are
listed explicitly so the values can be audited against the PDF.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent

REQ_PDF = "https://join.hkust.edu.hk/docs/ADMISSIONS%20REQUIREMENTS%20AND%20SCORE%20FORMULAE.pdf"
SCORES_PDF = "https://join.hkust.edu.hk/docs/2026_HKUST_JUPAS_ADMISSIONS_SCORES.pdf"
JUPAS_PAGE = "https://www.jupas.edu.hk/en/programme/hkust/{code}/"

E = "English Language"
C = "Chinese Language"
M = "Mathematics (Compulsory Part)"
M1 = "Mathematics Extended Part (Module 1)"
M2 = "Mathematics Extended Part (Module 2)"
BIO, CHEM, PHY = "Biology", "Chemistry", "Physics"
ICT = "Information and Communication Technology"
ECON, DAT = "Economics", "Design and Applied Technology"

SCI_SPEC = ["Biology", "Chemistry", "Physics", M1, M2]
ENG_SPEC = ["Biology", "Chemistry", "Physics", ICT]

# code: (name, formula text, weights, best-of groups, programme-specific elective group, confidence)
SPEC = {
    "JS5101": ("International Research Enrichment",
               "English + Mathematics + Best 2 from Biology/Chemistry/Physics/M1/M2 + Best 1 other subject",
               {}, [], SCI_SPEC, "official"),
    "JS5102": ("Science (Group A)",
               "English x1.5 + Mathematics + Best from Biology/Chemistry/Physics/M1/M2 + Best 2 other subjects "
               "(Physics/M1/M2 x2; Biology/Chemistry x1.5)",
               {E: 1.5, PHY: 2, M1: 2, M2: 2, BIO: 1.5, CHEM: 1.5}, [], None, "official"),
    "JS5103": ("Science (Group B)",
               "English x1.5 + Mathematics + Best from Biology/Chemistry/Physics/M1/M2 + Best 2 other subjects "
               "(Biology/Chemistry x2; Physics/M1/M2 x1.5)",
               {E: 1.5, BIO: 2, CHEM: 2, PHY: 1.5, M1: 1.5, M2: 1.5}, [], None, "official"),
    "JS5118": ("BSc in Biomedical and Health Sciences",
               "", {}, [], SCI_SPEC, "partial"),
    "JS5181": ("Science (Group A) with Extended Major in Artificial Intelligence",
               "English x1.5 + Mathematics + Best from Biology/Chemistry/Physics/M1/M2 + Best 2 other subjects "
               "(Physics/M1/M2 x2; Biology/Chemistry x1.5)",
               {E: 1.5, PHY: 2, M1: 2, M2: 2, BIO: 1.5, CHEM: 1.5}, [], None, "official"),
    "JS5212": ("BEng in Computer Engineering",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Physics x2; ICT x1.5; Biology/Chemistry x1; M1/M2 x2)",
               {E: 2, M: 2, PHY: 2, ICT: 1.5, BIO: 1, CHEM: 1, M1: 2, M2: 2}, [], ENG_SPEC, "official"),
    "JS5220": ("Department of Chemical and Biological Engineering",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Biology/Chemistry/Physics x2; ICT x1.5; M1/M2 x2)",
               {E: 2, M: 2, BIO: 2, CHEM: 2, PHY: 2, ICT: 1.5, M1: 2, M2: 2}, [], ENG_SPEC, "official"),
    "JS5230": ("Department of Civil and Environmental Engineering",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Chemistry/Physics x2; ICT x1.5; Biology x1; M1/M2 x2)",
               {E: 2, M: 2, CHEM: 2, PHY: 2, ICT: 1.5, BIO: 1, M1: 2, M2: 2}, [], ENG_SPEC, "official"),
    "JS5240": ("Department of Computer Science and Engineering",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Physics x2; ICT x1.5; Biology/Chemistry x1; M1/M2 x2)",
               {E: 2, M: 2, PHY: 2, ICT: 1.5, BIO: 1, CHEM: 1, M1: 2, M2: 2}, [], ENG_SPEC, "official"),
    "JS5250": ("Department of Electronic and Computer Engineering",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Physics x2; ICT x1.5; Biology/Chemistry x1; M1/M2 x2)",
               {E: 2, M: 2, PHY: 2, ICT: 1.5, BIO: 1, CHEM: 1, M1: 2, M2: 2}, [], ENG_SPEC, "official"),
    "JS5260": ("Department of Industrial Engineering and Decision Analytics",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Physics x2; ICT x1.5; Biology/Chemistry x1; M1/M2 x2)",
               {E: 2, M: 2, PHY: 2, ICT: 1.5, BIO: 1, CHEM: 1, M1: 2, M2: 2}, [], ENG_SPEC, "official"),
    "JS5270": ("Department of Mechanical and Aerospace Engineering",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Biology/Chemistry/Physics x2; ICT x1; M1/M2 x1.5)",
               {E: 2, M: 2, BIO: 2, CHEM: 2, PHY: 2, ICT: 1, M1: 1.5, M2: 1.5}, [], ENG_SPEC, "official"),
    "JS5282": ("Engineering with Extended Major in Artificial Intelligence",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Biology/Chemistry/Physics x2; ICT x1.5; M1/M2 x1.5)",
               {E: 2, M: 2, BIO: 2, CHEM: 2, PHY: 2, ICT: 1.5, M1: 1.5, M2: 1.5}, [], ENG_SPEC, "official"),
    "JS5300": ("Business and Management",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5311": ("BBA in Economics",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5312": ("BBA in Finance",
               "English x2 + Mathematics x2 + better of (Best 3 other subjects) OR "
               "(Best of Chemistry/Economics/Physics/M1/M2 x1.5 + Best 2 other subjects)",
               {E: 2, M: 2}, [{"count": 1, "subjects": [CHEM, ECON, PHY, M1, M2], "weight": 1.5}],
               None, "official"),
    "JS5313": ("BBA in Global Business",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5314": ("BBA in Information Systems",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5315": ("BBA in Management",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5316": ("BBA in Marketing",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5317": ("BBA in Operations Management",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5318": ("BBA in Professional Accounting",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5331": ("BSc in Economics and Finance",
               "English x2 + Mathematics x2 + better of (Best 3 other subjects) OR "
               "(Best of Chemistry/Economics/Physics/M1/M2 x1.5 + Best 2 other subjects)",
               {E: 2, M: 2}, [{"count": 1, "subjects": [CHEM, ECON, PHY, M1, M2], "weight": 1.5}],
               None, "official"),
    "JS5332": ("BSc in Quantitative Finance",
               "English x2 + Mathematics x2 + better of (Best 3 other subjects) OR "
               "(Best of Chemistry/Economics/Physics/M1/M2 x1.5 + Best 2 other subjects)",
               {E: 2, M: 2}, [{"count": 1, "subjects": [CHEM, ECON, PHY, M1, M2], "weight": 1.5}],
               None, "official"),
    "JS5411": ("BSc in Global China Studies",
               "English x2 + Chinese x1.5 + Best 3 other subjects",
               {E: 2, C: 1.5}, [], None, "official"),
    "JS5412": ("BSc in Quantitative Social Analysis",
               "English x2 + Mathematics x2 + Best 3 other subjects (M1/M2 x1.5)",
               {E: 2, M: 2, M1: 1.5, M2: 1.5}, [], None, "official"),
    "JS5711": ("BSc in Innovation, Design and Technology",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/Design and Applied Technology/ICT "
               "+ Best 2 other subjects (Biology/Chemistry/Physics/DAT x2; ICT x1; M1/M2 x1.5)",
               {E: 2, M: 2, BIO: 2, CHEM: 2, PHY: 2, DAT: 2, ICT: 1, M1: 1.5, M2: 1.5}, [],
               ["Biology", "Chemistry", "Physics", DAT, ICT], "official"),
    "JS5712": ("BSc in Individualized Interdisciplinary Major",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5812": ("BSc in Environmental Management and Technology",
               "English x2 + Mathematics x2 + Best 3 other subjects", {E: 2, M: 2}, [], None, "official"),
    "JS5901": ("BEng/BSc & BBA Dual Degree Program in Technology and Management",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/ICT + Best 2 other subjects "
               "(Biology/Chemistry/Physics x2; ICT x1; M1/M2 x1.5)",
               {E: 2, M: 2, BIO: 2, CHEM: 2, PHY: 2, ICT: 1, M1: 1.5, M2: 1.5}, [], ENG_SPEC, "official"),
    "JS5811": ("BSc in Biotechnology and Business",
               "English x2 + Mathematics x2 + Best of Biology/Chemistry x1.5 + Best 2 other subjects",
               {E: 2, M: 2}, [{"count": 1, "subjects": [BIO, CHEM], "weight": 1.5}],
               ["Biology", "Chemistry"], "official"),
    "JS5813": ("BSc in Mathematics and Economics",
               "English x2 + Mathematics x2 + Best from Biology/Chemistry/Physics/Economics/M1/M2 + Best 2 other "
               "subjects (M1/M2 x2; Biology/Chemistry/Physics/Economics x1.5)",
               {E: 2, M: 2, M1: 2, M2: 2, BIO: 1.5, CHEM: 1.5, PHY: 1.5, ECON: 1.5}, [],
               ["Biology", "Chemistry", "Physics", ECON, M1, M2], "official"),
    "JS5814": ("BSc in Risk Management and Business Intelligence",
               "English x2 + Mathematics x2 + Best 3 other subjects (M1/M2 x1.5)",
               {E: 2, M: 2, M1: 1.5, M2: 1.5}, [], None, "official"),
    "JS5822": ("BSc in Sustainable and Green Finance",
               "English x2 + Mathematics x2 + better of (Best 3 other subjects) OR "
               "(Best of Chemistry/Economics/Physics/M1/M2 x1.5 + Best 2 other subjects)",
               {E: 2, M: 2}, [{"count": 1, "subjects": [CHEM, ECON, PHY, M1, M2], "weight": 1.5}],
               None, "official"),
}

CUSTOM = {"JS5312", "JS5331", "JS5332", "JS5822", "JS5118"}


def clean_title(title: str) -> str:
    return re.split(r"[\u3000-\u9fff\uff00-\uffef]", title)[0].strip()


def main() -> None:
    scores = {r["code"]: r for r in json.loads((HERE / "hkust_scores_2026.json").read_text())}
    pages = {r["code"]: r for r in json.loads((HERE / "jupas_pages_hkust.json").read_text())}

    out = []
    for code in sorted(SPEC):
        name, formula, weights, best_of, spec_group, conf = SPEC[code]
        page = pages.get(code, {})
        core = {re.sub(r"\s*Note\d+", "", k).strip(): v for k, v in page.get("core", {}).items()}
        elect1 = {"count": 1, "subjects": spec_group, "grade": "3"} if spec_group else \
                 {"count": 1, "subjects": ["Any"], "grade": "3"}
        s = scores.get(code)
        out.append({
            "jupas_code": code,
            "institution": "HKUST",
            "name": name,
            "formula_2027": formula,
            "formula_2027_id": "custom" if code in CUSTOM else "best5",
            # only weightings above 1.0 are recorded (1.0 is the default)
            "subject_weights_2027": {k: v for k, v in weights.items() if v > 1},
            "best_of_weights_2027": best_of,
            "min_requirements_2027": {
                "chi": core.get("CHINESE LANGUAGE", "3"),
                "eng": core.get("ENGLISH LANGUAGE"),
                "math": core.get("MATHEMATICS COMPULSORY PART"),
                "csd": "A",
                "elect1": elect1,
                "elect2": {"count": 1, "subjects": ["Any"], "grade": "3"},
            },
            "scores_2026": None if not s else {
                "uq": None,          # HKUST publishes highest attainable / median / LQ only
                "median": s["median"],
                "lq": s["lq"],
                "mean": None,
            },
            "score_grades_2026": None,
            "sources": [REQ_PDF, SCORES_PDF, JUPAS_PAGE.format(code=code)],
            "confidence": "partial" if (code in ("JS5118", "JS5712") or not s) else conf,
        })

    dest = ROOT / "work/2027/HKUST.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"wrote {len(out)} HKUST programmes -> {dest}")
    for r in out:
        if r["scores_2026"] is None or not r["formula_2027"]:
            print("  gap:", r["jupas_code"], r["name"], "scores" if not r["scores_2026"] else "",
                  "formula" if not r["formula_2027"] else "")


if __name__ == "__main__":
    main()
