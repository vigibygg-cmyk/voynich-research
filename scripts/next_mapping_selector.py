import os
import json
from collections import defaultdict

CSV_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti\ZL3b-n_clean.csv"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_49_Next_Targets.md"

# All pages we have already mapped
ALREADY_MAPPED = [
    "f1v", "f2r", "f8r", "f49v", "f67r1", "f67r2", "f68r1", "f68r3", 
    "f68v3", "f75r", "f75v", "f82r", "f87r", "f87v", "f88r", "f103r", 
    "f104r", "f105v", "f116r"
]

def get_theme(folio_id):
    try:
        num_str = ''.join([c for c in folio_id if c.isdigit()])
        if not num_str: return "Unknown"
        num = int(num_str)
        if 1 <= num <= 66: return "Botanika"
        if 67 <= num <= 73: return "Astronomija"
        if 75 <= num <= 84: return "Balneologija"
        if 85 <= num <= 86: return "Kosmologija"
        if 87 <= num <= 102: return "Farmacija"
        if 103 <= num <= 116: return "Receptai"
        return "Unknown"
    except:
        return "Unknown"

def select_next_targets():
    print("Scanning whole manuscript for new targets...")
    try:
        with open(CSV_FILE, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Error: {e}")
        return

    stats = defaultdict(lambda: {"bisections": 0, "labels": 0, "paragraphs": 0, "theme": "Unknown"})

    for line in lines:
        parts = line.strip().split(',')
        if len(parts) >= 4:
            folio = parts[1]
            locus = parts[2].strip('"')
            clean_text = parts[-1]

            # Ignoring those already investigated
            if folio in ALREADY_MAPPED: continue
            
            stats[folio]["theme"] = get_theme(folio)

            if "<>" in clean_text or "<->" in clean_text:
                stats[folio]["bisections"] += 1
            if "@L" in locus or "=L" in locus or "+L" in locus or "*L" in locus:
                stats[folio]["labels"] += 1
            if "@P" in locus or "+P" in locus or "*P" in locus:
                stats[folio]["paragraphs"] += 1

    targets = []
    
    # Criterion 1: Balneology with the most labels (check link between nymph names and pipes)
    balneo = {k: v for k, v in stats.items() if v["theme"] == "Balneologija"}
    if balneo:
        best_balneo = sorted(balneo.items(), key=lambda x: x[1]["labels"], reverse=True)[0]
        targets.append(("Balneology Label Test", best_balneo))

    # Criterion 2: Pharmacy with most bisections and paragraphs (check drug recipe structure)
    pharma = {k: v for k, v in stats.items() if v["theme"] == "Farmacija"}
    if pharma:
        best_pharma = sorted(pharma.items(), key=lambda x: x[1]["bisections"] + x[1]["paragraphs"], reverse=True)[0]
        targets.append(("Pharmacy Vessels and Roots Test", best_pharma))

    # Criterion 3: Cosmology foldout (Macro structure test)
    cosmo = {k: v for k, v in stats.items() if v["theme"] == "Kosmologija"}
    if cosmo:
        best_cosmo = sorted(cosmo.items(), key=lambda x: x[1]["labels"] + x[1]["paragraphs"], reverse=True)[0]
        targets.append(("Makro Kosmologijos Testas (Foldouts)", best_cosmo))

    # Criterion 4: Botany with most massive bisection chain
    botany = {k: v for k, v in stats.items() if v["theme"] == "Botanika"}
    if botany:
        best_botany = sorted(botany.items(), key=lambda x: x[1]["bisections"], reverse=True)[0]
        targets.append(("Massive Botanical Bisection Test", best_botany))

    # Criterion 5: Astronomy with most labels (time modifier test)
    astro = {k: v for k, v in stats.items() if v["theme"] == "Astronomija"}
    if astro:
        best_astro = sorted(astro.items(), key=lambda x: x[1]["labels"], reverse=True)[0]
        targets.append(("Astronominio Laiko Testas", best_astro))

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Next Research Phase: Strict Hypotheses and Targets\n\n")
        f.write("To avoid hasty conclusions and ensure strict scientific verification, we selected 5 new pages based on mathematical criteria. Each page must test a specific Pasigraphic Engine hypothesis.\n\n")
        
        for hyp, (folio, data) in targets:
            f.write(f"## Folio: `{folio}`\n")
            f.write(f"* **Hypothesis (Test):** {hyp}\n")
            f.write(f"* **Tema:** {data['theme']}\n")
            f.write(f"* **Statistics:** {data['bisections']} Bisections, {data['labels']} Labels, {data['paragraphs']} Paragraph lines.\n")
            
            # Adding logical explanation
            if "Balneologijos" in hyp:
                f.write("* **Scientific Goal:** Check the reverse model: do the names/labels of 'nymphs' (liquid elements) on this page migrate into the operational paragraphs of the same page.\n\n")
            elif "Pharmaceutical" in hyp:
                f.write("* **Scientific Goal:** Check if the text next to small rootlets and vessels maintains the same extraction logic as the large botany pages or transitions to microscopic doses.\n\n")
            elif "Kosmologijos" in hyp:
                f.write("* **Scientific Goal:** Cosmological foldouts (Rosettes) are the most complex drawings. We need to check if this macro-architecture uses the same spagyric roots or talks about completely different (e.g., geographic/alchemical furnace) operations.\n\n")
            elif "Bisekcijos" in hyp:
                f.write("* **Scientific Goal:** Find the longest possible algorithmic 'highway' in the botany section and perform the longest isomorphic translation.\n\n")
            elif "Astronominio" in hyp:
                f.write("* **Scientific Goal:** Extract more zodiac/month labels and check if they modify time in operation paragraphs.\n\n")

    print(f"Nauji taikiniai atrinkti. Ataskaita: {OUTPUT_REPORT}")

if __name__ == "__main__":
    select_next_targets()
