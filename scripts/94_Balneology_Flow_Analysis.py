import os
import sys
import json
import collections

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# Goal: Phase 94, Balneology Flow and Structure Analysis (f77r, f78r, f80v)
# We will check if the "Baths" section structurally matches liquid flows and condensation.

JSON_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
BALNEOLOGY_FILES = ["f77r_mapping.json", "f78r_mapping.json", "f80v_mapping.json"]

print("# Phase 94: Balneology Piping and Flow Analysis (Balneological Flow Audit)")
print("Hypothesis: 'Balneology' section is not people bathing, but Athanor condensation / cooling / filtering piping schemes.\n")

isolated_words_pool = []
isolated_words_pipe = []
isolated_words_nymph = []
all_words = []

colors_found = collections.Counter()
categories_found = collections.Counter()

files_processed = 0

for f in BALNEOLOGY_FILES:
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
    
    # Creating statistics from anchors
    for a in data.get("visual_anchors", []):
        cat = a.get("category", "").lower()
        categories_found[cat] += 1
        for color in a.get("colors", []):
            colors_found[color.lower()] += 1
            
    # Analizuojame etiketes
    for label in data.get("isolated_labels", []):
        raw_text = label.get("raw_text", "").strip()
        words = [w for w in raw_text.replace('.', ' ').split() if w.isalpha() and len(w) > 2]
        all_words.extend(words)
        
        anchor_id = label.get("target_anchor_id", "unknown")
        anchor = anchors.get(anchor_id, {})
        
        ctx = label.get("placement_context", "").lower()
        cat = anchor.get("category", "").lower()
        desc = anchor.get("morphology_description", "").lower()
        
        combined_context = ctx + " " + cat + " " + desc
        
        if "pipe" in combined_context or "tube" in combined_context or "spout" in combined_context or "conduit" in combined_context:
            isolated_words_pipe.extend(words)
        elif "pool" in combined_context or "water" in combined_context or "basin" in combined_context or "fluid" in combined_context:
            isolated_words_pool.extend(words)
        elif "nymph" in combined_context or "figure" in combined_context or "person" in combined_context:
            isolated_words_nymph.extend(words)
        else:
            # Fallback, add to general pool, but count as 'other'
            pass

print(f"Successfully read files: {files_processed}\n")

print("## 1. Visual Anchor Morphology and Colors (Balneology Materials)")
print("Most common anchor categories:")
for cat, count in categories_found.most_common(5):
    print(f"- `{cat}`: {count} vnt.")
    
print("\nMost common anchor colors:")
for color, count in colors_found.most_common(5):
    print(f"- `{color}`: {count} vnt.")

def get_affixes(words, length=2):
    prefixes = collections.Counter([w[:length] for w in words if len(w) > length])
    suffixes = collections.Counter([w[-length:] for w in words if len(w) > length])
    return prefixes, suffixes

pipe_p, pipe_s = get_affixes(isolated_words_pipe)
pool_p, pool_s = get_affixes(isolated_words_pool)
nymph_p, nymph_s = get_affixes(isolated_words_nymph)

print("\n## 2. Pipes (Flow) vs Basins (Pools) Syntax")
print("Checking flow asymmetry. According to previous findings, outflow (pipes) should associate with `qo-`/`ch-`, and pools (inflow/condensate) with `-in` / `so-`.\n")

print("### Pipes/Tubes labels")
print(f"Total words: {len(isolated_words_pipe)}")
if len(isolated_words_pipe) > 0:
    print("Top Prefixes (Start):", ", ".join([f"`{p}-`({c})" for p, c in pipe_p.most_common(5)]))
    print("Top Priesagos (Pabaiga):", ", ".join([f"`-{s}`({c})" for s, c in pipe_s.most_common(5)]))

print("\n### Pools / Liquids labels")
print(f"Total words: {len(isolated_words_pool)}")
if len(isolated_words_pool) > 0:
    print("Top Prefixes (Start):", ", ".join([f"`{p}-`({c})" for p, c in pool_p.most_common(5)]))
    print("Top Priesagos (Pabaiga):", ", ".join([f"`-{s}`({c})" for s, c in pool_s.most_common(5)]))

print("\n### Nymph (Figures/Nymphs) labels")
print(f"Total words: {len(isolated_words_nymph)}")
if len(isolated_words_nymph) > 0:
    print("Top Prefixes (Start):", ", ".join([f"`{p}-`({c})" for p, c in nymph_p.most_common(5)]))
    print("Top Priesagos (Pabaiga):", ", ".join([f"`-{s}`({c})" for s, c in nymph_s.most_common(5)]))

print("\n## 3. Water / Condensate Match Test (so- prefix)")
print("Searching for specific `so-` prefix, previously identified as liquid (BLUE/WATER) indicator.")
so_words = [w for w in all_words if w.startswith('so')]
if so_words:
    print(f"Words with prefix `so-` found {len(so_words)} times in these 'water' structures.")
else:
    print("Words with `so-` prefix in isolated labels not found (might be in text itself).")

print("\n## CONCLUSIONS")
print("If pipes match Athanor connections (Rosettes bridges) syntax (e.g., `qo-` outflow), and pools and liquids correlate with `-in` (inflow) or `so-` (water), it definitively links Balneology section with Alchemical Distillation.")
