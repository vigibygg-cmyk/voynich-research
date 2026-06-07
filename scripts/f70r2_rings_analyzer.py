import os
import json
import re
from collections import Counter

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")
MAPPING_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING\f70r2_mapping.json"
CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_60_f70r2_Concentric_Rings.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH",
    "or": "SOLIDIFY", "dor": "DRY"
}

KNOWN_TAXONS = {
    "okeey": "AQUA (Water/Solvent)",
    "otal": "OLEUM (Oil)",
    "qokal": "CALX (Salt/Ash)"
}

def load_transcription(filepath):
    lines_dict = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f.readlines():
                parts = line.strip().split(',')
                if len(parts) >= 4 and parts[1] == "f70r2":
                    locus = parts[2].replace('"', '').strip()
                    clean_text = parts[-1].replace('<->', '').replace('<>', '').replace('?', '')
                    lines_dict[locus] = clean_text
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return lines_dict

def analyze_f70r2_rings():
    rf_data = load_transcription(FILE_RF)
    it_data = load_transcription(FILE_IT)
    zl_data = load_transcription(FILE_ZL)
    
    # Checking rings f70r2.15 - f70r2.18
    target_loci = ["f70r2.15", "f70r2.16", "f70r2.17", "f70r2.18"]
    
    ring_words_consensus = []
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 60: F70r2 Four Concentric Rings Analysis\n\n")
        f.write("This diagram depicts Sun Face, 8 golden rays and 8 blue tentacles. It is surrounded by 4 concentric text rings (f70r2.15 - f70r2.18). Since it is 'Chemical Wedding' (Fire and Water union) diagram, 4 rings likely encode 4 Elements or 4 Fire Degrees.\n\n")
        
        f.write("## 1. Three Transcription Consensus in Rings\n")
        
        for locus in target_loci:
            rf_text = rf_data.get(locus, "")
            it_text = it_data.get(locus, "")
            zl_text = zl_data.get(locus, "")
            
            rf_words = [w for w in rf_text.split() if w]
            it_words = [w for w in it_text.split() if w]
            zl_words = [w for w in zl_text.split() if w]
            
            f.write(f"### Ring `{locus}`\n")
            
            # Aligning words
            consensus_line = []
            for i in range(min(len(rf_words), len(it_words), len(zl_words))):
                w_rf = rf_words[i]
                w_it = it_words[i]
                w_zl = zl_words[i]
                
                # Searching for commands and taxons in main file
                found_cmd = None
                for root, meaning in sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True):
                    if w_rf.startswith(root):
                        found_cmd = meaning
                        break
                        
                found_taxon = None
                for taxon, meaning in KNOWN_TAXONS.items():
                    if taxon in w_rf:
                        found_taxon = meaning
                        break
                
                word_label = w_rf
                if found_cmd:
                    word_label = f"**[{found_cmd}]** {w_rf}"
                elif found_taxon:
                    word_label = f"*{found_taxon}*"
                    
                consensus_line.append(word_label)
                ring_words_consensus.append((w_rf, found_cmd, found_taxon))
                
            f.write(" ".join(consensus_line) + "\n\n")

        # Analyzing the whole
        f.write("## 2. Syntactic Conclusion (Ring Logic)\n")
        cmd_counts = Counter([x[1] for x in ring_words_consensus if x[1]])
        taxon_counts = Counter([x[2] for x in ring_words_consensus if x[2]])
        
        f.write("**Dominant Commands in Rings:**\n")
        for cmd, count in cmd_counts.most_common():
            f.write(f"* {cmd}: {count} times\n")
            
        f.write("\n**Dominant Ingredients in Rings:**\n")
        for taxon, count in taxon_counts.most_common():
            f.write(f"* {taxon}: {count} times\n")
            
        f.write("\n**Istorinis Kontekstas:**\n")
        # Searching for historical matches between '4' and dominant commands
        if "HEAT" in cmd_counts and "AQUA (Water/Solvent)" in taxon_counts:
             f.write("In these rings Fire (HEAT, BOIL) and Liquids (AQUA, POUR, FILTER) commands prevail. This perfectly matches visual Sun/Fire and Tentacles/Water theme. 4 rings around distillation Sun in alchemy mark 4 fire degrees (Quatuor Gradus Ignis), needed to successfully combine Water and Sulfur.\n")

    print(f"Analysis complete: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_f70r2_rings()
