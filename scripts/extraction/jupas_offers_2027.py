"""Fetch JUPAS 2027 programme pages and capture the 2026 application/offer
statistics + 2027 first-year intake. Resilient (retries, small thread pool)."""
import json, re, time, random
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from bs4 import BeautifulSoup

CODES = [r['JUPAS Catalogue No.'] for r in __import__('pandas').read_csv('data/raw/2027 JUPAS Program Overview.csv').to_dict('records')]
OUT = 'work/2027/offers_2027.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124 Safari/537.36'}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

def fetch(code):
    url = f'https://www.jupas.edu.hk/en/programme/{"" if False else ""}'
    # the overview CSV holds the exact path
    return None

# load overview for URLs
import pandas as pd
ov = pd.read_csv('data/raw/2027 JUPAS Program Overview.csv')
urls = dict(zip(ov['JUPAS Catalogue No.'], ov['url']))

def one(code):
    last = None
    for attempt in range(4):
        try:
            u = 'https://www.jupas.edu.hk' + urls[code]
            r = SESSION.get(u, timeout=25)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, 'html.parser')
            rows = []
            table_idx = 0
            for t in soup.find_all('table'):
                txt = ' '.join(t.get_text(' ', strip=True).split())
                if 'Band A' not in txt or 'Year' not in txt:
                    continue
                table_idx += 1
                typ = 'Application' if table_idx == 1 else 'Offer'
                for tr in t.find_all('tr'):
                    cells = [td.get_text(' ', strip=True) for td in tr.find_all('td')]
                    if len(cells) < 7: continue
                    try:
                        year = int(cells[0])
                    except Exception:
                        continue
                    vals = []
                    for c in cells[1:7]:
                        try: vals.append(int(re.sub(r'[^0-9]', '', c) or 0))
                        except Exception: vals.append(0)
                    rows.append({'Year': year, 'Band A': vals[0], 'Band B': vals[1], 'Band C': vals[2],
                                 'Band D': vals[3], 'Band E': vals[4], 'Total': vals[5], 'Type': typ})
            quota = None
            d = soup.find('div', class_='programInfo_block programInfo_block-firstyear')
            if d:
                m = re.search(r'First Year Intake(?:\s*\([^)]*\))?\s*:?\s*(\d+)', d.get_text(' ', strip=True), re.I)
                if m and int(m.group(1)) <= 3000: quota = int(m.group(1))
            return code, {'offer_statistics': rows, 'quota': quota, 'url': 'https://www.jupas.edu.hk' + urls[code]}
        except Exception as e:
            last = str(e)
            time.sleep(1.5 * (attempt + 1) + random.random())
    return code, {'error': last}

out = {}
with ThreadPoolExecutor(max_workers=4) as ex:
    futs = {ex.submit(one, c): c for c in CODES}
    for i, f in enumerate(as_completed(futs), 1):
        code, res = f.result()
        out[code] = res
        if i % 20 == 0:
            print(f'{i}/{len(CODES)}', flush=True)
json.dump(out, open(OUT, 'w'), ensure_ascii=False, indent=1)
ok = sum(1 for v in out.values() if 'error' not in v)
print('done', ok, '/', len(CODES), '->', OUT)
