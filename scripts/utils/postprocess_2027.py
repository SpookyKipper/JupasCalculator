"""Final, idempotent clean-up pass for the 2027 dataset.

- fills missing core requirements from the 2026 record (CityU/CUHK grouped PDF
  cells leave some rows blank);
- normalises legacy bare-list best-of pools into the runtime object shape;
- drops inherited 2026 score_basis labels that no longer describe the data;
- guarantees every array field the frontend iterates exists;
- refreshes the runtime version hash.
"""
import json, hashlib, re

P = 'data/processed/JUPAS_2027_Unified_Data.json'
OLD = 'data/processed/JUPAS_2026_Unified_Data.json'

d = json.load(open(P, encoding='utf-8'))
old = {x['jupas_code']: x for x in json.load(open(OLD, encoding='utf-8'))}

CANON = ['Biology','Chemistry','Physics','Economics','Geography','History',
 'Chinese History','Chinese Literature','Literature in English',
 'Information and Communication Technology',
 'Business, Accounting and Financial Studies','Design and Applied Technology',
 'Health Management and Social Care','Tourism and Hospitality Studies',
 'Visual Arts','Music','Physical Education','Ethics and Religious Studies',
 'Integrated Science','Mathematics Extended Part (Module 1)',
 'Mathematics Extended Part (Module 2)']

for x in d:
    # 1) requirements fallback
    mr = x.get('min_requirements_2027') or {}
    om = (old.get(x['jupas_code'], {}) or {}).get('min_requirements_2026') or {}
    for k in ('chi','eng','math','csd'):
        if not mr.get(k):
            mr[k] = om.get(k)
    for k in ('elect1','elect2'):
        cur = mr.get(k)
        if not isinstance(cur, dict) or not cur.get('grade'):
            mr[k] = om.get(k)
    if x.get('institution') == 'CityUHK':
        for k in ('elect1','elect2'):
            pool = mr.get(k)
            if not isinstance(pool, dict):
                continue
            note = pool.get('note') or ''
            if 'from' in note.lower():
                subs = [s for s in CANON if re.search(re.escape(s), note, re.I)]
                if subs:
                    pool['subjects'] = subs
                    pool['count'] = 1
    x['min_requirements_2027'] = mr

    # 2) best-of pool shape
    pools = []
    for pool in x.get('best_of_weights_2027') or []:
        if isinstance(pool, list):
            subs = [s for s in pool if s != 'Specified ApL subject(s)']
            w = max([x.get('subject_weights_2027', {}).get(s, 1.0) for s in subs] or [1.0])
            pools.append({'count': 1, 'subjects': subs, 'weight': w})
            for s in subs:
                x.get('subject_weights_2027', {}).pop(s, None)
        elif isinstance(pool, dict) and isinstance(pool.get('subjects'), list):
            pools.append(pool)
    x['best_of_weights_2027'] = pools
    x.setdefault('subject_weights_2027', {})
    x.setdefault('scores_2026', {})

    # 3) inherited basis notes only apply to CityU's PDF-recalculated scores
    if x.get('score_basis') in ('cuhk_2027_recalculated','cuhk_2027_simulated',
                                'eduhk_2027_recalculated','hkbu_2027_simulated'):
        x['score_basis'] = None

json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
payload = open(P, 'rb').read()
h = hashlib.sha1(payload).hexdigest()[:12]
open('data/processed/JUPAS_2027_Unified_Data.version', 'w').write(h)
print(f'postprocessed {len(d)} programmes; version {h}')

# ── Extra 2027 clean-up (idempotent) ────────────────────────────────────────
import os
d = json.load(open(P, encoding='utf-8'))
old = {x['jupas_code']: x for x in json.load(open(OLD, encoding='utf-8'))}
NEW_CODES = {'JS1063','JS1120','JS2030','JS2050','JS3997','JS5712','JS9210','JSSU75','JSSY03','JS6133','JS6365','JS4472','JS3923'}
SEVEN = {'EdUHK','LingnanU','HKBU','HKMU','SSSDP'}
for x in d:
    code = x['jupas_code']
    # 1) New-for-2027 programmes have no 2026 formula; mirror the 2027 one so the
    #    "previous cycle" reference panel is not blank.
    if not x.get('formula_2026'):
        x['formula_2026'] = x.get('formula_2027')
        x['formula_2026_id'] = x.get('formula_2027_id')
    # 2) Institution conversion scales (new-programme template defaults to 8.5).
    if x.get('institution') in SEVEN:
        x.setdefault('score_conversion_table', {})['category_a'] = {
            '5**':7.0,'5*':6.0,'5':5.0,'4':4.0,'3':3.0,'2':2.0,'1':1.0,'attained':0.0,'A':0.0}
    # 3) A few SSSDP requirement pools came through with a stray "2" token.
    for k in ('elect1','elect2'):
        pool = (x.get('min_requirements_2027') or {}).get(k)
        if isinstance(pool, dict) and isinstance(pool.get('subjects'), list):
            pool['subjects'] = [s for s in pool['subjects'] if s not in ('2',2)]
            if not pool['subjects']:
                pool['subjects'] = ['Any']
    # 4) New programmes cannot have a 2026 score; discard header-year artefacts.
    if code in NEW_CODES:
        sc = x.get('scores_2026') or {}
        for k in ('uq','median','lq','mean'):
            v = sc.get(k)
            if isinstance(v,(int,float)) and v > 200:
                sc[k] = None
        x['scores_2026'] = sc
    # 5) aliases / unscoreable placeholders
    w = x.get('subject_weights_2027') or {}
    if 'Technology and Living' in w:
        w['Technology and Living (Food Science and Technology)'] = w.pop('Technology and Living')
    w.pop('Specified ApL subject(s)', None)
    if 'Combined Science' in w:
        cv = w.pop('Combined Science')
        for _s in ('Combined Science: Biology + Chemistry','Combined Science: Biology + Physics','Combined Science: Physics + Chemistry'):
            w[_s] = cv
    # 6) New CityU code with a missing core requirement: use the CityU baseline.
    if code in ('JS1063','JS1120') and not (x.get('min_requirements_2027') or {}).get('chi'):
        x['min_requirements_2027']['chi'] = '3'

json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# Recompute 2026 -> 2027 weighting changes from the previous cycle's stored 2026
# weights and the newly overlaid 2027 weights. This keeps the "what changed"
# panel truthful instead of carrying the 2025->2026 diff forward.
_reg = json.load(open('data/raw/subjects.canonical.json', encoding='utf-8'))
_ok_subjects = set(_reg['core'] + _reg['category_a'] + [_reg['math_extended']['module_1'], _reg['math_extended']['module_2'], _reg['math_extended']['combined']])
for x in d:
    prev = (old.get(x['jupas_code'], {}) or {}).get('subject_weights_2026') or {}
    cur = x.get('subject_weights_2027') or {}
    items = []
    pool_subjects = set()
    for pool in x.get('best_of_weights_2027') or []:
        pool_subjects.update(pool.get('subjects') or [])
    for subj in sorted(set(prev) | set(cur)):
        if subj not in _ok_subjects or subj in pool_subjects:
            continue  # Category C naming churn / a subject moved into a best-of pool
        a, b = prev.get(subj), cur.get(subj)
        if a is None and b is None:
            continue
        if b is None:
            b = 1.0
        if a is None:
            a = 1.0
        if abs(float(a) - float(b)) > 1e-9:
            items.append({'type':'weighting','subject':subj,'from':float(a),'to':float(b)})
    x['year_changes'] = ({'weighting_changed': True, 'formula_changed': False,
                          'items': items} if items else None)

json.dump(d, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
h = hashlib.sha1(open(P, 'rb').read()).hexdigest()[:12]
open('data/processed/JUPAS_2027_Unified_Data.version', 'w').write(h)
print('extended clean-up done; version', h)
