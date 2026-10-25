# CUHK + HKUST — 2027-cycle extraction notes

Outputs: `CUHK.json` (72 programmes), `HKUST.json` (34 programmes).
Scripts: `scripts/parse_cuhk_grades.py`, `scripts/build_cuhk.py`,
`scripts/parse_hkust_scores.py`, `scripts/build_hkust.py`,
`scripts/fetch_jupas_pages.py` (shared), `scripts/validate_my_outputs.py`.
Cached sources: `Reference(2027)/CUHK/`, `Reference(2027)/HKUST/`.

## Year labels (critical)

| Field | Source | Intake / cycle |
|---|---|---|
| `scores_2026` (CUHK) | *Admission Grades of JUPAS Applicants (2026 Entry)*, published Oct 2026 | **2026 intake** |
| `score_grades_2026` (CUHK) | same PDF — grades attained by the UQ / median / LQ admit | **2026 intake** |
| `scores_2026` (HKUST) | *2026 HKUST JUPAS Admissions Scores* | **2026 intake** |
| `formula_2027`, `subject_weights_2027`, `best_of_weights_2027` | CUHK 2027 score-calculator feed / HKUST *2027 JUPAS Admissions Requirements* PDF | **2027 entry** |
| `min_requirements_2027` | CUHK feed + HKUST PDF, both cross-checked against the JUPAS 2027 programme pages | **2027 entry** |

CUHK's `wp-content/uploads/data.json` feed is 2027-aware (it lists a programme with no 2026 intake,
`JS4858`, plus 2027 expected-score fields and 2027 requirements), but its own `uq/m/lq` fields are
**last year's** grades — for every programme they reproduce the older 2025-entry values
(e.g. JS4006: 24.5 / 24 / 23 vs the official 2026 PDF 26 / 25 / 24.5). All CUHK scores here
therefore come from the 2026 PDF, not from the feed.

## CUHK specifics

- Weighted totals in the PDF are on CUHK's 8.5 / 7 / 5.5 / 4 point scale (JS4501/JS4502 use 7/6/5…).
  They are already programme-weighted, so they are **not** comparable across programmes with
  different weightings.
- `score_grades_2026` keeps the PDF's per-percentile grades: core subjects + `electives` list
  (elective subjects are not named in the PDF, only their levels), `csd` shown as `A`
  (the PDF prints `TT` = Attained).
- Formula ids: plain `Best(5)` → `best5`; every formula with a compulsory subject or a
  "best of" group (e.g. `AENGL+Best(4)`, `Best(1,[ABIOL,ACHEM])+Best(4)`, medicine's
  6-subject rule) → `custom`, with the constraint spelled out in `formula_2027`.
- `JS4111` Theology and `JS4858` Global Communication are in the 2027 catalogue but have no
  2026 admission grades (no 2026 intake) → `scores_2026` null, confidence `partial`.

## HKUST specifics

- HKUST publishes **no upper quartile**. The 2026 sheet gives highest attainable, median and
  lower quartile only, so `scores_2026.uq` is null everywhere.
- `JS5118` (Biomedical and Health Sciences) has no formula in the 2027 requirements PDF — its
  row is blank (merged cell). Formula left empty, confidence `partial`. Its 2027 minimum
  requirements are complete (JUPAS page agrees: 332A33 + one of Bio/Chem/Phy/M1/M2).
- `JS5712` (Individualized Interdisciplinary Major) is **new for 2027** and is not in
  `data/processed/JUPAS_2027_Unified_Data.json` (33 HKUST codes) — included here, no 2026
  scores. HKUST count is therefore 34, not 33.
- `subject_weights_2027` records every multiplier > 1 as printed ("Physics x2" → Physics: 2).
  `best_of_weights_2027` is used only where HKUST weights *the best of* a group
  (`JS5811` best of Bio/Chem x1.5) or where a "better of … OR …" alternative formula gives
  one group x1.5 (`JS5312`, `JS5331`, `JS5332`, `JS5822` — those are `custom`).
- The engineering rows JS5240 / JS5250 / JS5260 share one merged formula cell in the PDF
  (Physics x2, ICT x1.5, Bio/Chem x1, M1/M2 x2), as do JS5212 and JS5240's wording.

## Cross-checks performed

- Every CUHK and HKUST 2027 minimum requirement was compared with the JUPAS 2027 programme
  page (`work/2027/scripts/jupas_pages_*.json`); core levels match for all 72 + 34 records.
  Differences only in how elective alternatives are grouped (JUPAS lists one row per
  alternative, the institution feed uses one row per slot).
- CUHK score totals and HKUST medians/LQs spot-checked against the PDFs' own text.
- `scripts/validate_my_outputs.py` checks key order, enum values, canonical subject names and
  numeric sanity; it reports 0 problems.
