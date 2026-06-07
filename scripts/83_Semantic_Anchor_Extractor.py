import json
import glob
import os
import sys

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# Configuration
JSON_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
FILES = [
    "f71r_mapping.json", 
    "f72r1_pixel_mapping.json", 
    "f17r_pixel_mapping.json", 
    "f100r_pixel_mapping.json"
]

labels_data = []

# 1. Read and merge data
for f in FILES:
    path = os.path.join(JSON_DIR, f)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as fp:
            try:
                data = json.load(fp)
            except Exception as e:
                print(f"Klaida skaitant {f}: {e}")
                continue
            
            folio = data.get("folio", f.split('_')[0])
            anchors = {a["anchor_id"]: a for a in data.get("visual_anchors", [])}
            
            for label in data.get("isolated_labels", []):
                anchor_id = label.get("target_anchor_id", "unknown")
                anchor = anchors.get(anchor_id, {})
                
                # Cleaning text (removing dots or uncertainties, but keeping original for study)
                raw_text = label.get("raw_text", "").strip()
                words = raw_text.split('.') # Sometimes label has several words separated by dot
                
                for w in words:
                    if not w: continue
                    labels_data.append({
                        "folio": folio,
                        "locus": label.get("locus", ""),
                        "word": w,
                        "raw_text": raw_text,
                        "category": anchor.get("category", "unknown_category"),
                        "colors": [c.lower() for c in anchor.get("colors", [])],
                        "anchor_id": anchor_id
                    })

print("# Phase 83: Strict Empirical Semantic Anchor Analysis (Cross-Domain Semantic Anchoring)")
print("\n## 1. Bendra Statistika")
print(f"- Analyzed folios: {', '.join(FILES)}")
print(f"- Found unique visually grounded words (isolated labels): {len(labels_data)}")

# 2. 'ot-' and 'ok-' prefix analysis (Cross-Domain)
print("\n## 2. 'ot-' and 'ok-' prefix distribution by domains (Cross-Domain Tracking)")
print("Hypothesis: Are `ot-` and `ok-` specific only to Zodiac (e.g. numbers/months), or are they universal state/action commands?")
print("\n| Word | Folio | Category | Colors | Related Object |")
print("|-------|---------|------------|---------|------------------|")

ot_ok_words = [d for d in labels_data if d['word'].startswith('ot') or d['word'].startswith('ok')]
for d in sorted(ot_ok_words, key=lambda x: x['folio']):
    colors = ", ".join(d['colors']) if d['colors'] else "No data"
    print(f"| **{d['word']}** | {d['folio']} | {d['category']} | {colors} | {d['anchor_id']} |")

# 3. Color and suffix/prefix correlation (Scientific test)
print("\n## 3. Color Correlation Test (Strict Falsification)")
print("Checking if certain prefixes exclusively correlate with 'blue' (water/liquid) or 'red/gold' (fire/heat) attributes.")

color_prefixes = {}
for d in labels_data:
    prefix = d['word'][:2]
    if len(prefix) < 2: continue
    
    for color in d['colors']:
        base_color = "red/gold" if any(c in color for c in ['red', 'gold', 'orange']) else \
                     "blue/water" if any(c in color for c in ['blue', 'teal', 'cobalt']) else \
                     "green/plant" if 'green' in color else \
                     "brown/earth" if 'brown' in color else "other"
                     
        if base_color not in color_prefixes:
            color_prefixes[base_color] = {}
        color_prefixes[base_color][prefix] = color_prefixes[base_color].get(prefix, 0) + 1

for color_group, prefixes in color_prefixes.items():
    print(f"\n### Objektai su spalva: **{color_group.upper()}**")
    sorted_pref = sorted(prefixes.items(), key=lambda x: x[1], reverse=True)
    for pref, count in sorted_pref[:5]: # Top 5 prefixes per color
        print(f"- Prefix `{pref}-`: found {count} times")

# 4. Search for morphological forms in Pharmacy and Botany
print("\n## 4. Pharmacy and Botany Specific Markers (Vessels vs. Roots)")
print("\n| Word | Folio | Type (Vessel/Root) | Morphological description |")
print("|-------|---------|-----------------------|----------------------|")
pharma_botany = [d for d in labels_data if 'pharma' in d['category'] or 'botany' in d['category']]
for d in sorted(pharma_botany, key=lambda x: x['category']):
    print(f"| **{d['word']}** | {d['folio']} | {d['category']} | {d['anchor_id']} |")

print("\n## 5. Zodiac radial label sequence (For Calendar / Numbers phonetic test)")
zodiac_f71 = [d['word'] for d in labels_data if d['folio'] == 'f71r' and 'nymph' in d['category']]
zodiac_f72 = [d['word'] for d in labels_data if d['folio'] == 'f72r1' and 'nymph' in d['category']]

print(f"\n**f71r (Aries) Nymph labels (In order):**\n" + ", ".join(zodiac_f71))
print(f"\n**f72r1 (Sagittarius/Scorpio) Nymph labels (In order):**\n" + ", ".join(zodiac_f72))

print("\n---\n**CONCLUSION:** Script successfully extracted data. Next step - perform human and AI analytical evaluation (see report).")
