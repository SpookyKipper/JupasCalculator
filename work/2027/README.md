# 2027-cycle extraction — HKMU + SSSDP

Outputs: `HKMU.json` (28), `SSSDP.json` (59). Scripts in `scripts/`, sources cached in `raw/`.

## Provenance / year labels

| Data | Source | Intake year |
|---|---|---|
| HKMU (JS9xxx + JSSU) scores | HKMU *2026 JUPAS Admission Scores* PDF (`raw/Scores_JUPAS.pdf`, last modified 21 Sep 2026) | 2026 |
| HKMU subject weight multipliers | same PDF (weights applied to the 2026 scores) | 2026 |
| HSUHK (JSSH) | `admission.hsu.edu.hk/.../2026-JUPAS-Admission-Scores.pdf` — average, Best 5 | 2026 |
| TWC (JSST) | `twc.edu.hk/uploads/files/TWC_2026_JUPAS_admission_scores.pdf` — mean, Best 5 | 2026 |
| THEi (JSSV) | `thei.edu.hk/admission/sssdp/` — average of Eng+Chi+Math+CSD+1 elective | 2026 |
| SFU (JSSA) | SFU SSSDP Year-1 page, "2026-27 JUPAS Admission Score" table (image) — mean, Best 5 | 2026 |
| 2027 min. entrance requirements (all) | JUPAS 2027 programme pages (`raw/jupas_pages/`) | 2027 |

JUPAS's *Admissions Scores of The SSSDP Institutions* hub (page 3669) still publishes **2025 only**,
and `af_2026_JUPAS.pdf` / `af_2026_SSSDP.pdf` return 404 — hence the per-operator sources above.

## Pipeline

1. `fetch_jupas.py` — fetch + parse the 87 JUPAS 2027 programme pages (28 HKMU, 59 SSSDP) →
   `raw/jupas_parsed.json` (core/elective requirement rows, weighted-subject hints, names).
2. `build_hkmu.py` — word-position parse of the HKMU PDF (median/LQ/weights) merged with the
   2027 requirements → `HKMU.json`.
3. `build_sssdp.py` — HKMU JSSU rows from the same PDF + the operators' published 2026 averages →
   `SSSDP.json`.

Both `build_*.py` import `to_minreq()` from `build_hkmu.py`, so run `fetch_jupas.py` first.

## Known gaps

- `JS9210` (HKMU, 2027 catalogue) and `JSSU75` (HKMU SSSDP) are new: no 2026 intake → null scores, `partial`.
- `JS9775` (Robotics & Automation, in the 2026 scores PDF) is **not** in the 2027 catalogue
  (`/hkmu/JS9775/` → 404), so it is intentionally absent from `HKMU.json`.
- No official 2026 score found for HKCHC `JSSC02`, UOWCHK `JSSW01/02`, HKSYU `JSSY01/02/03`
  → null scores, `estimated`, with a `notes` field. JUPAS's own pages confirm SYU scores "best five".
- HKMU/HSUHK/TWC/THEi/SFU publish no 2027 weight table beyond the above, so
  `subject_weights_2027` is `{}` for most SSSDP records (official: no weighting).
- THEi gives DSE Physical Education ×2.0 for `JSSV09/13/14` (stated on the JUPAS 2027 pages).
