import json, re, glob, os
from bs4 import BeautifulSoup

rows = {}
for path in sorted(glob.glob("work/2027/raw/polyu_pages/JS*.html")):
    code = os.path.basename(path)[:-5]
    s = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    for t in s(["script", "style", "noscript"]):
        t.decompose()
    txt = s.get_text("\n")
    lines = [l.strip() for l in txt.split("\n")]
    lines = [l for l in lines if l]

    def after(label, n=60):
        for i, l in enumerate(lines):
            if l.startswith(label):
                return lines[i:i + n]
        return []

    mech = ""
    blk = after("Admission Score Calculation Mechanism", 12)
    if len(blk) > 1:
        mech = blk[1]

    avg = None
    blk = after("2026/27 Average Score", 14)
    for l in blk:
        m = re.search(r"=\s*([\d.]+)", l)
        if m:
            avg = float(m.group(1)); break

    pref, mode = [], None
    for i, l in enumerate(lines):
        if l.startswith("Preferred Subjects with the Highest Weighting"):
            for x in lines[i + 1:i + 24]:
                if x.startswith("Relevant Applied Learning") or x.startswith("Admission Score Calculation"):
                    break
                if x.startswith("There is no compulsory") or x.startswith("Preferred subject"):
                    continue
                if re.fullmatch(r"[A-Za-z0-9 ,:+()\-/&]+", x) and len(x) < 70:
                    pref.append(x)
            break

    # requirement block
    req = after("Entrance Requirements and Subject Weightings", 45)
    req_txt = " | ".join(req)
    rows[code] = {"mechanism": mech, "avg": avg, "preferred": pref, "req": req_txt[:1500]}

json.dump(rows, open("work/2027/raw/polyu_pages_parsed.json", "w"), indent=1, ensure_ascii=False)
for c, v in rows.items():
    print(c, "| avg", v["avg"], "| mech:", v["mechanism"][:50], "| pref:", v["preferred"][:4])
