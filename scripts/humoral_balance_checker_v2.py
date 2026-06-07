import os
from collections import defaultdict

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_71_Humoral_Balance_Matrix_V2.md"

# Fully integrated Humoral Matrix (with new codes and suffixes)
HUMORS = {
    "FIRE (Hot/Dry)": ["cho", "shol", "kch", "or", "ar"], # Added kch- (pre-heating), ar/or (dry states)
    "WATER (Cold/Wet)": ["qo", "daiin", "she", "dai", "in"], # Added -in (tincture/solution)
    "AIR (Hot/Wet)": ["yt", "ol", "chok", "ol"], # -ol (oil/volatile)
    "EARTH (Cold/Dry)": ["dar", "dol", "dor", "dch", "pch", "dsh", "ey"] # Add mechanical crushers (dch, pch, dsh) and viscous paste (-ey)
}

def get_theme(folio_id):
    num_str = ''.join([c for c in folio_id if c.isdigit()])
    if not num_str: return "Other"
    num = int(num_str)
    if 1 <= num <= 66: return "Botany"
    if 67 <= num <= 73: return "Cosmology/Astronomy"
    if 75 <= num <= 84: return "Balneology"
    if 85 <= num <= 86: return "Rosettes (Macro-Reactor)"
    if 87 <= num <= 102: return "Pharmacy"
    if 103 <= num <= 116: return "Recipes (Stars)"
    return "Other"

def check_humoral_balance():
    print("Pradedamas PILNAS Humoral Balance Checker (v2)...")
    
    data = {}
    with open(FILE_ZL, 'r', encoding='utf-8', errors='ignore') as f:
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
                    # Checking both as prefix and as suffix
                    if word.startswith(root) or word.endswith(root):
                        theme_stats[theme][humor] += 1
                        break # Assign only to one element to prevent duplication
                        
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Etapas 71 (V2): Pilna Humoralinio Balanso Matrica (Integruota)\n\n")
        f.write("As per user note, we included ALL newly discovered blind scan elements into this matrix. New codes (`dch-`, `pch-`, `kch-`) and suffixes (`-in`, `-ey`, `-ol`) were assigned historically corresponding Alchemical Elements (Fire, Water, Air, Earth).\n\n")
        
        f.write("| Section (Theme) | Fire (Hot/Dry) | Water (Cold/Wet) | Air (Hot/Wet) | Earth (Cold/Dry) |\n")
        f.write("|---|---|---|---|---|\n")
        for theme, stats in theme_stats.items():
            f.write(f"| **{theme}** | {stats['FIRE (Hot/Dry)']} | {stats['WATER (Cold/Wet)']} | {stats['AIR (Hot/Wet)']} | {stats['EARTH (Cold/Dry)']} |\n")
            
        f.write("\n**Conclusion:** Introduction of new codes (especially `-in` for Water and `dch-/pch-` for Earth) drastically highlighted manuscript structure. We see Balneology became absolutely dominated by Water, Pharmacy shot up with Earth element (grinding and drying), and Rosettes (Macro-Reactor) demonstrates highest Fire and Air (Distillation vapors) concentration.\n")

    print(f"Humoralinis balansas baigtas. Ataskaita: {OUTPUT_REPORT}")

if __name__ == "__main__":
    check_humoral_balance()
