"""Validate work/2027/CUHK.json and HKUST.json against the agreed record schema."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
KEYS = ["jupas_code", "institution", "name", "formula_2027", "formula_2027_id",
        "subject_weights_2027", "best_of_weights_2027", "min_requirements_2027",
        "scores_2026", "score_grades_2026", "sources", "confidence"]
MINREQ = ["chi", "eng", "math", "csd", "elect1", "elect2"]
CANON = json.loads((ROOT / "data/raw/subjects.canonical.json").read_text())
ALLOWED = set(sum([v for k, v in CANON.items() if isinstance(v, list)], []))
ALLOWED |= {"Any", "Mathematics Extended Part (Module 1)", "Mathematics Extended Part (Module 2)"}

problems = []
for inst in ("CUHK", "HKUST"):
    recs = json.loads((ROOT / f"work/2027/{inst}.json").read_text())
    codes = [r["jupas_code"] for r in recs]
    assert len(codes) == len(set(codes)), f"{inst}: duplicate codes"
    for r in recs:
        tag = f"{inst} {r.get('jupas_code')}"
        if list(r) != KEYS:
            problems.append(f"{tag}: key mismatch {list(r)}")
        if r["institution"] != inst:
            problems.append(f"{tag}: institution {r['institution']}")
        if r["formula_2027_id"] not in ("best5", "best6", "best4", "custom"):
            problems.append(f"{tag}: formula id {r['formula_2027_id']}")
        if r["confidence"] not in ("official", "partial", "estimated"):
            problems.append(f"{tag}: confidence {r['confidence']}")
        for s, w in r["subject_weights_2027"].items():
            if s not in ALLOWED:
                problems.append(f"{tag}: non-canonical weight subject {s!r}")
            if not isinstance(w, (int, float)) or w <= 1:
                problems.append(f"{tag}: weight not >1 ({s}={w})")
        for g in r["best_of_weights_2027"]:
            if set(g) != {"count", "subjects", "weight"}:
                problems.append(f"{tag}: best_of keys {set(g)}")
            for s in g["subjects"]:
                if s not in ALLOWED:
                    problems.append(f"{tag}: non-canonical best-of subject {s!r}")
            if not (isinstance(g["count"], int) and g["count"] >= 1):
                problems.append(f"{tag}: best_of count {g['count']}")
        mr = r["min_requirements_2027"]
        if list(mr) != MINREQ:
            problems.append(f"{tag}: min_requirements keys {list(mr)}")
        for k in ("elect1", "elect2"):
            e = mr[k]
            if set(e) != {"count", "subjects", "grade"}:
                problems.append(f"{tag}: {k} keys {set(e)}")
            for s in e["subjects"]:
                if s not in ALLOWED:
                    problems.append(f"{tag}: non-canonical elect subject {s!r}")
        sc = r["scores_2026"]
        if sc is not None:
            if set(sc) != {"uq", "median", "lq", "mean"}:
                problems.append(f"{tag}: scores keys {set(sc)}")
            vals = [v for v in (sc["uq"], sc["median"], sc["lq"]) if v is not None]
            if any(not isinstance(v, (int, float)) for v in vals):
                problems.append(f"{tag}: non-numeric score {vals}")
            if len(vals) >= 2 and max(vals) > 100:
                problems.append(f"{tag}: suspicious score {vals}")
        if not r["sources"]:
            problems.append(f"{tag}: no sources")

print(f"{len(problems)} problem(s)")
for p in problems:
    print(" -", p)
