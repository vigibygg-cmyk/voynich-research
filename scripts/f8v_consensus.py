import os
import json

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_53_f8v_Consensus.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH",
    "or": "SOLIDIFY", "dor": "DRY"
}

def load_f8v_transcription(filepath):
    lines_dict = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    folio = parts[1]
                    if folio != "f8v": continue
                    locus = parts[2].strip('"')
                    clean_text = parts[-1]
                    lines_dict[locus] = clean_text
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return lines_dict

def get_bisection_starts(text):
    # Returns all words that immediately follow line start or bisection <-> or <>
    starts = []
    if not text: return starts
    
    parts = text.replace("<->", "<>").split("<>")
    for i, p in enumerate(parts):
        words = [w.strip() for w in p.split(' ') if w.strip()]
        if words:
            # We want the first word of the segment
            word = words[0].replace('<', '').replace('>', '').replace('%', '').replace('$', '')
            if word:
                starts.append((i, word))
    return starts

def analyze_f8v():
    print("Kraunamos visos 3 f8v transkripcijos...")
    rf_data = load_f8v_transcription(FILE_RF)
    it_data = load_f8v_transcription(FILE_IT)
    zl_data = load_f8v_transcription(FILE_ZL)
    
    # Sorting roots
    sorted_roots = sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    consensus_sequence = []
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 53: Folio f8v Three Transcription Consensus\n\n")
        
        # Take all unique loci on f8v page that have bisection in RF file
        loci = sorted([k for k, v in rf_data.items() if "<>" in v or "<->" in v])
        
        for locus in loci:
            rf_text = rf_data.get(locus, "")
            it_text = it_data.get(locus, "")
            zl_text = zl_data.get(locus, "")
            
            rf_starts = get_bisection_starts(rf_text)
            it_starts = get_bisection_starts(it_text)
            zl_starts = get_bisection_starts(zl_text)
            
            # Compare each segment
            for i in range(len(rf_starts)):
                rf_word = rf_starts[i][1] if i < len(rf_starts) else ""
                it_word = it_starts[i][1] if i < len(it_starts) else ""
                zl_word = zl_starts[i][1] if i < len(zl_starts) else ""
                
                rf_root, rf_meaning = next(((r, m) for r, m in sorted_roots if rf_word.startswith(r)), (None, None))
                it_root, _ = next(((r, m) for r, m in sorted_roots if it_word.startswith(r)), (None, None))
                zl_root, _ = next(((r, m) for r, m in sorted_roots if zl_word.startswith(r)), (None, None))
                
                if rf_root:
                    if rf_root == it_root == zl_root:
                        consensus_sequence.append(rf_meaning)
                        f.write(f"* Locus `{locus}` (Seg {i}): All agree on **{rf_root}-** ({rf_meaning}). Words: RF:`{rf_word}`, IT:`{it_word}`, ZL:`{zl_word}`\n")
                    else:
                        f.write(f"* Locus `{locus}` (Seg {i}): NO FULL CONSENSUS for **{rf_root}-**. Words: RF:`{rf_word}`, IT:`{it_word}`, ZL:`{zl_word}`\n")
                        
        f.write("\n## Final 100% Confirmed Chain:\n")
        f.write(" -> ".join(consensus_sequence) + "\n")

    print(f"F8v analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_f8v()
