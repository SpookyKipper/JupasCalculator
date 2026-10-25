"""Create the 2027 dataset by re-basing the 2026 dataset one cycle.

This is a scaffold for the annual refresh: 2025->2026 and 2026->2027 keys.
The 2027 weightings and 2026 admission scores are then overlaid from official
2027 sources by apply_2027_overrides.py.
"""
import json, os, shutil

SRC = 'data/processed/JUPAS_2026_Unified_Data.json'
DST = 'data/processed/JUPAS_2027_Unified_Data.json'

KEY_MAP = {
    'formula_2025': 'formula_2026',
    'formula_2026': 'formula_2027',
    'formula_2025_id': 'formula_2026_id',
    'formula_2026_id': 'formula_2027_id',
    'subject_weights_2025': 'subject_weights_2026',
    'subject_weights_2026': 'subject_weights_2027',
    'best_of_weights_2025': 'best_of_weights_2026',
    'best_of_weights_2026': 'best_of_weights_2027',
    'subject_weights_2025_raw': 'subject_weights_2026_raw',
    'subject_weights_2026_raw': 'subject_weights_2027_raw',
    'subject_weights_2025_official': 'subject_weights_2026_official',
    'best_of_weights_2025_official': 'best_of_weights_2026_official',
    'subject_weights_2025_official_raw': 'subject_weights_2026_official_raw',
    'min_requirements_2026': 'min_requirements_2027',
    'scores_2025': 'scores_2026',
    'score_grades_2025': 'score_grades_2026',
}
BASIS_MAP = {
    'cityu_2026_recalculated': 'cityu_2027_recalculated',
    'cuhk_2026_recalculated': 'cuhk_2027_recalculated',
    'cuhk_2026_simulated': 'cuhk_2027_simulated',
    'eduhk_2026_recalculated': 'eduhk_2027_recalculated',
    'hkbu_2026_simulated': 'hkbu_2027_simulated',
}

def remap(rec):
    out = {}
    for k, v in rec.items():
        nk = KEY_MAP.get(k, k)
        if k == 'score_basis' and v in BASIS_MAP:
            v = BASIS_MAP[v]
        out[nk] = v
    # provenance defaults; overrides may replace these
    out.setdefault('scores_year', 2026)
    out.setdefault('weights_year', 2027)
    out['scores_status'] = 'carried_forward_2025'
    out['weights_status'] = 'carried_forward_2026'
    return out

with open(SRC, encoding='utf-8') as f:
    data = json.load(f)
data = [remap(r) for r in data]
with open(DST, 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print('wrote', DST, len(data))

# programme details: keep the descriptive payload, rename the file
src_det = 'data/processed/programme_details_2026.json'
dst_det = 'data/processed/programme_details_2027.json'
if os.path.exists(src_det):
    shutil.copyfile(src_det, dst_det)
    print('wrote', dst_det)
