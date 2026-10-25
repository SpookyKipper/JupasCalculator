import json, re, requests, pdfplumber
from bs4 import BeautifulSoup

API='https://admissions.hku.hk/api/hkdse/admission_standard'
PDF='Reference(2027)/HKU/HKU-JUPAS-Admissions-Information-2027.pdf'
OUT='work/2027/HKU.json'

def clean(x): return ' '.join((x or '').split())

def parse_weights(html):
    if not html: return {}
    soup=BeautifulSoup(html,'html.parser'); out={}
    for tr in soup.find_all('tr'):
        th=tr.find('th'); td=tr.find('td')
        if not th or not td: continue
        m=re.search(r'([\d.]+)',th.get_text())
        if not m: continue
        w=float(m.group(1))
        for sub in re.split(r'[,/]',td.get_text()):
            sub=clean(sub)
            if sub: out[sub]=w
    return out

def parse_min(soup):
    t=soup.find('table',class_=lambda c:c and 'section-Minimum-Level-Requirement' in c)
    if not t: return {}
    rows=t.find_all('tr'); out={}
    if len(rows)>=2:
        cells=rows[1].find_all('td')
        keys=['req_eng','req_chin','req_math','req_csd','req_e1','req_e2']
        for i,k in enumerate(keys):
            if i<len(cells): out[k]=clean(cells[i].get_text())
    return out

def parse_formula(soup):
    for t in soup.find_all('table',class_=lambda c:c and 'table-style-2' in c):
        for tr in t.find_all('tr'):
            th=tr.find('th'); td=tr.find('td')
            if th and td and 'HKDSE Scoring Formula' in th.get_text(): return clean(td.get_text())
    return ''

api={}
r=requests.get(API,timeout=60); r.raise_for_status()
for fac,progs in r.json()['data']['programme'].items():
    for name,p in progs.items():
        code=p.get('programme_code','')
        if not re.fullmatch(r'\d{4}',code or ''): continue
        soup=BeautifulSoup(p.get('accordionHTML','') or '','html.parser')
        api['JS'+code]={
            'name':p.get('programme_name',''),'faculty':fac,'degree_type':p.get('degree_type',''),
            'formula':parse_formula(soup),'weights':parse_weights(p.get('field_hkuad_dse_subject_w')),'weight_text':p.get('field_hkuad_dse_subject_w') or '',
            **parse_min(soup),
        }

pdf={}
with pdfplumber.open(PDF) as doc:
    for page in doc.pages:
        for t in page.extract_tables():
            if not t or max(len(x) for x in t)<12: continue
            for row in t:
                code=clean(row[0])
                if not re.fullmatch(r'\d{4}',code): continue
                pdf['JS'+code]={
                    'name':clean(row[1]),'formula_2027':clean(row[2]),
                    'req_eng':clean(row[3]),'req_chin':clean(row[4]),'req_math':clean(row[5]),
                    'req_csd':clean(row[6]),'req_e1':clean(row[7]),'req_e2':clean(row[8]),
                    'other':clean(row[9]),'formula_2026':clean(row[10]),
                    'uq':clean(row[11]),'median':clean(row[12]),'lq':clean(row[13]),
                }
print('api',len(api),'pdf',len(pdf))
out=[]
for code in sorted(set(api)|set(pdf)):
    a=api.get(code,{}); p=pdf.get(code,{})
    def num(x):
        try: return float(x)
        except: return None
    out.append({
        'jupas_code':code,'institution':'HKU','name':a.get('name') or p.get('name',''),
        'faculty':a.get('faculty',''),'degree_type':a.get('degree_type',''),
        'formula_2027':re.sub(r'^[a-z]\s+','',p.get('formula_2027') or a.get('formula','')),
        'subject_weights_2027':a.get('weights',{}),
        'subject_weight_text':a.get('weight_text',''),
        'min_requirements_2027':{k:(a.get(k) or p.get(k.replace('req_','req_')) or '') for k in ['req_eng','req_chin','req_math','req_csd','req_e1','req_e2']},
        'scores_2026':{'uq':num(p.get('uq')),'median':num(p.get('median')),'lq':num(p.get('lq'))},
        'formula_2026':p.get('formula_2026',''),
        'source':'HKU 2027 JUPAS Admissions PDF + admissions.hku.hk API',
    })
json.dump(out,open(OUT,'w'),ensure_ascii=False,indent=1)
print('wrote',OUT,len(out))
for x in out[:3]: print(x['jupas_code'],x['formula_2027'],x['subject_weights_2027'],x['scores_2026'])
