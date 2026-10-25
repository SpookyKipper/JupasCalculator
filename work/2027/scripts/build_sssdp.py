"""
Build work/2027/SSSDP.json  (59 SSSDP programmes, 2027 entry)

Scores = 2026 intake (students admitted Sept 2026) from each operator's own
publication; entrance requirements = JUPAS 2027 programme pages.

Operator sources
----------------
HKMU (JSSU)  2026 JUPAS Admission Scores PDF (median + LQ + weightings)
             https://www.hkmu.edu.hk/REG/reg_ftae/Admission/Scores_JUPAS.pdf
HSUHK (JSSH) 2026 JUPAS Admission Score PDF (average, Best 5)
             https://admission.hsu.edu.hk/wp-content/uploads/2026/10/2026-JUPAS-Admission-Scores.pdf
TWC (JSST)   2026 JUPAS Admission Scores PDF (mean, Best 5)
             https://www.twc.edu.hk/uploads/files/TWC_2026_JUPAS_admission_scores.pdf
THEi (JSSV)  2026/27 Admission Scores (average of Eng+Chi+Math+CSD+1 elective)
             https://thei.edu.hk/admission/sssdp/
SFU (JSSA)   2026-27 JUPAS Admission Score image (mean, Best 5)
             https://www.sfu.edu.hk/en/admission/admission/sssdp-undergraduate-programmes-year-1-entry-/index.html
HKSYU / HKCHC / UOWCHK: no 2026 score table located -> nulls + "estimated".
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_hkmu import parse_pdf, to_minreq  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "raw")
OUT = os.path.join(ROOT, "SSSDP.json")

CODES = ['JSSA01', 'JSSA02', 'JSSA03', 'JSSA04', 'JSSA05', 'JSSA06', 'JSSC02',
         'JSSH01', 'JSSH02', 'JSSH03', 'JSSH04', 'JSSH05', 'JSSH06',
         'JSST01', 'JSST02', 'JSST03', 'JSST04', 'JSST05', 'JSST06', 'JSST07', 'JSST08',
         'JSSU12', 'JSSU14', 'JSSU15', 'JSSU18', 'JSSU40', 'JSSU50', 'JSSU55',
         'JSSU61', 'JSSU66', 'JSSU67', 'JSSU69', 'JSSU70', 'JSSU72', 'JSSU75',
         'JSSU77', 'JSSU78', 'JSSU79', 'JSSU90', 'JSSU93', 'JSSU95', 'JSSU96',
         'JSSU97',
         'JSSV01', 'JSSV02', 'JSSV03', 'JSSV04', 'JSSV05', 'JSSV07', 'JSSV08',
         'JSSV09', 'JSSV10', 'JSSV13', 'JSSV14',
         'JSSW01', 'JSSW02', 'JSSY01', 'JSSY02', 'JSSY03']

PREFIX_INST = {
    "JSSA": "SFU", "JSSC": "HKCHC", "JSSH": "HSUHK", "JSST": "TWC",
    "JSSU": "HKMU", "JSSV": "THEi", "JSSW": "UOWCHK", "JSSY": "HKSYU",
}

SRC = {
    "HKMU": ["https://www.hkmu.edu.hk/REG/reg_ftae/Admission/Scores_JUPAS.pdf"],
    "HSUHK": ["https://admission.hsu.edu.hk/wp-content/uploads/2026/10/2026-JUPAS-Admission-Scores.pdf"],
    "TWC": ["https://www.twc.edu.hk/uploads/files/TWC_2026_JUPAS_admission_scores.pdf"],
    "THEi": ["https://thei.edu.hk/admission/sssdp/"],
    "SFU": ["https://www.sfu.edu.hk/en/admission/admission/sssdp-undergraduate-programmes-year-1-entry-/index.html"],
    "HKSYU": ["https://uao.hksyu.edu/en/qualifications/dse"],
    "HKCHC": ["https://www.chuhai.edu.hk/"],
    "UOWCHK": ["https://www.uowchk.edu.hk/"],
}

# 2026 intake averages published by the operator (mean scores)
MEAN_2026 = {
    # HSUHK — average admission score, Best 5 (incl M1/M2)
    "JSSH01": 16.80, "JSSH02": 18.06, "JSSH03": 16.65,
    "JSSH04": 17.82, "JSSH05": 16.58, "JSSH06": 15.75,
    # TWC — admission mean score, best five subjects
    "JSST01": 17.6, "JSST02": 20.5, "JSST03": 22.4, "JSST04": 18.9,
    "JSST05": 20.0, "JSST06": 15.9, "JSST07": 15.5, "JSST08": 19.9,
    # THEi — average of best 5 (Eng, Chi, Math, CSD + 1 elective)
    "JSSV01": 15.0, "JSSV02": 15.0, "JSSV03": 16.0, "JSSV04": 14.0,
    "JSSV05": 16.0, "JSSV07": 17.0, "JSSV08": 15.0, "JSSV09": 15.0,
    "JSSV10": 15.0, "JSSV13": 14.0, "JSSV14": 15.0,
    # SFU — mean score (Best 5 subjects)
    "JSSA01": 16.0, "JSSA02": 16.0, "JSSA03": 20.0,
    "JSSA04": 17.0, "JSSA05": 15.0, "JSSA06": 15.0,
}

FORMULA = {
    "HKMU": ("Best 5 Subjects", "best5"),
    "HSUHK": ("Best 5 Subjects", "best5"),
    "TWC": ("Best 5 Subjects", "best5"),
    "SFU": ("Best 5 Subjects", "best5"),
    "THEi": ("Best 5 Subjects (English, Chinese, Mathematics, CSD + 1 elective)", "custom"),
    "HKSYU": ("Best 5 Subjects", "best5"),
    "HKCHC": ("Not published (believed Best 5)", "custom"),
    "UOWCHK": ("Not published (believed Best 5)", "custom"),
}

# THEi gives the DSE Physical Education subject a x2.0 weight (sports programmes)
THEI_PE_CODES = {"JSSV09", "JSSV13", "JSSV14"}


def inst_of(code):
    return PREFIX_INST[code[:4]]


def main():
    pages = json.load(open(os.path.join(RAW, "jupas_parsed.json"), encoding="utf-8"))
    hkmu_pdf = parse_pdf()

    records = []
    for code in CODES:
        inst = inst_of(code)
        page = pages.get(code, {})
        name = page.get("name") or hkmu_pdf.get(code, {}).get("name", "")
        formula, fid = FORMULA[inst]

        weights = {}
        scores = {"uq": None, "median": None, "lq": None, "mean": None}
        confidence = "official"
        notes = None

        if inst == "HKMU":
            pdf = hkmu_pdf.get(code)
            if pdf:
                weights = pdf["weights"]
                scores["median"] = float(pdf["median"]) if pdf["median"] is not None else None
                scores["lq"] = float(pdf["lq"]) if pdf["lq"] is not None else None
                if scores["median"] is None:
                    confidence = "partial"
                    notes = ("Listed on the JUPAS 2027 SSSDP catalogue but has no 2026 admission "
                             "figures in HKMU's 2026 JUPAS Admission Scores document (new programme).")
            else:
                confidence = "partial"
                notes = "No 2026 admission figures published by HKMU for this programme (new)."
        else:
            if code in MEAN_2026:
                scores["mean"] = MEAN_2026[code]
            else:
                confidence = "estimated"
                scores = {"uq": None, "median": None, "lq": None, "mean": None}
                notes = ("No official 2026 admission score located for this programme on the "
                         "operator's site (or JUPAS SSSDP scores hub, which still shows 2025). "
                         "Left null rather than estimated.")
            if inst == "THEi" and code in THEI_PE_CODES:
                weights = {"Physical Education": 2.0}

        # SFU/THEi/HSUHK/TWC publish no 2027 subject weighting table -> {} is the official answer
        rec = {
            "jupas_code": code,
            "institution": inst,
            "name": name,
            "formula_2027": formula,
            "formula_2027_id": fid,
            "subject_weights_2027": weights,
            "best_of_weights_2027": [],
            "min_requirements_2027": to_minreq(page),
            "scores_2026": scores,
            "score_grades_2026": None,
            "sources": SRC[inst] + [f"https://www.jupas.edu.hk/en/programme/sssdp/{code}/"],
            "confidence": confidence,
        }
        if notes:
            rec["notes"] = notes
        records.append(rec)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=1)

    print(f"{len(records)} SSSDP programmes -> {OUT}")
    from collections import Counter
    print("confidence:", Counter(r["confidence"] for r in records))
    for r in records:
        s = r["scores_2026"]
        fig = (f"med {s['median']}/lq {s['lq']}" if s["median"] is not None
               else (f"mean {s['mean']}" if s["mean"] is not None else "no score"))
        print(f"  {r['jupas_code']:7} {r['institution']:7} {fig:16} "
              f"{('w:' + ','.join(r['subject_weights_2027'])) if r['subject_weights_2027'] else '':22} {r['name'][:48]}")


if __name__ == "__main__":
    main()
