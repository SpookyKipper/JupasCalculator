import pdfplumber, re, json, collections, importlib.util

PDF='Reference(2027)/CityU/CityU_2027_Requirements_AdmissionScores.pdf'
OUT='work/2027/CityU.json'

spec=importlib.util.spec_from_file_location('u','scripts/utils/unify_2026_data.py')
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
norm=u.normalize_subject

BANDS={
 'eng':(140,186),'chin':(186,220),'math':(220,270),'csd':(270,320),
 'e1':(318,428),'e2':(428,535),'formula':(535,610),'weights':(610,716),
 'median':(725,772),'lq':(772,820),
}

def band_words(words, lo, hi):
    return [w for w in words if lo <= (w['x0']+w['x1'])/2 < hi]

def text_of(ws):
    return ' '.join(w['text'] for w in sorted(ws, key=lambda w:(round(w['top']),w['x0'])))

SUBJECTS = [
 'Business, Accounting and Financial Studies','Design and Applied Technology',
 'Information and Communication Technology','Technology and Living','Health Management and Social Care',
 'Tourism and Hospitality Studies','Ethics and Religious Studies','Combined Science',
 'Integrated Science','Chinese Literature','Literature in English','Chinese History',
 'Physical Education','Visual Arts','Mathematics (Compulsory Part)','English Language',
 'Chinese Language','Mathematics','English','Chinese','Biology','Chemistry','Physics',
 'Economics','Geography','History','Music','BAFS','DAT','ICT','M1/M2','M1','M2',
]

def split_subjects(token):
    token = re.sub(r'\s+',' ',token).strip(' .,;:')
    if not token: return []
    # special compact forms
    if re.fullmatch(r'M1\s*/\s*M2', token, re.I):
        return ['Mathematics Extended Part (Module 1)','Mathematics Extended Part (Module 2)']
    found=[]; remaining=token
    # longest names first, case-insensitive; avoid matching inside already-removed spans
    for name in sorted(SUBJECTS, key=len, reverse=True):
        pat=re.compile(re.escape(name), re.I)
        for m in pat.finditer(remaining):
            found.append((m.start(), name))
    # de-overlap: prefer longest at each position
    found.sort(key=lambda x:(x[0],-len(x[1])))
    picked=[]; last_end=-1
    for pos,name in found:
        if pos < last_end: continue
        picked.append((pos,name)); last_end=pos+len(name)
    out=[]
    for _,name in picked:
        low=name.lower()
        if low in ('m1/m2',):
            out += ['Mathematics Extended Part (Module 1)','Mathematics Extended Part (Module 2)']
        elif low in ('m1',):
            out.append('Mathematics Extended Part (Module 1)')
        elif low in ('m2',):
            out.append('Mathematics Extended Part (Module 2)')
        elif low in ('english','eng'): out.append('English Language')
        elif low in ('chinese','chin'): out.append('Chinese Language')
        elif low in ('mathematics','math'): out.append('Mathematics (Compulsory Part)')
        elif low in ('bafs',): out.append('Business, Accounting and Financial Studies')
        elif low in ('dat',): out.append('Design and Applied Technology')
        elif low in ('ict',): out.append('Information and Communication Technology')
        else: out.append(norm(name))
    return list(dict.fromkeys(out))

def parse_weights(text):
    text=text.replace('\u2013','-').replace('•',' ')
    # split on "1.5:" style markers
    parts=re.split(r'(?:(?<=\s)|^)(\d+(?:\.\d+)?)\s*:\s*', text)
    out={}; pools=[]
    for i in range(1,len(parts)-1,2):
        w=float(parts[i]); body=parts[i+1]
        # stop at the next marker already split; remove trailing "1: other..."
        body=re.split(r'\s+\d+(?:\.\d+)?\s*:\s*',body)[0]
        # handle best of (...) separately
        for m in re.finditer(r'the best of\s*\(([^)]*)\)', body, re.I):
            pool=[]
            for s in re.split(r'\s*/\s*',m.group(1)):
                s=s.strip()
                if not s: continue
                if s.upper() in ('M1/M2','M1 OR M2','M1/M2'):
                    pool += ['Mathematics Extended Part (Module 1)','Mathematics Extended Part (Module 2)']
                elif 'math' in s.lower():
                    pool.append('Mathematics (Compulsory Part)')
                else:
                    pool.append(norm(s))
            # dedupe
            pool=list(dict.fromkeys(pool))
            pools.append({'count':1,'subjects':pool,'weight':w})
        body=re.sub(r'the best of\s*\([^)]*\)',' ',body,flags=re.I)
        for s in re.split(r'\s*/\s*',body):
            s=re.sub(r'\s+',' ',s).strip(' .')
            if not s: continue
            if s.lower().startswith('other') or s.lower() in ('others',): continue
            for sub in split_subjects(s): out[sub]=w
    return out,pools

def parse_formula(text):
    t=re.sub(r'\s+',' ',text).strip()
    cons=[]
    if re.search(r'3\s*core\s*\+\s*2\s*elective',t,re.I):
        cons.append({'type':'compulsory_subjects','subjects':['Chinese Language','English Language','Mathematics (Compulsory Part)'],'description':'3 Core + 2 Elective: Chinese, English and Mathematics are compulsory'})
    if re.search(r'include[^)]*English',t,re.I) and not any('English Language' in c.get('subjects',[]) for c in cons):
        cons.append({'type':'compulsory_subjects','subjects':['English Language'],'description':'Formula includes English Language'})
    if re.search(r'include[^)]*Mathematics',t,re.I) and not any('Mathematics (Compulsory Part)' in c.get('subjects',[]) for c in cons):
        cons.append({'type':'compulsory_subjects','subjects':['Mathematics (Compulsory Part)'],'description':'Formula includes Mathematics (Compulsory Part)'})
    return cons

def num(s):
    m=re.search(r'\d+(?:\.\d+)?',s or '')
    return float(m.group(0)) if m else None

rows=[]
with pdfplumber.open(PDF) as doc:
    for pi,page in enumerate(doc.pages):
        words=page.extract_words()
        # code positions
        codes=[w for w in words if re.fullmatch(r'JS\d+',w['text'])]
        codes=sorted(codes,key=lambda w:w['top'])
        for ci,cw in enumerate(codes):
            top=cw['top']
            nxt=codes[ci+1]['top'] if ci+1<len(codes) else 10**9
            blk=[w for w in words if top-1 <= w['top'] < min(nxt-1, 755) and w['top'] > 110]
            # block ends at page bottom; continuation handled separately
            rec={'jupas_code':cw['text'],'page':pi}
            for k,(lo,hi) in BANDS.items():
                rec[k]=text_of(band_words(blk,lo,hi))
            rec['name']=' '.join(w['text'] for w in sorted(band_words(blk,0,140),key=lambda w:(round(w['top']),w['x0'])))
            rows.append(rec)

# drop duplicate code rows (page breaks)
by={}
for r in rows:
    if r['jupas_code'] in by:
        # merge text from continuation into first
        for k in ['name','eng','chin','math','csd','e1','e2','formula','weights']:
            if r[k]: by[r['jupas_code']][k]=(by[r['jupas_code']][k]+' '+r[k]).strip()
        if not by[r['jupas_code']].get('median'): by[r['jupas_code']]['median']=r['median']
        if not by[r['jupas_code']].get('lq'): by[r['jupas_code']]['lq']=r['lq']
    else:
        by[r['jupas_code']]=r

out=[]
for code,r in sorted(by.items()):
    weights,pools=parse_weights(r['weights'])
    cons=parse_formula(r['formula'])
    out.append({
        'jupas_code':code,'institution':'CityUHK','name':re.sub(r'\s+',' ',r['name']).strip(),
        'formula_2027':re.sub(r'\s+',' ',r['formula']).strip(),
        'formula_2027_id':'best5','subject_weights_2027':weights,'best_of_weights_2027':pools,
        'calculation_constraints':cons,
        'min_requirements_2027':{
            'eng':re.sub(r'\D','',r['eng'])[:1] or None,'chin':re.sub(r'\D','',r['chin'])[:1] or None,
            'math':re.sub(r'\D','',r['math'])[:1] or None,'csd':'A' if 'Attained' in r['csd'] else None,
            'elect1':{'count':1,'subjects':['Any'],'grade':re.sub(r'\D','',r['e1'])[:1] or '3','note':r['e1']},
            'elect2':{'count':1,'subjects':['Any'],'grade':re.sub(r'\D','',r['e2'])[:1] or '3','note':r['e2']},
        },
        'scores_2026':{'median':num(r['median']),'lq':num(r['lq']),'uq':None,'mean':None},
        'source':'CityUHK JUPAS Admissions (2027 Entry) PDF',
    })
json.dump(out,open(OUT,'w'),ensure_ascii=False,indent=1)
print('wrote',OUT,len(out))
for x in out[:6]:
    print(x['jupas_code'],x['formula_2027'],x['scores_2026'],x['subject_weights_2027'],x['best_of_weights_2027'])
