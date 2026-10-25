"""Build the 2027 unified dataset.

The 2027 refresh starts from the last 2026 dataset, shifts the year keys one
cycle (2025->2026, 2026->2027), then overlays the official 2027 weightings,
2026 intake admission scores and 2027 requirements extracted into work/2027/.
"""
import runpy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for script in ("scripts/utils/rebase_2027.py", "scripts/utils/apply_2027_overrides.py", "scripts/utils/apply_offers_2027.py", "scripts/utils/postprocess_2027.py"):
    print(f"==> {script}")
    runpy.run_path(str(ROOT / script), run_name="__main__")
