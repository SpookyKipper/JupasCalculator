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
    # 6) Give every record a source link (new programmes inherit their JUPAS page).
    if not x.get('data_sources') and x.get('jupas_url'):
        x['data_sources'] = [x['jupas_url']]
    # 7) New CityU code with a missing core requirement: use the CityU baseline.
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

# ── Curated 2027 corrections / final overlays ──────────────────────────────
d = {x['jupas_code']: x for x in json.load(open(P, encoding='utf-8'))}

# 8) Tuition from the 2027 JUPAS pages (the old dataset carried the 2026 fee).
import os
_tuition = 'work/2027/tuition_2027.json'
if os.path.exists(_tuition):
    for code, fee in json.load(open(_tuition, encoding='utf-8')).items():
        if code in d and fee:
            d[code]['tuition_fee_first_year'] = fee

# 9) Strip a duplicated JUPAS code from scraped names (JS1063/JS1120).
for code, x in d.items():
    for key in ('name_en', 'name_zh'):
        val = x.get(key)
        if isinstance(val, str) and val.startswith(code + ' '):
            val = val[len(code):].strip()
        if isinstance(val, str):
            val = re.sub(r'\s*#\s*(?:COLLEGE|SCHOOL|FACULTY)\s+OF\b.*$', '', val, flags=re.I).strip()
            x[key] = val

# 10) JS4472 Robotics (new for 2027) shipped as a bare overview placeholder.
#     Official JUPAS page: Math 4, Any 1 subject 3 + one of Bio/Chem/ICT/DAT/
#     Physics/M1/M2 3, tuition HK$49,500. 2027 weighting supplied by CUHK's
#     2027 programme information; kept at "partial" because the central
#     score-calculator JSON has not yet been refreshed for new 2027 programmes.
js4472 = d['JS4472']
js4472['name_en'] = 'Robotics'
js4472['name_zh'] = '機器人學'
js4472['formula_2027'] = 'Best 5 Subjects'
js4472['formula_2027_id'] = 'best5'
js4472['subject_weights_2027'] = {
    'Mathematics (Compulsory Part)': 1.75,
    'Physics': 1.75,
    'Biology': 1.25,
    'Chemistry': 1.25,
    'Design and Applied Technology': 1.25,
    'Information and Communication Technology': 1.25,
}
js4472['best_of_weights_2027'] = [{
    'count': 1,
    'subjects': ['Mathematics Extended Part (Module 1)', 'Mathematics Extended Part (Module 2)'],
    'weight': 1.75,
}]
js4472['min_requirements_2027'] = {
    'chi': '3', 'eng': '3', 'math': '4', 'csd': 'A',
    'elect1': {'count': 1, 'subjects': ['Any'], 'grade': '3', 'note': 'Any 1 subject at Level 3'},
    'elect2': {'count': 1,
               'subjects': ['Biology', 'Chemistry', 'Information and Communication Technology',
                            'Design and Applied Technology', 'Physics',
                            'Mathematics Extended Part (Module 1)', 'Mathematics Extended Part (Module 2)'],
               'grade': '3',
               'note': 'One of Biology / Chemistry / ICT / DAT / Physics / M1/M2 at Level 3'},
}
js4472['tuition_fee_first_year'] = 'HK$49,500'
js4472['quota'] = 20
js4472['scores_2026'] = {'uq': None, 'median': None, 'lq': None, 'mean': None, 'expected_score': None}
js4472['scores_status'] = 'unavailable_2026'
js4472['weights_status'] = 'partial_2027'
js4472['data_confidence'] = 'partial'
js4472['data_sources'] = [
    'https://www.jupas.edu.hk/en/programme/cuhk/JS4472/',
    'https://admission.cuhk.edu.hk/programme/rosen/',
]
js4472['year_changes'] = None

out = list(d.values())
json.dump(out, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
h = hashlib.sha1(open(P, 'rb').read()).hexdigest()[:12]
open('data/processed/JUPAS_2027_Unified_Data.version', 'w').write(h)
print('final corrections + tuition overlay done; version', h)

# 11) JS3923 Applied Biology with Biotechnology (new 2027 PolyU code) was
#     created from the overview baseline; use PolyU's official 2027 weighting PDF
#     and JUPAS entrance requirements.
d = {x['jupas_code']: x for x in json.load(open(P, encoding='utf-8'))}
if 'JS3923' in d:
    p = d['JS3923']
    p['formula_2027'] = 'Any Best 5 Subjects'
    p['formula_2027_id'] = 'best5'
    p['min_requirements_2027'] = {
        'chi': '3', 'eng': '3', 'math': '2', 'csd': 'A',
        'elect1': {'count': 1, 'subjects': ['Any'], 'grade': '3', 'note': ''},
        'elect2': {'count': 1, 'subjects': ['Any'], 'grade': '3', 'note': ''},
    }
    w = {
        'Biology': 10, 'Business, Accounting and Financial Studies': 5,
        'Business, Accounting and Financial Studies (Accounting)': 5,
        'Business, Accounting and Financial Studies (Business Management)': 5,
        'Chemistry': 7, 'Chinese History': 5, 'Chinese Language': 7,
        'Chinese Literature': 5,
        'Combined Science: Biology + Chemistry': 10,
        'Combined Science: Biology + Physics': 10,
        'Combined Science: Physics + Chemistry': 7,
        'Design and Applied Technology': 5, 'Economics': 5,
        'English Language': 10, 'Ethics and Religious Studies': 5,
        'Geography': 5, 'Health Management and Social Care': 5,
        'History': 5, 'Information and Communication Technology': 5,
        'Integrated Science': 7, 'Literature in English': 5,
        'Mathematics (Compulsory Part)': 7,
        'Mathematics Extended Part (Module 1)': 7,
        'Mathematics Extended Part (Module 2)': 7,
        'Music': 5, 'Physical Education': 5, 'Physics': 7,
        'Technology and Living (Fashion, Clothing and Textiles)': 5,
        'Technology and Living (Food Science and Technology)': 5,
        'Tourism and Hospitality Studies': 5, 'Visual Arts': 5,
    }
    # PolyU lists the BAFS strands separately; the app's canonical dropdown uses
    # the combined BAFS subject, so fold them into that one key.
    bafs = max(w.pop('Business, Accounting and Financial Studies (Accounting)', 5),
               w.pop('Business, Accounting and Financial Studies (Business Management)', 5))
    w['Business, Accounting and Financial Studies'] = bafs
    p['subject_weights_2027'] = w
    p['best_of_weights_2027'] = []
    p['weights_status'] = 'official_2027'
    p['data_confidence'] = 'partial'
    p['data_sources'] = [
        'https://www.jupas.edu.hk/en/programme/polyu/JS3923/',
        'https://www.polyu.edu.hk/saso/docdrive/jupas/2027_JS3923_SW.pdf',
    ]
    p['year_changes'] = None

out = list(d.values())
json.dump(out, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
h = hashlib.sha1(open(P, 'rb').read()).hexdigest()[:12]
open('data/processed/JUPAS_2027_Unified_Data.version', 'w').write(h)
print('JS3923 correction done; version', h)

# 12) JS6626's 2026 admission median (50) was published under HKU's 2026
#     "Best 6 Subjects" formula, but the rebased record inherited the older
#     best-5 id. Align the comparison formula with the benchmark.
d = {x['jupas_code']: x for x in json.load(open(P, encoding='utf-8'))}
if 'JS6626' in d:
    d['JS6626']['formula_2026'] = 'Best 6 Subjects'
    d['JS6626']['formula_2026_id'] = 'best6'
out = list(d.values())
json.dump(out, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
h = hashlib.sha1(open(P, 'rb').read()).hexdigest()[:12]
open('data/processed/JUPAS_2027_Unified_Data.version', 'w').write(h)
print('JS6626 formula correction done; version', h)
