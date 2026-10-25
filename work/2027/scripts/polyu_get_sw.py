import json, os, time, urllib.request

codes = json.load(open("work/2027/raw/polyu_codes.json"))
os.makedirs("work/2027/raw/polyu_sw_2027", exist_ok=True)
for c in codes:
    path = f"work/2027/raw/polyu_sw_2027/{c}.pdf"
    if os.path.exists(path) and os.path.getsize(path) > 20000:
        continue
    url = f"https://www.polyu.edu.hk/saso/docdrive/jupas/2027_{c}_SW.pdf"
    try:
        with urllib.request.urlopen(url, timeout=40) as r:
            data = r.read()
        open(path, "wb").write(data)
        print(c, len(data), data[:4])
    except Exception as e:
        print(c, "ERR", e)
    time.sleep(0.3)
