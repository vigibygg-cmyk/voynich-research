import os
from collections import defaultdict

CSV_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti\ZL3b-n_clean.csv"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_42_Folio_Selection.md"

ALREADY_MAPPED = ["f1v", "f2r", "f68r1", "f68r3", "f68v3", "f75v", "f104r", "f116r"]

def get_theme(folio_id):
    try:
        # Extract number from fX...
        num_str = ''.join([c for c in folio_id if c.isdigit()])
        if not num_str: return "Unknown"
        num = int(num_str)
        if 1 <= num <= 66: return "Botanika (Herbal)"
        if 67 <= num <= 73: return "Astrologija (Zodiac/Astro)"
        if 75 <= num <= 84: return "Balneologija (Nymphs/Baths)"
        if 85 <= num <= 86: return "Kosmologija (Foldouts)"
        if 87 <= num <= 102: return "Farmacija (Jars/Roots)"
        if 103 <= num <= 116: return "Receptai (Stars/Text)"
        return "Unknown"
    except:
        return "Unknown"

def select_folios():
    try:
        with open(CSV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error: {e}")
        return

    stats = defaultdict(lambda: {"bisections": 0, "labels": 0, "theme": "Unknown"})

    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            folio = parts[1]
            locus = parts[2].strip('"')
            clean_text = parts[-1]

            if folio in ALREADY_MAPPED: continue
            
            stats[folio]["theme"] = get_theme(folio)

            if "<>" in clean_text or "<->" in clean_text:
                stats[folio]["bisections"] += 1
            if "@L" in locus or "=L" in locus or "+L" in locus or "*L" in locus:
                stats[folio]["labels"] += 1

    # Select best 5 (highest combined complexity) from DIFFERENT themes
    selected = []
    seen_themes = set()
    
    # Sort folios by complexity (bisections + labels)
    sorted_folios = sorted(stats.items(), key=lambda x: x[1]["bisections"] + x[1]["labels"], reverse=True)

    for folio, data in sorted_folios:
        if data["bisections"] + data["labels"] == 0: continue
        theme = data["theme"]
        
        # We want 5 different topics, but if we already have one of each, we can take anything
        if theme not in seen_themes and len(selected) < 5:
            selected.append((folio, data))
            seen_themes.add(theme)
            
    # If we do not have 5 yet, fill with most complex regardless of topic
    if len(selected) < 5:
        for folio, data in sorted_folios:
            if len(selected) >= 5: break
            if folio not in [s[0] for s in selected]:
                selected.append((folio, data))

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Rekomenduojami Puslapiai (Folios) Naujam Pixel Mappingui\n\n")
        f.write("We selected 5 most complex, unseen pages from different thematic sections, having the most bisections and labels. This will allow testing the isomorphic alchemy theory in completely different contexts.\n\n")
        
        for folio, data in selected:
            f.write(f"### Folio: `{folio}`\n")
            f.write(f"* **Tema:** {data['theme']}\n")
            f.write(f"* **Bisections (text crosses drawing):** {data['bisections']}\n")
            f.write(f"* **Labels (isolated words):** {data['labels']}\n")
            f.write(f"* **Why selected:** Represents unique '{data['theme']}' area, having particularly much visual-textual integration.\n\n")

if __name__ == "__main__":
    select_folios()
