"""Fetch the 2027 JUPAS programme pages and record the published first-year
tuition fee. The 2027 pages show the 2027-28 fee (HK$49,500 for UGC-funded
programmes), replacing the stale 2026 figure carried in the old dataset.
"""
import json, re, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
from bs4 import BeautifulSoup

OUT = 'work/2027/tuition_2027.json'
ov = pd.read_csv('data/raw/2027 JUPAS Program Overview.csv')
urls = dict(zip(ov['JUPAS Catalogue No.'], ov['url']))
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}

def one(code):
    last = None
    for attempt in range(4):
        try:
            r = requests.get('https://www.jupas.edu.hk' + urls[code], headers=headers, timeout=25)
            r.raise_for_status()
            text = ' '.join(BeautifulSoup(r.text, 'html.parser').get_text(' ', strip=True).split())
            m = re.search(r'First Year Tuition Fee\s*(?:Updated\s*)?(HK\$\s*[\d,]+)', text)
            fee = m.group(1).replace(' ', '') if m else None
            if fee:
                fee = re.sub(r'HK\$0*(\d)', r'HK$\1', fee)
            return code, fee
        except Exception as e:
            last = str(e)
            time.sleep(1.2 * (attempt + 1) + random.random())
    return code, None

out = {}
with ThreadPoolExecutor(max_workers=4) as ex:
    futs = {ex.submit(one, c): c for c in urls}
    for i, f in enumerate(as_completed(futs), 1):
        code, fee = f.result()
        out[code] = fee
        if i % 40 == 0:
            print(f'{i}/{len(urls)}', flush=True)
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
print('fees found', sum(1 for v in out.values() if v), '/', len(out), '->', OUT)
