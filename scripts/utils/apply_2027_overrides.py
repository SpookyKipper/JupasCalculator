import json, glob, os, re

BASE='data/processed/JUPAS_2027_Unified_Data.json'
OVER='work/2027'
OVERVIEW='data/raw/2027 JUPAS Program Overview.csv'

base={p['jupas_code']:p for p in json.load(open(BASE,encoding='utf-8'))}

# ---- CityU PDF patches for merged-cell rows ----
cityu_path=f'{OVER}/CityU.json'
if os.path.exists(cityu_path):
    cityu=json.load(open(cityu_path,encoding='utf-8'))
    by={x['jupas_code']:x for x in cityu}
    def patch(code, **kw): by[code].update(kw)
    sci_weights={'English Language':1.5,'Biology':1.5,'Chemistry':1.5,'Geography':1.5,
                 'Mathematics (Compulsory Part)':1.5,'Mathematics Extended Part (Module 1)':1.5,
                 'Mathematics Extended Part (Module 2)':1.5,'Physics':1.5,'English Language':1.25}
    sci_cons=[{'type':'compulsory_subjects','subjects':['Chinese Language','English Language','Mathematics (Compulsory Part)'],'description':'3 Core Subjects + 2 Elective Subjects (at least one elective in Biology, Chemistry or Physics)'}]
    for code in ('JS1050','JS1051'):
        patch(code, formula_2027='3 Core Subjects + 2 Elective Subjects (including at least one elective in Biology, Chemistry or Physics)',
              formula_2027_id='best5', subject_weights_2027=sci_weights, best_of_weights_2027=[], calculation_constraints=sci_cons)
    bio_weights={'English Language':1.5,'Biology':1.5,'Chemistry':1.5,'Mathematics (Compulsory Part)':1.25,
                 'Business, Accounting and Financial Studies':1.25,'Design and Applied Technology':1.25,
                 'Information and Communication Technology':1.25,'Mathematics Extended Part (Module 1)':1.25,
                 'Mathematics Extended Part (Module 2)':1.25,'Physics':1.25}
    bio_cons=[{'type':'compulsory_subjects','subjects':['Chinese Language','English Language','Mathematics (Compulsory Part)'],'description':'3 Core + 2 Elective: Chinese, English and Mathematics are compulsory'}]
    for code in ('JS1805','JS1806','JS1807'):
        patch(code, formula_2027='3 core + 2 elective subjects', formula_2027_id='best5',
              subject_weights_2027=bio_weights, best_of_weights_2027=[], calculation_constraints=bio_cons,
              min_requirements_2027={'eng':'3','chin':'3','math':'3','csd':'A',
                'elect1':{'count':1,'subjects':['Biology','Chemistry','Physics'],'grade':'3','note':'Level 3 in one elective subject from Biology / Chemistry / Physics'},
                'elect2':{'count':1,'subjects':['Any'],'grade':'3','note':'Level 3 in any elective subjects'}})
    # clean leftover page-footer bleed
    for x in cityu:
        x['formula_2027']=re.split(r'\s+JS\d{4}\s+and\s+JS\d{4}',x.get('formula_2027') or '')[0].strip()
        if x.get('formula_2027') in ('Physics)',): x['formula_2027']=''
    json.dump(cityu,open(cityu_path,'w'),ensure_ascii=False,indent=1)

FILES=['CityU','HKU','CUHK','HKUST','PolyU','HKBU','EdUHK','LingnanU','HKMU','SSSDP']
VALID_IDS={'best4','best5','best6'}
CONF_TO_STATUS={'official':'official','partial':'partial','estimated':'estimated'}

for name in FILES:
    path=f'{OVER}/{name}.json'
    if not os.path.exists(path): continue
    recs=json.load(open(path,encoding='utf-8'))
    inst_name='CityUHK' if name=='CityU' else ('LingnanU' if name=='LingnanU' else name)
    for r in recs:
        code=r['jupas_code']; p=base.get(code)
        if p is None:
            # start from a minimal record; detailed fields filled later
            p={'jupas_code':code,'name_en':r.get('name',''),'name_zh':None,'institution':inst_name,
               'faculty':None,'formula_2026':None,'formula_2026_id':None,'subject_weights_2026':{},
               'best_of_weights_2026':[],'min_requirements_2027':{},'calculation_constraints':[],
               'score_conversion_table':{'category_a':{'5**':8.5,'5*':7.0,'5':5.5,'4':4.0,'3':3.0,'2':2.0,'1':1.0,'attained':0.0,'A':0.0},
                                          'category_c':{'A':5.0,'B':4.0,'C':3.0,'D':2.0,'E':1.0}},
               'scores_2026':{},'score_grades_2026':None,'offer_statistics':[],'quota':None,
               'remarks':'','jupas_url':None,'short_description':None,'programme_websites':[],
               'tuition_fee_first_year':'','contacts_text':'','study_level':'','jupas_requirements':None,
               'non_academic':[],'apl_policy':'none','scores_year':2026,'weights_year':2027}
            base[code]=p
        # formula / weights
        if r.get('formula_2027'):
            p['formula_2027']=r['formula_2027']
        fid=r.get('formula_2027_id')
        if fid in VALID_IDS:
            p['formula_2027_id']=fid
        elif not p.get('formula_2027_id'):
            p['formula_2027_id']='best5'
        if 'subject_weights_2027' in r:
            p['subject_weights_2027']={k:v for k,v in (r.get('subject_weights_2027') or {}).items() if k and isinstance(v,(int,float))}
        if 'best_of_weights_2027' in r:
            p['best_of_weights_2027']=r.get('best_of_weights_2027') or []
        # constraints from override (CityU / any explicit)
        if r.get('calculation_constraints') is not None:
            p['calculation_constraints']=r['calculation_constraints']
        # requirements
        mr=r.get('min_requirements_2027')
        if isinstance(mr,dict) and mr:
            p['min_requirements_2027']=mr
        # scores
        sc=r.get('scores_2026')
        if isinstance(sc,dict):
            p['scores_2026']={k:sc.get(k) for k in ('uq','median','lq','mean','expected_score')}
        if 'score_grades_2026' in r:
            p['score_grades_2026']=r['score_grades_2026']
        p['data_sources']=r.get('sources') or ([r.get('source')] if r.get('source') else [])
        conf=r.get('confidence')
        if name in ('HKU','CityU') and not conf: conf='official'
        p['data_confidence']=conf or 'partial'
        p['scores_status']='official_2026' if sc and any(sc.get(k) is not None for k in ('median','lq','mean','uq')) else 'unavailable_2026'
        p['weights_status']='official_2027' if (r.get('subject_weights_2027') is not None or r.get('best_of_weights_2027')) else 'official_2027'

# ---- HKU weights: parse the API HTML table for 2027 ----
try:
    import importlib.util
    spec=importlib.util.spec_from_file_location('u','scripts/utils/unify_2026_data.py')
    u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
    hku=json.load(open(f'{OVER}/HKU.json',encoding='utf-8'))
    for r in hku:
        p=base.get(r['jupas_code'])
        if not p: continue
        w=r.get('subject_weights_2027') or {}
        # API text has 'Other Subjects' as a default weight — expand it
        if 'Other Subjects' in w:
            default=w.pop('Other Subjects')
            for s in ['English Language','Chinese Language','Mathematics (Compulsory Part)','Biology','Chemistry','Physics','Economics','Geography','History','Chinese History','Chinese Literature','Literature in English','Information and Communication Technology','Business, Accounting and Financial Studies','Design and Applied Technology','Visual Arts','Music','Physical Education','Integrated Science','Combined Science','Ethics and Religious Studies','Tourism and Hospitality Studies','Health Management and Social Care']:
                w.setdefault(s,default)
        # formula multipliers (English×2 etc.)
        w.update(u.parse_hku_formula_weights(r.get('formula_2027') or ''))
        # normalize known names
        w={u.normalize_subject(k):float(v) for k,v in w.items() if k and float(v)!=1.0}
        # expand combined-science token to the canonical variants
        if 'Combined Science' in w:
            cv=w.pop('Combined Science')
            for s in ['Combined Science: Biology + Chemistry','Combined Science: Biology + Physics','Combined Science: Physics + Chemistry']:
                w[s]=cv
        if 'Mathematics Extended Part (Module 1 or 2)' in w:
            cv=w.pop('Mathematics Extended Part (Module 1 or 2)')
            w['Mathematics Extended Part (Module 1)']=cv
            w['Mathematics Extended Part (Module 2)']=cv
        p['subject_weights_2027']=w
        p['weights_status']='official_2027'
        p['formula_2027']=r.get('formula_2027') or p.get('formula_2027')
        p['scores_2026']=r.get('scores_2026')
        p['data_sources']=r.get('sources') or [r.get('source','')]
        p['data_confidence']='official'
        p['scores_status']='official_2026'
except Exception as e:
    print('HKU post-process warning:',e)

# ---- HKUST: update the structured formula-step weights to 2027 ----
try:
    import importlib.util
    _spec=importlib.util.spec_from_file_location('_unify_helpers','scripts/utils/unify_2026_data.py')
    _uh=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_uh)
    _norm=_uh.normalize_subject

    hkust=json.load(open(f'{OVER}/HKUST.json',encoding='utf-8'))
    for r in hkust:
        p=base.get(r['jupas_code'])
        if not p: continue
        raw=r.get('subject_weights_2027') or {}
        # Normalise BOTH sides of the lookup. The JS-extract writes the Maths core as
        # "Mathematics Compulsory Part" while the 2027 overrides use the canonical
        # "Mathematics (Compulsory Part)"; a raw .get() missed it and silently demoted
        # the ×2 Maths core to ×1 on every HKUST programme.
        neww={_norm(k):v for k,v in raw.items() if k and isinstance(v,(int,float))}
        # 2027 best-of pools (e.g. JS5312's Chem/Econ/Phys/M1/M2 ×1.5) live in
        # best_of_weights_2027, NOT in the flat subject_weights map, so they must be
        # looked up separately — otherwise the pool multiplier falls back to ×1.
        pools=[bw for bw in (r.get('best_of_weights_2027') or []) if isinstance(bw,dict)]

        def w_for(sub):
            """Override weight for a subject, or None when 2027 says nothing about it."""
            return neww.get(_norm(sub), raw.get(sub))

        def pool_w_for(subs):
            """Override weight for a pooled subject group, or None if not a 2027 pool.

            Require the group to sit INSIDE the override pool (subset), so an
            unrelated weight group in the same step (e.g. the Bio/Chem/Phys ×2
            science group) isn't handed a neighbouring pool's multiplier.
            """
            keys={_norm(s) for s in (subs or [])}
            if not keys: return None
            for bw in pools:
                pool_keys={_norm(s) for s in (bw.get('subjects') or [])}
                if keys <= pool_keys:
                    return bw.get('weight')
            return None

        def patch_step(st):
            if st.get('type')=='required' and st.get('subject'):
                w=w_for(st['subject'])
                if w is not None: st['weight']=w
            if st.get('weights'):
                for grp in st['weights']:
                    pw=pool_w_for(grp.get('subjects'))
                    if pw is not None:
                        grp['weight']=pw
                    else:
                        vals=[w for w in (w_for(s) for s in (grp.get('subjects') or [])) if w is not None]
                        if vals: grp['weight']=max(vals)

        steps=p.get('hkust_formula_steps')
        if isinstance(steps,list):
            for st in steps:
                patch_step(st)
                if st.get('type')=='better_of':
                    for opt in st.get('options',[]):
                        for sub in opt: patch_step(sub)
        p['subject_weights_2027']=raw
        p['weights_status']='official_2027'
except Exception as e:
    print('HKUST post-process warning:',e)

# ---- add new 2027 programmes and drop removed ----
import pandas as pd
ov=pd.read_csv(OVERVIEW)
ovcodes=set(ov['JUPAS Catalogue No.'])
for code in list(base):
    if code not in ovcodes:
        print('drop removed',code); del base[code]
for _,row in ov.iterrows():
    code=row['JUPAS Catalogue No.']
    if code in base: continue
    inst=row['Institution / Scheme']
    inst={'CityUHK':'CityUHK'}.get(inst,inst)
    conv={'5**':8.5,'5*':7.0,'5':5.5,'4':4.0,'3':3.0,'2':2.0,'1':1.0,'attained':0.0,'A':0.0}
    if inst in ('EdUHK','LingnanU','HKBU','HKMU','SSSDP'):
        conv={'5**':7.0,'5*':6.0,'5':5.0,'4':4.0,'3':3.0,'2':2.0,'1':1.0,'attained':0.0,'A':0.0}
    base[code]={'jupas_code':code,'name_en':row['Programme Full Title'],'name_zh':row['chinese_name'],
        'institution':inst,'faculty':None,'formula_2026':None,'formula_2026_id':None,'formula_2027':'Best 5 Subjects',
        'formula_2027_id':'best5','subject_weights_2026':{},'subject_weights_2027':{},'best_of_weights_2026':[],
        'best_of_weights_2027':[],'min_requirements_2027':{'chi':'3','eng':'3','math':'2','csd':'A',
          'elect1':{'count':1,'subjects':['Any'],'grade':'2'},'elect2':{'count':1,'subjects':['Any'],'grade':'2'}},
        'calculation_constraints':[],'score_conversion_table':{'category_a':conv,'category_c':{'A':5.0,'B':4.0,'C':3.0,'D':2.0,'E':1.0}},
        'scores_2026':{'uq':None,'median':None,'lq':None,'mean':None,'expected_score':None},'score_grades_2026':None,
        'offer_statistics':[],'quota':None,'remarks':'','jupas_url':None,'short_description':None,'programme_websites':[],
        'tuition_fee_first_year':'','contacts_text':'','study_level':'','jupas_requirements':None,'non_academic':[],
        'apl_policy':'none','scores_year':2026,'weights_year':2027,'scores_status':'unavailable_2026',
        'weights_status':'unavailable_2027','data_confidence':'estimated'}

out=list(base.values())
out.sort(key=lambda p:(p.get('institution',''),p['jupas_code']))
json.dump(out,open(BASE,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('merged',len(out),'programmes')
# coverage
from collections import Counter
print(Counter((p.get('institution'),p.get('scores_status')) for p in out))
print('score coverage',sum(1 for p in out if p.get('scores_status')=='official_2026'),'/',len(out))
print('weight coverage',sum(1 for p in out if p.get('weights_status')=='official_2027'),'/',len(out))
