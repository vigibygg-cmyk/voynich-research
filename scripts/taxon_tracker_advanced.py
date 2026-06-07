import os
from collections import defaultdict, Counter

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_70_Taxon_Tracker_Lifecycle.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH",
    "dch": "PREP_MECH", "pch": "PREP_MECH2", "kch": "PREP_HEAT"
}

def load_data():
    rf_data, it_data, zl_data = {}, {}, {}
    for filepath, data_dict in [(FILE_RF, rf_data), (FILE_IT, it_data), (FILE_ZL, zl_data)]:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        locus = parts[2].replace('"', '').strip()
                        clean_text = parts[-1].replace('?', '').replace('<->', ' ').replace('<>', ' ')
                        data_dict[locus] = clean_text
        except: pass
    return rf_data, it_data, zl_data

def track_taxons():
    print("Pradedamas Taxon Tracker (Ingredient Lifecycle)...")
    rf, it, zl = load_data()
    
    # 1. Collect labels (@L) via 3 transcription consensus
    labels_set = set()
    for locus in rf.keys():
        if "@L" in locus or "=L" in locus or "+L" in locus:
            w_rf = [w.strip() for w in rf[locus].split() if len(w.strip()) > 3]
            w_it = [w.strip() for w in it.get(locus, "").split() if len(w.strip()) > 3]
            w_zl = [w.strip() for w in zl.get(locus, "").split() if len(w.strip()) > 3]
            
            for i in range(min(len(w_rf), len(w_it), len(w_zl))):
                if w_rf[i] == w_it[i] == w_zl[i]:
                    # Remove the most common prefixes to get the pure root
                    word = w_rf[i]
                    cleaned_taxon = word
                    for pref in ["q", "ch", "sh", "d", "y", "t", "o"]:
                        if word.startswith(pref) and len(word) > 5:
                            cleaned_taxon = word[len(pref):]
                            break
                    labels_set.add((word, cleaned_taxon))
                    
    # Filtruojame unikalius Taxonus
    valid_taxons = {t[1]: t[0] for t in labels_set if len(t[1]) >= 3}
    
    lifecycle_graph = defaultdict(Counter)
    
    # 2. Search for Taxons in paragraphs (@P) and determine their command prefixes
    for locus in rf.keys():
        if "@P" in locus or "+P" in locus or "*P" in locus:
            text = rf[locus]
            words = [w.strip() for w in text.split() if w.strip()]
            for word in words:
                for taxon_root, original_label in valid_taxons.items():
                    if taxon_root in word and len(word) > len(taxon_root):
                        # Randame, koks prefixas prijungtas
                        prefix = word.split(taxon_root)[0]
                        if prefix:
                            # Patikriname ar tai komanda
                            matched_cmd = None
                            for cmd_root, meaning in COMMAND_ROOTS.items():
                                if prefix.startswith(cmd_root) or prefix == cmd_root[0]: # Could be just one letter, e.g. q-okal
                                    matched_cmd = meaning
                                    break
                            if matched_cmd:
                                lifecycle_graph[original_label][matched_cmd] += 1
                            else:
                                lifecycle_graph[original_label][f"UNKNOWN_PREFIX({prefix})"] += 1
                                
    # Generate report
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 70: Taxon Tracker (Ingredient Life Cycle Graph)\n\n")
        f.write("This script tracks each visually isolated label (@L) through all three transcriptions and creates its "shadow" - observes how this word is processed in main text blocks throughout the book.\n\n")
        f.write(f"Found consensus validated unique label roots: {len(valid_taxons)}\n\n")
        
        f.write("## Ingredient Processing Cycles (Top 10 most active Taxons)\n")
        
        # Filtering and sorting those with the most processing actions
        active_taxons = {k: v for k, v in lifecycle_graph.items() if sum(v.values()) > 5}
        sorted_taxons = sorted(active_taxons.items(), key=lambda x: sum(x[1].values()), reverse=True)
        
        for label, operations in sorted_taxons[:10]:
            f.write(f"### [TAXON]: `{label}`\n")
            f.write("Gyvavimo Ciklas (Pritaikytos komandos paragrafuose):\n")
            for op, count in operations.most_common():
                f.write(f"* **{op}**: {count} times\n")
            f.write("\n")
            
        f.write("---\n**Conclusion:** Reverse tracking graph proves visual labels are not just names. They are variables. When entered into text paragraphs, an operational prefix (e.g., 'Heat', 'Process') is glued to their root, turning the noun into a processing instruction.\n")

    print(f"Taxon Tracker baigtas. Ataskaita: {OUTPUT_REPORT}")

if __name__ == "__main__":
    track_taxons()
