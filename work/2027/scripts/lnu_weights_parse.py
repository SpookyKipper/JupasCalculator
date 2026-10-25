"""Parse Lingnan "JUPAS Admissions (2027 Entry)" PDF section 5 for 2027 Category A weightings.

PDF: work/2027/raw/lnu_admreq_2026-27.pdf (pages 6-12 = section 5)
Output: work/2027/raw/lnu_weights_2027.json  {code: {subject(original text): weight}}

Table shape: JUPAS Code | Programme Title | HKDSE Subjects | Subject Weight
Continuation rows repeat neither code nor title, so the current code carries
across rows and pages.  Within a row the weight is the last pure number and the
subject is the cell just before it.
"""
import json
import os
import re

import pdfplumber

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PDF = os.path.join(ROOT, "work", "2027", "raw", "lnu_admreq_2026-27.pdf")
OUT = os.path.join(ROOT, "work", "2027", "raw", "lnu_weights_2027.json")

CODE_RE = re.compile(r"^JS7\d{3}$")
NUM_RE = re.compile(r"^\d+(?:\.\d+)?$")
W_RE = re.compile(r"^(.+?)\s+(\d+(?:\.\d+)?)$")


def clean(s):
    return re.sub(r"\s+", " ", (s or "")).strip()


def main():
    weights = {}
    current = None
    with pdfplumber.open(PDF) as pdf:
        for pno in range(5, 12):  # pages 6-12
            for table in pdf.pages[pno].extract_tables():
                for row in table:
                    cells = [clean(c) for c in row]
                    if not any(cells):
                        continue
                    code = next((c for c in cells if CODE_RE.match(c)), None)
                    if code:
                        current = code
                        weights.setdefault(current, {})
                    if current is None:
                        continue
                    # last pure-number cell = weight, cell before it = subject
                    num_idx = [i for i, c in enumerate(cells) if c and NUM_RE.match(c)]
                    if num_idx:
                        i = num_idx[-1]
                        w = float(cells[i])
                        subj = next((cells[j] for j in range(i - 1, -1, -1) if cells[j] and not CODE_RE.match(cells[j])), None)
                        if subj and not NUM_RE.match(subj):
                            weights[current][subj] = w
                            continue
                    joined = " ".join(c for c in cells if c and not CODE_RE.match(c))
                    m = W_RE.match(joined)
                    if m:
                        weights[current][clean(m.group(1))] = float(m.group(2))
    json.dump(weights, open(OUT, "w"), ensure_ascii=False, indent=1)
    print("programmes:", len(weights), "counts:", {k: len(v) for k, v in weights.items()})
    for k, v in weights.items():
        print(k, v)


if __name__ == "__main__":
    main()
