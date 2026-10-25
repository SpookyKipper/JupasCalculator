"""Build work/2027/PolyU.json from official PolyU 2027 weighting PDFs, the 2026 admission
figures PDF and the 2027 programme pages."""
import json, re

dataset = json.load(open("data/processed/JUPAS_2027_Unified_Data.json"))
figures = json.load(open("work/2027/raw/polyu_figures_2026.json"))
sw = json.load(open("work/2027/raw/polyu_sw_2027.json"))
pages = json.load(open("work/2027/raw/polyu_pages_parsed.json"))

# 2027 code changes: JS3011 (2026 scheme) became JS3997 for 2027 entry.
CODE_MAP = {"JS3011": "JS3997"}

MIN_REQ = {
    "chi": "3", "eng": "3", "math": "2", "csd": "A",
    "elect1": {"count": 1, "subjects": ["Any"], "grade": "3", "note": ""},
    "elect2": {"count": 1, "subjects": ["Any"], "grade": "3", "note": ""},
}

out = []
for p in dataset:
    if p["institution"] != "PolyU":
        continue
    old_code = p["jupas_code"]
    code = CODE_MAP.get(old_code, old_code)

    weights = sw.get(code, {}).get("weights") or sw.get(old_code, {}).get("weights") or {}
    score_src = old_code if old_code in figures else code
    fig = figures.get(score_src) or figures.get(code) or {}

    page = pages.get(old_code) or pages.get(code) or {}
    mech = page.get("mechanism") or fig.get("mechanism") or ""
    mech = re.sub(r"\s+", " ", mech).strip()

    name = p["name_en"]
    if code != old_code:
        name = sw.get(code, {}).get("title") or name

    mean = fig.get("average")
    median = fig.get("median")
    lq = fig.get("lq")
    if page.get("avg") is not None and mean is None:
        mean = page.get("avg")

    sources = [
        "https://www.polyu.edu.hk/saso/docdrive/jupas/admission_figures.pdf",
        f"https://www.polyu.edu.hk/saso/docdrive/jupas/2027_{code}_SW.pdf",
        f"https://www.polyu.edu.hk/study/ug/jupas/2027/{code.lower()}",
    ]

    out.append({
        "jupas_code": code,
        "institution": "PolyU",
        "name": name,
        "formula_2027": mech,
        "formula_2027_id": "best5",
        "subject_weights_2027": dict(sorted(weights.items())),
        "best_of_weights_2027": [],
        "min_requirements_2027": MIN_REQ,
        "scores_2026": {"uq": None, "median": median, "lq": lq, "mean": mean},
        "score_grades_2026": None,
        "sources": sources,
        "confidence": "official" if (weights and mean is not None and code == old_code) else "partial",
    })

out.sort(key=lambda r: r["jupas_code"])
json.dump(out, open("work/2027/PolyU.json", "w"), indent=1, ensure_ascii=False)
print("entries", len(out))
print("no weights:", [r["jupas_code"] for r in out if not r["subject_weights_2027"]])
print("no scores:", [r["jupas_code"] for r in out if r["scores_2026"]["mean"] is None])
print("partial:", [r["jupas_code"] for r in out if r["confidence"] != "official"])
print("no formula:", [r["jupas_code"] for r in out if not r["formula_2027"]])
