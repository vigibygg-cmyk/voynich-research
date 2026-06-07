import os
import re
from collections import defaultdict

CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_39_Semantic_Triangulation.md"

# Corresponding keywords in historical texts (Latin, German and English languages)
CATEGORIES = {
    "Engineering_Balneology": [
        "bath", "balneo", "balneum", "tub", "pool", "water", "aqua", "wasser", "bad",
        "pipe", "tube", "fistula", "rohr", "vas", "furnace", "furnus", "oven", "distill", "distillare"
    ],
    "Alchemical_Operations": [
        "heat", "calefacere", "ignis", "feuer", "extract", "extrahere", "mix", "misce", "mischen",
        "filter", "filtra", "pour", "funde", "boil", "ebullire", "kochen", "grind", "tere"
    ],
    "Astrological_Time": [
        "moon", "luna", "mond", "sun", "sol", "sonne", "star", "stella", "stern", 
        "days", "dies", "tage", "zodiac", "aries", "taurus", "spring", "ver", "frühling"
    ]
}

TARGET_FILES = [
    "Latin_Alchemy.txt",
    "Latin_Botany_Medicine.txt",
    "Latin_Astronomy_Astrology.txt",
    "German_Botany_Medicine.txt",
    "English_Alchemy.txt",
    "English_Botany_Medicine.txt"
]

def triangulate():
    print("Starting Combined Semantic Search...")
    
    results = []
    
    for filename in TARGET_FILES:
        filepath = os.path.join(CORPORA_DIR, filename)
        if not os.path.exists(filepath):
            continue
            
        print(f"Skenuojamas failas: {filename}")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Simplified paragraph separation (double newline symbol)
        paragraphs = re.split(r'\n\s*\n', content)
        
        for p in paragraphs:
            p_lower = p.lower()
            matches = {
                "Engineering_Balneology": [],
                "Alchemical_Operations": [],
                "Astrological_Time": []
            }
            
            for cat_name, keywords in CATEGORIES.items():
                for kw in keywords:
                    if re.search(r'\b' + kw + r'\b', p_lower):
                        matches[cat_name].append(kw)
                        
            # We are looking for "Holy Grail" – text containing at least one word from all 3 categories (or at least 2)
            matched_categories = sum(1 for k, v in matches.items() if len(v) > 0)
            
            if matched_categories >= 3:
                # Found perfect match!
                results.append({
                    "file": filename,
                    "text": p.strip(),
                    "matches": matches
                })
                
    # Generate report
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 39: Combined Semantic Search Results\n\n")
        f.write("This report combines **Historical texts, Engineering drawings and Astrological cycles** search. We scanned medieval Latin, English and German corpora looking for paragraphs simultaneously describing: hydraulics/pools, operational heating/mixing and astrological/calendar time. This helps to directly link Voynich 'f75v' (balneological) drawings with real historical processes.\n\n")
        
        f.write(f"**Found unique three domain intersection paragraphs:** {len(results)}\n\n")
        
        for i, res in enumerate(results[:20]): # Rodome top 20
            f.write(f"## {i+1}. Source: `{res['file']}`\n")
            f.write(f"**Recognized keywords:**\n")
            f.write(f"* Engineering/Baths: {', '.join(res['matches']['Engineering_Balneology'])}\n")
            f.write(f"* Alchemija/Operacijos: {', '.join(res['matches']['Alchemical_Operations'])}\n")
            f.write(f"* Astrologija/Laikas: {', '.join(res['matches']['Astrological_Time'])}\n\n")
            f.write(f"> **Excerpt:**\n> {res['text'][:800]}...\n\n")
            f.write("---\n")

    print(f"Search completed. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    triangulate()
