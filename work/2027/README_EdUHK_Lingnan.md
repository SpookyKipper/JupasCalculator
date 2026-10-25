# 2027-cycle extraction — EdUHK + LingnanU

Outputs: `EdUHK.json` (26 programmes), `LingnanU.json` (23 programmes) — bare JSON arrays
with the same 12-key record shape as `PolyU.json` / `HKBU.json` / `CUHK.json`.

The score-conversion table and provenance notes are in `meta/EdUHK.json` and `meta/LingnanU.json`
(`_conversion` + `_meta`), because a JSON array cannot carry top-level keys.

## Provenance / year labels

| Data | Source | Year |
|---|---|---|
| EdUHK 2026 intake scores (LQ, Median) + **2027** subject weightings | `raw/eduhk_scores_2026.pdf` = <https://www.eduhk.hk/acadprog/downloads/EdUHK_admission_scores_2026.pdf> (4 pp, dated 15 Oct 2026) | scores 2026, weights 2027 |
| Lingnan 2026 intake scores (Median, LQ, per-subject median/LQ) | `raw/lnu_scores_2026.pdf` = <https://www.ln.edu.hk/admissions/ug/f/upload/642/3418/2026_Admissions%20Scores.pdf> ("2026 JUPAS Admission Scores (Main Round)") | 2026 |
| Lingnan **2027** Category A weightings | `raw/lnu_admreq_2026-27.pdf` section 5 = <https://www.ln.edu.hk/admissions/ug/f/upload/629/3362/Admission%20Requirements_JUPAS%20(UG%20Website)%2026-27.pdf> | 2027 |
| 2027 min. entrance requirements + official programme names | JUPAS 2027 programme pages (`raw/jupas_reqs_2027.json`) | 2027 |

The EdUHK PDF carries the 2026 scores and a **2027-entry** weighting column side by side, so
`subject_weights_2027` is the 2027 column (starred entries = revised vs 2026).

## Conversion (both institutions: 7-point, NOT the 8.5 scale)

Category A: 5\*\*=7, 5\*=6, 5=5, 4=4, 3=3, 2=2, 1=1. EdUHK also converts Category B ApL
(Distinction II=4, Distinction/I=3, Attained=0) and Category C. Citizenship and Social
Development is excluded from the EdUHK score and not counted by Lingnan.

## Pipeline

1. `scripts/fetch.py` — tolerant fetcher (eduhk.hk needs `SSL_OP_LEGACY_SERVER_CONNECT`).
2. `scripts/jupas_reqs_scrap.py` — 49 JUPAS 2027 programme pages → `raw/jupas_reqs_2027.json`.
3. `scripts/eduhk_pdf_parse.py` — table parse of the EdUHK PDF → `raw/eduhk_pdf_parsed.json`.
4. `scripts/lnu_pdf_parse.py` — two-column word-position parse of the Lingnan scores PDF →
   `raw/lnu_pdf_parsed.json` (score rows bind to the nearest JS code; letter-by-letter
   "L o w e r" / "Q u a r t i l e" labels matched whitespace-stripped).
5. `scripts/lnu_weights_parse.py` — Lingnan weighting tables (pages 6–12) →
   `raw/lnu_weights_2027.json` (code carries across rows and page breaks).
6. `scripts/build.py` — merge, canonicalise subject names, emit both institution files.

Every emitted 2026 score was re-checked to appear verbatim in the source PDF text.

## Known gaps / caveats

- **No UQ anywhere**: EdUHK publishes Lower Quartile + Median only, Lingnan Median + Lower
  Quartile only → `scores_2026.uq` and `.mean` are `null` for all 49 records (EdUHK's
  "mean score of specific HKDSE subject" is a single-subject figure, not an overall mean).
- `confidence` is `official` for all 49: every number comes from the institution's own publication.
- **`Specified ApL subject(s)` is not a canonical subject name.** EdUHK weights a specific list of
  Applied Learning subjects; the key is kept as a placeholder (same convention as
  `Reference(2026)/EdUHK/EdUHK_2026_Data.json`). A closed-vocabulary check will flag it — it is a
  token, not a DSE subject.
- **`Combined Science`** is likewise a family token (three canonical variants exist); EdUHK weights
  Combined Science as a whole.
- Lingnan prints "Technology and Living"; mapped to canonical
  `Technology and Living (Food Science and Technology)` via `subjects.canonical.json` aliases —
  the Fashion, Clothing and Textiles strand is not identified separately in the source.
- **JS8012 / JS8702 2027 weight revisions**: EdUHK also prints references scores recomputed with the
  2027 weightings (JS8012 LQ 26.5 / median 27.5; JS8702 LQ 26.4 / median 26.6). Stored
  `scores_2026` are the actual 2026 figures (25.0/26.0 and 25.2/25.6).
- **Lingnan JS7305 LQ = 21.5 vs median 28.5** is printed that way in the source; reproduced as-is.
- EdUHK JS8507 (Higher Diploma in Early Childhood Education) is not a 332A programme: Chinese 2 +
  English 2 + any 3 electives at 2, expressed as `elect1.count=3` with `elect2` empty.
- `best_of_weights_2027` is non-empty only for JS8007 and JS8013, where EdUHK weights
  "the best one subject of" a group (list of lists; only the best subject of a group earns the weight).
