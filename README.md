# JUPASCal 2027 · unofficial fork of JUPASCal 2026

An **unofficial 2027 fork** of the original [JUPASCal 2026 project](https://github.com/JUPASCal/JUPASCal.github.io),
for Hong Kong DSE students. The original 2026 project is released under the
**MIT License** and is available on [GitHub](https://github.com/JUPASCal/JUPASCal.github.io)
and at <https://jupascal.com/>. This 2027 fork is **not currently published as an
open-source repository** and has no public GitHub repository. Enter your HKDSE grades, build your A1–B6 programme list, and the tool
estimates your admission score for every JUPAS programme (400+ across 10
institutions) and compares it against historical admission data — a fast **DSE
score calculator** that works out each programme's own weighting for you.

🔗 **Original 2026 project:** [GitHub](https://github.com/JUPASCal/JUPASCal.github.io) (MIT License) · [jupascal.com](https://jupascal.com/) — this working copy is the 2027 data refresh of that MIT-licensed app. Remove/change the canonical URL and branding before publishing your own deployment.

> [!IMPORTANT]
> **This is an unofficial, educational tool — not affiliated with JUPAS or any
> university.** The 2027 weightings, entrance requirements, 2026 intake scores and
> admission statistics were gathered with **AI assistance** and manual spot-checks.
> **Accuracy is not guaranteed**; the data may be incomplete, out of date or wrong.
> Always verify against official JUPAS and institution publications before using it
> for any decision. Scores are *estimates* based on published formulas and past
> admission statistics; they are not predictions or guarantees of admission.
> Always confirm details with the official JUPAS and institution sources. Use it
> to get a rough sense of where you stand, nothing more.

## What it does

- **Score estimation** — applies each institution's own weighting/formula
  (Best-5, Best-6, subject multipliers, bonus subjects, M1/M2 handling, …) to
  your grades.
- **Eligibility checks** — verifies minimum and elective-subject requirements
  per programme.
- **Portfolio analysis** — an advisor-style read of your Band-A choices: per-slot
  risk, and "safer options in the same direction" suggestions.
- **Shareable plans** — your grades + choices encode into the URL (no account, no
  server), so a plan can be shared or handed to a teacher.
- **Bilingual** — English / 繁體中文.

Everything runs **client-side** — there is no backend. Your grades never leave
your browser except in a share link you choose to create.

## Tech stack

React 19 + TypeScript + Vanilla CSS, built with Vite. Deployed to GitHub Pages
via GitHub Actions on every push to `main`. Score computation runs in a Web
Worker to keep grade entry responsive.

## Local development

Requires Node.js 20+.

```bash
npm install
npm run dev      # starts Vite on http://localhost:5174
npm run build    # type-check + production build into dist/
```

Validation harnesses for the calculation/analysis logic:

```bash
npm run audit              # eligibility
npm run audit:analysis     # portfolio-analysis fuzz
npm run audit:suggestions  # safer-option suggestions
npm run audit:selection    # non-academic requirements
npm run audit:apl          # Applied Learning (Category B) model consistency
```

## Data pipeline

The app ships a single processed dataset
(`data/processed/JUPAS_2027_Unified_Data.json`). It is regenerated from
per-institution 2027 admissions publications, the official JUPAS 2027 catalogue
and the 2026 intake score releases. The 2027 refresh is a *re-base* of the
previous unified dataset plus an overlay of the new cycle's data:

- `work/2027/<Institution>.json` — official 2027 weightings / requirements and
  2026 intake scores, one file per institution (sources recorded in each record).
- `scripts/utils/rebase_2027.py` — shifts the 2026 dataset's year keys one cycle.
- `scripts/utils/apply_2027_overrides.py` — overlays the official 2027 data,
  adds new programmes and drops retired ones.
- `scripts/utils/apply_offers_2027.py` — overlays the 2026 application/offer
  bands and 2027 first-year intake scraped from JUPAS.
- `scripts/utils/postprocess_2027.py` — final schema/alias clean-up, year-change
  diff and version hash.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium     # for the Playwright-based scrapers
python scripts/utils/unify_2027_data.py
python scripts/utils/validate_unified_2027.py
```

The programme count is **not** hardcoded — it's derived at build time from the
dataset length, and new JUPAS-listed programmes are auto-included by the
unification step.

## Project structure

```
index.html, src/, vite.config.ts   the React app (repo root)
data/processed/                    the runtime dataset the app fetches
data/raw/                          source files + subject vocabulary
scripts/extraction/                per-institution scrapers
scripts/utils/                     unification + validation
scripts/*.mjs                      JS audit harnesses (npm run audit*)
docs/manuals/                      architecture & calculation notes
.github/workflows/deploy.yml       build + deploy to GitHub Pages
```

## Data sources & attribution

The admission data is compiled from **publicly available** JUPAS and university
sources (programme requirements, weightings, and past admission statistics). That
data belongs to its respective owners and is **not** covered by this project's
license — it's bundled here only to make the calculator usable. If you reuse this
project, you are responsible for your own use of that data.

## License & attribution

The **original JUPASCal 2026 project** is released under the **[MIT License](https://github.com/JUPASCal/JUPASCal.github.io/blob/main/LICENSE)**.
That licence applies to the original project, not to this unpublished 2027 fork.
No `LICENSE` file is included in this working copy and no licence is granted for
this 2027 fork.

A couple of notes:

- The bundled admission data is third-party (see *Data sources & attribution*
  above) and is not yours to relicense — use it responsibly.
- "JUPAS Cal" and **jupascal.com** refer to the original project. This 2027 fork
  is unofficial; please don't run it in a way that impersonates the official site
  or implies its endorsement.

## Disclaimer

JUPAS Cal is provided "as is", without warranty of any kind. The estimates may be
incomplete or wrong. The authors are not responsible for any decision made based
on this tool. Always rely on official JUPAS and institutional information for
real admission decisions.
