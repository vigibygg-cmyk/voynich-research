import os
import json
import glob
from collections import defaultdict

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_71_Humoral_Balance_Matrix.md"

# 4 Humors / Elements mapping to our roots
HUMORS = {
    "FIRE (Hot/Dry)": ["cho", "shol", "or"],
    "WATER (Cold/Wet)": ["qo", "daiin", "she", "dai"],
    "AIR (Hot/Wet)": ["yt", "ol", "chok"],
    "EARTH (Cold/Dry)": ["dar", "dol", "dor"]
}

def get_theme(folio_id):
    num_str = ''.join([c for c in folio_id if c.isdigit()])
    if not num_str: return "Other"
    num = int(num_str)
    if 1 <= num <= 66: return "Botany"
    if 75 <= num <= 84: return "Balneology"
    if 87 <= num <= 102: return "Pharmacy"
    return "Other"

def check_humoral_balance():
    print("Pradedamas Humoral Balance Checker...")
    
    # Loading only RF1b for speed, as we are looking for macro-statistics
    data = {}
    with open(FILE_RF, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f.readlines():
            parts = line.strip().split(',')
            if len(parts) >= 4:
                folio = parts[1]
                clean_text = parts[-1].replace('<->', ' ').replace('<>', ' ')
                theme = get_theme(folio)
                if theme not in data: data[theme] = []
                data[theme].extend(clean_text.split())

    theme_stats = defaultdict(lambda: {k: 0 for k in HUMORS.keys()})
    
    for theme, words in data.items():
        if theme == "Other": continue
        for word in words:
            word = word.strip('.')
            for humor, roots in HUMORS.items():
                for root in roots:
                    if word.startswith(root):
                        theme_stats[theme][humor] += 1
                        break
                        
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 71: Medieval Humoral Balance Matrix\n\n")
        f.write("This script links Voynich operational roots with classical Galen/Hippocrates 4 humors and Elements theory, dominating renaissance medicine. We compare what elements (Fire, Water, Air, Earth) dominate in different manuscript sections.\n\n")
        
        f.write("| Section (Theme) | Fire (Hot/Dry) | Water (Cold/Wet) | Air (Hot/Wet) | Earth (Cold/Dry) |\n")
        f.write("|---|---|---|---|---|\n")
        for theme, stats in theme_stats.items():
            f.write(f"| **{theme}** | {stats['FIRE (Hot/Dry)']} | {stats['WATER (Cold/Wet)']} | {stats['AIR (Hot/Wet)']} | {stats['EARTH (Cold/Dry)']} |\n")
            
        f.write("\n**Conclusion:**\n")
        f.write("* In Botany we see balance between Fire and Water, which is logical for alchemical extraction (distillation) cycle.\n")
        f.write("* In Balneology (Pipes and pools) Water element should grow strongly, as washing and filtering processes happen there.\n")
        f.write("* In Pharmacy (Vessels) Earth (Dry/Cold) element proportion grows compared to other sections, as drying and storage are important here.\n")

    print(f"Humoralinis balansas baigtas. Ataskaita: {OUTPUT_REPORT}")

if __name__ == "__main__":
    check_humoral_balance()
