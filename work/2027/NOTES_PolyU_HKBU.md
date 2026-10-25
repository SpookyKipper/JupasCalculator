# PolyU + HKBU — 2027-cycle extraction notes

Extracted 25 Oct 2026 by the PolyU/HKBU subagent. Outputs: `work/2027/PolyU.json` (46),
`work/2027/HKBU.json` (23). Scripts in `work/2027/scripts/` (`parse_polyu_figures.py`,
`polyu_parse_sw.py`, `polyu_parse_pages.py`, `build_polyu.py`, `parse_hkbu_pdf.py`,
`hkbu_calc_scrape.py`, `build_hkbu.py`, `validate.py`); sources cached in `work/2027/raw/`.

## PolyU

Sources
- 2026-entry scores: `https://www.polyu.edu.hk/saso/docdrive/jupas/admission_figures.pdf`.
  That file bundles 2026 (pp.1–5), 2025 (pp.6–10) and 2024 (pp.11–13); only the 2026 section
  was parsed (parsing all pages silently mixes years).
- 2027/28 subject weightings: `https://www.polyu.edu.hk/saso/docdrive/jupas/2027_JS####_SW.pdf`.
  The older `.../aradm/jupas/...` path 404s; `saso/docdrive/jupas/` is the current location.
- Per-programme 2027 mechanism + "2026/27 Average Score":
  `https://www.polyu.edu.hk/study/ug/jupas/2027/js####`.

Score scale — important
PolyU scores are `Σ(subject points × subject weighting)` with weights **5 / 7 / 10**
(base 7, so an equal-weight programme multiplies every subject by 7) and points
5**=8.5, 5*=7, 5=5.5, 4=4, 3=3, 2=2, 1=1. Weights are stored **raw (5/7/10)**, matching the
existing unified dataset. Do not renormalise to /7 without rescaling `scores_2026` — the
published means (e.g. 254.8) are on the ×7 scale.

Field mapping
- `average` → `mean`, `Median` → `median`, `Lower Quartile` → `lq`. PolyU publishes no upper
  quartile, so `uq` is null everywhere.
- `subject_weights_2027` holds Category A + Category C only. Category B (ApL) weights were
  parsed from the same PDFs but are **not** included: the canonical Cat-B vocabulary covers
  only 45 of the 91 ApL names in the 2027 PDFs, so a partial map would silently zero the rest.
  The existing pipeline keeps PolyU ApL weights in
  `Reference(2026)/PolyU/polyu_apl_weights.json`.

Code change for 2027
- **JS3011 → JS3997.** JUPAS 2027 has no JS3011 (404) and PolyU's 2027 URL redirects to
  JS3997 "BSc (Hons) in Chemical Technology" (`2027_JS3997_SW.pdf`). The JS3997 page still
  prints the 2026/27 average for "BSc (Hons) Scheme in Biotechnology and Chemical Technology
  (JS3011)" = 226.9, which is what `scores_2026` carries. Confidence `partial` (restructured).
- JS3000: "Scores of admittees from previous cohorts are not available" → all scores null,
  confidence `partial` (weights are official).
- JS3240: 2027 mechanism heading is **Any Best 5 Subjects (+bonus)**, but its "2026/27 Average
  Score" caption still reads "Chinese & English Languages + Any Best 3 Subjects (+bonus)"
  (the 2026 mechanism, under which that figure was computed). The JSON follows the 2027
  heading; the 2026 number is therefore not strictly comparable.

2027 weight changes vs the 2026 weights in the unified dataset
- JS3000 English/Mathematics 7→10; JS3006 floor 5→7; JS3220 5→7 and sciences 7→10;
  JS3223 5→7; JS3290 Chinese 7→10; JS3310 English 10→7.

## HKBU

Sources
- 2027 requirements + 2027 weights: `https://admissions.hkbu.edu.hk/content/dam/ao-assets/document/news/JUPAS_GER_PER.pdf`
  ("... for JUPAS Admissions (2027 Entry)").
- 2026 scores: the "Admissions Scores and Score Calculation" calculator on
  `https://admissions.hkbu.edu.hk/ug/jupas_weighting`, programme + year 2026
  (endpoint `.../jupasscorecalculator.scorecalculatorprogramme.json?code=JS####`).

What HKBU publishes
- A numeric **weighted mean** only ("Study Programme's Mean", best 5 Cat A/B/C, weighted).
- Median and Lower Quartile as **grade profiles**, not scores → `scores_2026.median`/`lq` are
  null; the profiles live in `score_grades_2026` (canonical core names + `Elective 1..4`).
- All programmes use **Best 5** for 2027 (stated once in the 2027 PDF). Weights default to 1,
  so `subject_weights_2027` lists only boosted subjects.

Code changes for 2027
- **JS2060 (BA / Bachelor of Music) split into JS2030 (Music) and JS2050 (Creative
  Industries).** HKBU's calculator returns identical 2026 statistics for both (mean 20.75,
  same grade profiles); marked `partial` as inherited from the pre-split combined entry.

Requirements
- GER 332A33: CHI 3, ENG 3, CSD Attained, MATH 2, two electives at 3 (elective 1 Cat A
  excluding M1/M2).
- JS2410 additionally requires one elective from Biology/Chemistry; JS2420 requires Chemistry.
- JS2410/JS2420 carry `#` on Chinese Language: no alternative Chinese qualification is
  accepted. The level is still 3; the NCS exception is not encoded in `min_requirements_2027`.

## Validation

`work/2027/scripts/validate.py` checks the exact key set, `formula_2027_id` vocabulary,
canonical subject names (against `data/raw/subjects.canonical.json`), weights > 1,
`scores_2026` key set, `confidence` vocabulary, non-empty http sources and median ≥ LQ.
Both files pass.
