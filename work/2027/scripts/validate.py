import json, sys
from itertools import chain

canon = json.load(open("data/raw/subjects.canonical.json"))
names = set(chain(canon["core"], canon["category_a"], canon["category_c"], canon["category_b"],
                  canon.get("math_extended", {}).values(), canon.get("tokens", [])))
KEYS = ["jupas_code","institution","name","formula_2027","formula_2027_id","subject_weights_2027",
        "best_of_weights_2027","min_requirements_2027","scores_2026","score_grades_2026","sources","confidence"]
ok = True
for f in ["work/2027/PolyU.json", "work/2027/HKBU.json"]:
    d = json.load(open(f))
    print(f, len(d), "entries")
    codes = [r["jupas_code"] for r in d]
    assert len(codes) == len(set(codes)), "duplicate codes"
    for r in d:
        if list(r) != KEYS:
            print("  KEY MISMATCH", r["jupas_code"], set(r) ^ set(KEYS)); ok = False
        if r["formula_2027_id"] not in ("best5","best6","best4","custom"):
            print("  bad id", r["jupas_code"]); ok = False
        for s, w in r["subject_weights_2027"].items():
            if s not in names:
                print("  NON-CANONICAL weight subject:", r["jupas_code"], s); ok = False
            if not isinstance(w, (int, float)) or w <= 1:
                print("  bad weight", r["jupas_code"], s, w); ok = False
        if set(r["scores_2026"]) != {"uq","median","lq","mean"}:
            print("  scores keys", r["jupas_code"], r["scores_2026"]); ok = False
        if r["confidence"] not in ("official","partial","estimated"):
            print("  bad confidence", r["jupas_code"]); ok = False
        if not r["sources"] or not all(x.startswith("http") for x in r["sources"]):
            print("  bad sources", r["jupas_code"]); ok = False
        m = r["scores_2026"]
        if m["median"] is not None and m["lq"] is not None and m["median"] < m["lq"]:
            print("  median<lq", r["jupas_code"]); ok = False
        if not r["name"] or chr(0xF0) in r["name"] or "  " in r["name"]:
            print("  odd name", r["jupas_code"], repr(r["name"])); ok = False
print("OK" if ok else "ISSUES FOUND")
