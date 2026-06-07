import os
import sys
import csv
import collections

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

CLEAN_DATA_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data\RF1b-er_clean.csv"

print("# Phase 88b: Matematinio Dozavimo Testo Validacija Botanikoje (f25v, f31v)")
print("After successful 12:3 discovery on f17r page, testing new pages (f25v, f31v) based on AI extracted physical object numbers.\n")

# AI extracted visual data from f25v and f31v mappings
visual_data = {
    "f25v": {
        "lapai_total": 24, # 24 lanceolate leaves
        "lapu_grupe": 12, # 12 outer, 12 inner whorl
        "ziedai": 0,
        "stiebas": 1,
        "saknies_mazgas": 1
    },
    "f31v": {
        "ziedynas_A": 1, # Compound flower head
        "florets_A": 32, # Small dots on flower
        "spinduliai_A": 13, # Radiating lines from base of flower
        "lapai_A": 22, # 22 scalloped leaf units
        "saknies_lobai_A": 3, # 3 large rounded lobes
        "saknies_gijos_A": 3, # 3 long root strands
        "lapai_B": 7, # Ghost plant B leaves
        "ziedai_B": 2, # Ghost plant B dark flowers
        "sakos_B": 2 # Ghost plant B branches
    }
}

texts = {"f25v": [], "f31v": []}

with open(CLEAN_DATA_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        folio = row['Folio'].strip()
        if folio in texts:
            words = [w for w in row['Clean_Text'].strip().split() if w.isalpha() and len(w) > 1]
            texts[folio].extend(words)

# Counting frequencies
def get_stats(word_list):
    stats = {}
    stats['words'] = collections.Counter(word_list)
    stats['prefixes_2'] = collections.Counter([w[:2] for w in word_list if len(w) >= 3])
    stats['prefixes_3'] = collections.Counter([w[:3] for w in word_list if len(w) >= 4])
    stats['suffixes_2'] = collections.Counter([w[-2:] for w in word_list if len(w) >= 3])
    stats['suffixes_3'] = collections.Counter([w[-3:] for w in word_list if len(w) >= 4])
    stats['total_words'] = len(word_list)
    return stats

s_f25v = get_stats(texts['f25v'])
s_f31v = get_stats(texts['f31v'])

def find_exact_matches(folio, visual_dict, stats):
    print(f"## Analizuojamas Folio: {folio}")
    print(f"Total words on page: {stats['total_words']}")
    print("| Visual Parameter | Amount | Found Exact Linguistic Matches (Frequency = Amount) |")
    print("|---|---|---|")
    
    for feature, count in visual_dict.items():
        if count == 0: continue
        matches = []
        
        for w, c in stats['words'].items():
            if c == count: matches.append(f"Word `{w}`")
        for s, c in stats['suffixes_2'].items():
            if c == count: matches.append(f"Priesaga `-{s}`")
        for s, c in stats['suffixes_3'].items():
            if c == count: matches.append(f"Priesaga `-{s}`")
        for p, c in stats['prefixes_2'].items():
            if c == count: matches.append(f"Prefix `{p}-`")
            
        match_str = ", ".join(matches) if matches else "Nerasta tikslaus sutapimo"
        
        # Filtering longer lists (priority to suffixes and prefixes)
        if len(matches) > 5:
            filtered = [m for m in matches if "Suffix" in m or "Prefix" in m]
            if filtered:
                match_str = ", ".join(filtered) + f" (and {len(matches)-len(filtered)} others)"
            else:
                match_str = f"Found {len(matches)} random words (ignored)"
                
        print(f"| **{feature.capitalize()}** | {count} | {match_str} |")

find_exact_matches("f25v", visual_data["f25v"], s_f25v)
print("\n")
find_exact_matches("f31v", visual_data["f31v"], s_f31v)

print("\n## CONCLUSIONS AND CORRELATIONS")
print("1. **f25v (Leaves = 24 / Group = 12):** If we find suffix fixations at 24 or 12, it confirms f17r discovery (that `-hy` or other ending represents base of 12 units).")
print("2. **f31v (Numbers 3 and 22):** We analyze if root threads (3), flowers (2) and branches (2) reflect in prefixes. If suffix fixation matches physical element count again, Voynich measurement / dose system is deciphered.")
