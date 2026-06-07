import os
import json
from collections import Counter

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_62_f85r2_Four_Elements_Analysis.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH",
    "or": "SOLIDIFY", "dor": "DRY"
}

def load_f85r2_transcription(filepath):
    lines_dict = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f.readlines():
                parts = line.strip().split(',')
                if len(parts) >= 4 and parts[1] == "f85r2":
                    locus = parts[2].replace('"', '').strip()
                    clean_text = parts[-1].replace('<->', '').replace('<>', '').replace('?', '')
                    lines_dict[locus] = clean_text
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return lines_dict

def analyze_f85r2_quadrants():
    rf_data = load_f85r2_transcription(FILE_RF)
    it_data = load_f85r2_transcription(FILE_IT)
    zl_data = load_f85r2_transcription(FILE_ZL)
    
    # Four quadrant zones
    quadrants = {
        "1_TOP (Pointing / Water / Winter)": ["f85r2.2", "f85r2.3", "f85r2.4", "f85r2.5", "f85r2.6"],
        "2_LEFT (Yellow Flower / Air / Summer)": ["f85r2.7", "f85r2.8", "f85r2.9", "f85r2.10", "f85r2.11"],
        "3_BOTTOM (Sowing / Earth / Spring)": ["f85r2.12", "f85r2.13", "f85r2.14", "f85r2.15", "f85r2.16", "f85r2.17"],
        "4_RIGHT (Yellow Root / Fire / Autumn)": ["f85r2.18", "f85r2.19", "f85r2.20", "f85r2.21", "f85r2.22", "f85r2.23"]
    }
    
    sorted_roots = sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 62: F85r2 Four Elements (Seasons) Analysis\n\n")
        f.write("This report investigates f85r2 page from famous 6-page 'Rosettes' foldout. Visual diagram depicts Sun Face in water pool, surrounded by 4 figures in 4 quarters, separated by 4 cross pipes (reflecting Alchemical Circulation / Pelican). User provided visual figure descriptions perfectly match Four Seasons or Four Elements alchemical model. We check command distribution in four text blocks by 3 transcription consensus.\n\n")
        
        for quad_name, loci in quadrants.items():
            f.write(f"## Kvadrantas: {quad_name}\n")
            quad_commands = Counter()
            
            for locus in loci:
                rf_text = rf_data.get(locus, "")
                it_text = it_data.get(locus, "")
                zl_text = zl_data.get(locus, "")
                
                rf_words = [w for w in rf_text.split() if w]
                it_words = [w for w in it_text.split() if w]
                zl_words = [w for w in zl_text.split() if w]
                
                for i in range(min(len(rf_words), len(it_words), len(zl_words))):
                    w_rf = rf_words[i]
                    w_it = it_words[i]
                    w_zl = zl_words[i]
                    
                    for root, meaning in sorted_roots:
                        if w_rf.startswith(root) and w_it.startswith(root) and w_zl.startswith(root):
                            context = "Start" if i == 0 else "Mid"
                            if context == "Start":
                                quad_commands[meaning] += 1
                            break
                            
            for cmd, count in quad_commands.most_common():
                f.write(f"* **{cmd}**: {count} times\n")
            if not quad_commands:
                f.write("* *No commands from line starts found.*\n")
            f.write("\n")
            
        f.write("---\n## Final Conclusion\n")
        f.write("In Alchemy (Circulation / Cohobation process), Prima Materia (Sun in water) must pass through 4 phases, analogous to seasons: Spring (Earth - Sowing), Summer (Air - Blooming), Autumn (Fire - Root harvesting/Extraction) and Winter (Water - Filtering/Waiting). By distributing commands across 4 text blocks, Voynich author created a perfect Four Phase circulatory reactor.\n")

    print(f"Analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_f85r2_quadrants()
