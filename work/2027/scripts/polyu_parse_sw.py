"""Parse PolyU 2027/28 subject-weighting PDFs -> canonical weights."""
import json, re, glob, os
import pdfplumber

MAP = {
    "Biology": "Biology",
    "Business, Accounting and Financial Studies": "Business, Accounting and Financial Studies",
    "Business, Accounting and Financial Studies (Accounting)": "Business, Accounting and Financial Studies",
    "Business, Accounting and Financial Studies (Business Management)": "Business, Accounting and Financial Studies",
    "Chemistry": "Chemistry",
    "Chinese History": "Chinese History",
    "Chinese Language": "Chinese Language",
    "Chinese Literature": "Chinese Literature",
    "Combined Science: Biology + Chemistry": "Combined Science: Biology + Chemistry",
    "Combined Science: Biology + Physics": "Combined Science: Biology + Physics",
    "Combined Science: Physics + Chemistry": "Combined Science: Physics + Chemistry",
    "Design and Applied Technology": "Design and Applied Technology",
    "Economics": "Economics",
    "English Language": "English Language",
    "Ethics and Religious Studies": "Ethics and Religious Studies",
    "Geography": "Geography",
    "Health Management and Social Care": "Health Management and Social Care",
    "History": "History",
    "Information and Communication Technology": "Information and Communication Technology",
    "Integrated Science": "Integrated Science",
    "Literature in English": "Literature in English",
    "Mathematics": "Mathematics (Compulsory Part)",
    "Mathematics (Extended part - Algebra and Calculus)": "Mathematics Extended Part (Module 2)",
    "Mathematics (Extended part - Calculus and Statistics)": "Mathematics Extended Part (Module 1)",
    "Music": "Music",
    "Physical Education": "Physical Education",
    "Physics": "Physics",
    "Technology and Living (Fashion, Clothing and Textiles)": "Technology and Living (Fashion, Clothing and Textiles)",
    "Technology and Living (Food Science and Technology)": "Technology and Living (Food Science and Technology)",
    "Tourism and Hospitality Studies": "Tourism and Hospitality Studies",
    "Visual Arts": "Visual Arts",
    # Category C
    "Adv Dip of French Lang Studies/Dip of French Lang Studies": "French: Advanced Diploma of French Language Studies / Diploma of French Language Studies",
    "Diploma of Spanish as a Foreign Language": "Spanish: Diploma of Spanish as a Foreign Language",
    "French": "French: Advanced Diploma of French Language Studies / Diploma of French Language Studies",
    "French #": "French: Advanced Diploma of French Language Studies / Diploma of French Language Studies",
    "German": "German: Goethe-Certificate",
    "German #": "German: Goethe-Certificate",
    "Goethe-Certificate": "German: Goethe-Certificate",
    "Hindi #": None,  # legacy, not in canonical vocabulary
    "Japanese": "Japanese: Japanese-Language Proficiency Test",
    "Japanese #": "Japanese: Japanese-Language Proficiency Test",
    "Japanese-Language Proficiency Test": "Japanese: Japanese-Language Proficiency Test",
    "Spanish": "Spanish: Diploma of Spanish as a Foreign Language",
    "Spanish #": "Spanish: Diploma of Spanish as a Foreign Language",
    "Test of Proficiency in Korean II": "Korean: Test of Proficiency in Korean II",
    "Urdu #": "Urdu: Urdu (International)",
    "Urdu (International)": "Urdu: Urdu (International)",
}

out, unmapped = {}, set()
for path in sorted(glob.glob("work/2027/raw/polyu_sw_2027/JS*.pdf")):
    code = os.path.basename(path)[:-4]
    weights, title, section = {}, "", None
    with pdfplumber.open(path) as pdf:
        text = "\n".join((p.extract_text() or "") for p in pdf.pages)
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("Programme Title:"):
            title = line.split(":", 1)[1].strip()
        m = re.match(r"^(.*?)\s+(\d+)$", line)
        if not m:
            continue
        name, w = m.group(1).strip(), int(m.group(2))
        if name.lower().startswith(("subject name", "jupas code", "category", "programme title")):
            continue
        canon = MAP.get(name)
        if canon is None:
            if name not in MAP:
                unmapped.add(name)
            continue
        weights[canon] = float(w)
    out[code] = {"title": title, "weights": weights}

json.dump(out, open("work/2027/raw/polyu_sw_2027.json", "w"), indent=1, ensure_ascii=False)
print("files", len(out), "unmapped:", sorted(unmapped))
for c, v in out.items():
    ws = sorted(set(v["weights"].values()))
    print(c, len(v["weights"]), ws, "|", v["title"][:45])
