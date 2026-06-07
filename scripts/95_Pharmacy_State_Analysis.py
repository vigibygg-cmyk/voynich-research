import os
import sys
import json
import collections

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# Goal: Phase 95, Pharmacy "State of Matter" Test (f88v, f102v)
# We will check if vessels with liquids and vessels with powders (solids) have different suffixes.

JSON_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
PHARMA_FILES = ["f88v_mapping.json", "f102v1_mapping.json", "f102v2_mapping.json"]

print("# Phase 95: Pharmacy Vessel Contents (Liquid vs Powder)")
print("Hypothesis: Different dosing suffixes are used to indicate different state materials (liquids vs dry powders).\n")

liquid_jars = []
solid_jars = []
unknown_jars = []

files_processed = 0

for f in PHARMA_FILES:
    path = os.path.join(JSON_DIR, f)
    if not os.path.exists(path):
        continue
        
    with open(path, 'r', encoding='utf-8') as fp:
        try:
            data = json.load(fp)
            files_processed += 1
        except Exception as e:
            print(f"Nepavyko nuskaityti {f}")
            continue
            
    anchors = {a.get("anchor_id", "unknown"): a for a in data.get("visual_anchors", [])}
    
    # Analizuojame etiketes
    for label in data.get("isolated_labels", []):
        raw_text = label.get("raw_text", "").strip()
        words = [w for w in raw_text.replace('.', ' ').split() if w.isalpha() and len(w) > 2]
        
        anchor_id = label.get("target_anchor_id", "unknown")
        anchor = anchors.get(anchor_id, {})
        
        desc = anchor.get("morphology_description", "").lower()
        cat = anchor.get("category", "").lower()
        
        if not words: continue
        
        # Checking if vessel is liquid, solid or unclear
        if "liquid" in desc or "water" in desc or "fluid" in desc or "blue" in desc or "green" in desc or "narrow neck" in desc:
            liquid_jars.extend(words)
        elif "powder" in desc or "dry" in desc or "lidded box" in desc or "solid" in desc or "empty" in desc:
            solid_jars.extend(words)
        elif "jar" in cat or "vessel" in cat:
            # Fallback based on colors if description lacks explicit state
            colors = str(anchor.get("colors", [])).lower()
            if "blue" in colors or "green" in colors:
                liquid_jars.extend(words)
            elif "brown" in colors or "red" in colors or "gold" in colors:
                solid_jars.extend(words)
            else:
                unknown_jars.extend(words)

print(f"Successfully read files: {files_processed}\n")

def get_affixes(words, length=2):
    prefixes = collections.Counter([w[:length] for w in words if len(w) > length])
    suffixes = collections.Counter([w[-length:] for w in words if len(w) > length])
    return prefixes, suffixes

liq_p, liq_s = get_affixes(liquid_jars)
sol_p, sol_s = get_affixes(solid_jars)
unk_p, unk_s = get_affixes(unknown_jars)

print("## 1. Liquid Vessels (Liquid Vessels)")
print(f"Found label words: {len(liquid_jars)}")
if len(liquid_jars) > 0:
    print("Top Suffixes (Endings):", ", ".join([f"`-{s}`({c})" for s, c in liq_s.most_common(5)]))

print("\n## 2. Dry Materials / Powder Vessels (Dry/Solid Vessels)")
print(f"Found label words: {len(solid_jars)}")
if len(solid_jars) > 0:
    print("Top Suffixes (Endings):", ", ".join([f"`-{s}`({c})" for s, c in sol_s.most_common(5)]))
    
print("\n## 3. Kiti Farmacijos Indai (Pagal Spalvas)")
print(f"Found label words: {len(unknown_jars)}")
if len(unknown_jars) > 0:
    print("Top Suffixes (Endings):", ", ".join([f"`-{s}`({c})" for s, c in unk_s.most_common(5)]))

print("\n## CONCLUSIONS")
print("Tables clearly show if one suffix set (e.g., `-shol`, `-in`) is used for liquid substances, and another (e.g., `-os`, `-dy`) for solids / other colors.")
