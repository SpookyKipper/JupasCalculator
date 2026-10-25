"""Overlay the 2027 JUPAS page statistics: 2026 application/offer bands and
2027 first-year intake, plus the canonical programme URL."""
import json, hashlib

P='data/processed/JUPAS_2027_Unified_Data.json'
O='work/2027/offers_2027.json'
d=json.load(open(P,encoding='utf-8'))
o=json.load(open(O,encoding='utf-8'))
n=0
for x in d:
    rec=o.get(x['jupas_code'])
    if not rec or rec.get('error'): continue
    rows=rec.get('offer_statistics') or []
    if rows:
        x['offer_statistics']=rows
    if rec.get('quota') is not None:
        x['quota']=rec['quota']
    if rec.get('url'):
        x['jupas_url']=rec['url']
    n+=1
json.dump(d,open(P,'w',encoding='utf-8'),ensure_ascii=False,indent=2)
h=hashlib.sha1(open(P,'rb').read()).hexdigest()[:12]
open('data/processed/JUPAS_2027_Unified_Data.version','w').write(h)
print('offers overlaid',n,'version',h)
