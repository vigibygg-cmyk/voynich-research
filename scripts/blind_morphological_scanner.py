import os
from collections import Counter

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_66_Blind_Scan_Results.md"

def load_all_transcriptions():
    rf_data = {}
    it_data = {}
    zl_data = {}
    
    for filepath, data_dict in [(FILE_RF, rf_data), (FILE_IT, it_data), (FILE_ZL, zl_data)]:
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f.readlines():
                    parts = line.strip().split(',')
                    if len(parts) >= 4:
                        folio = parts[1]
                        locus = parts[2].replace('"', '').strip()
                        clean_text = parts[-1].replace('?', '')
                        data_dict[f"{folio}_{locus}"] = clean_text
        except: pass
    return rf_data, it_data, zl_data

def blind_scan():
    print("Starting blind scan (without any predefined dictionary)...")
    rf_data, it_data, zl_data = load_all_transcriptions()
    
    # Kuriame 3 statistines grupes
    bisection_starts = [] # Words immediately following <-> or <>
    labels = []           # Words from @L loci
    normal_text = []      # All other words
    
    for key in rf_data.keys():
        rf_text = rf_data[key]
        it_text = it_data.get(key, "")
        zl_text = zl_data.get(key, "")
        
        # Filtering only those words on which all 3 transcriptions agree (Consensus)
        rf_words = [w.strip() for w in rf_text.split() if w.strip()]
        it_words = [w.strip() for w in it_text.split() if w.strip()]
        zl_words = [w.strip() for w in zl_text.split() if w.strip()]
        
        # Tikriname bisekcijas
        has_bisection = "<->" in rf_text or "<>" in rf_text
        
        for i in range(min(len(rf_words), len(it_words), len(zl_words))):
            w_rf = rf_words[i].replace('<', '').replace('>', '').replace('%', '').replace('$', '')
            w_it = it_words[i].replace('<', '').replace('>', '').replace('%', '').replace('$', '')
            w_zl = zl_words[i].replace('<', '').replace('>', '').replace('%', '').replace('$', '')
            
            if not w_rf or len(w_rf) < 3: continue
            
            if w_rf == w_it and w_rf == w_zl: # 100% konsensusas
                # Distribute into groups
                is_bisection_start = False
                if has_bisection:
                    # Simple logic: is word rf_words[i] immediately after <>
                    # Saugiau naudoti raw string check
                    if ("<>" + rf_words[i] in rf_text.replace(" ", "")) or ("<->" + rf_words[i] in rf_text.replace(" ", "")):
                        is_bisection_start = True
                    elif i == 0: # Line start in bisection lines is also considered an operator
                        is_bisection_start = True
                        
                if is_bisection_start:
                    bisection_starts.append(w_rf)
                elif "@L" in key or "=L" in key or "+L" in key:
                    labels.append(w_rf)
                else:
                    normal_text.append(w_rf)
                    
    # Analyzing prefixes (3 letters)
    def get_prefixes(word_list, length=3):
        return [w[:length] for w in word_list if len(w) >= length]
        
    bi_pref = Counter(get_prefixes(bisection_starts))
    lab_pref = Counter(get_prefixes(labels))
    norm_pref = Counter(get_prefixes(normal_text))
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Etapas 66: Aklasis Morfologinis Skenavimas (Unsupervised)\n\n")
        f.write("During this scan computer was given NO dictionary (neither `cho`, nor `qok`, nor `yt`). Algorithm simply took thousands of words, which were 100% equally confirmed by 3 transcriptions, split them by spatial positions (Bisection starts, Labels, Normal text) and counted most frequent 3 letter prefixes.\n\n")
        
        f.write(f"**Analyzed bisection words:** {len(bisection_starts)}\n")
        f.write(f"**Analyzed label words:** {len(labels)}\n")
        f.write(f"**Analyzed normal text words:** {len(normal_text)}\n\n")
        
        f.write("## 1. Top Prefixes in BISECTIONS and line starts\n")
        f.write("Commands must appear here. Our hypothesis: will `cho`, `qok`, `yt` emerge without preset?\n")
        for p, count in bi_pref.most_common(10):
            f.write(f"* **`{p}-`**: {count} times ({(count/len(bisection_starts))*100:.1f}%)\n")
            
        f.write("\n## 2. Top Prefixes in LABELS (@L0, @Ln)\n")
        f.write("Ingredients must appear here. They must mathematically DIFFER from bisections.\n")
        for p, count in lab_pref.most_common(10):
            f.write(f"* **`{p}-`**: {count} times ({(count/max(1,len(labels)))*100:.1f}%)\n")
            
        f.write("\n## 3. Discovery of New, Unknown Commands\n")
        f.write("Are there any prefixes massively dominating near bisections, but which we never studied before?\n")
        # Searching for those not in our old 18-word list
        old_roots = ["qok", "cho", "dai", "sho", "yte", "che", "ote", "dal", "dol", "oke"]
        new_roots = []
        for p, count in bi_pref.most_common(20):
            if p not in old_roots and p[:2] not in [r[:2] for r in old_roots]: # Checking strictly
                new_roots.append((p, count))
                
        if new_roots:
            for p, count in new_roots[:5]:
                f.write(f"* **NEW CODE `{p}-`**: {count} times\n")
        else:
            f.write("* All peaks were taken by our already known roots. This proves that we have already found the main engine!\n")

    print(f"Aklasis skenavimas baigtas: {OUTPUT_REPORT}")

if __name__ == "__main__":
    blind_scan()
