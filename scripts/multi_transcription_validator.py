import os
from collections import defaultdict

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti" # Using OLD neliesti, because bisections <> marks are saved there
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_50_Multi_Transcription_Consensus.md"

COMMAND_ROOTS = ["qok", "qo", "cho", "daiin", "shol", "yt", "chok", "she", "ok", "dar", "ol", "chee", "or", "dor", "ot", "qot", "dal", "dol", "chot", "dai"]

def load_transcription(filepath):
    data = {}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    folio = parts[1]
                    locus = parts[2].strip('"')
                    # Creating unique ID for line
                    line_id = f"{folio}_{locus}"
                    clean_text = parts[-1]
                    data[line_id] = clean_text
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
    return data

def get_first_word(text):
    if "<>" in text:
        left_side = text.split('<>')[0]
    elif "<->" in text:
         left_side = text.split('<->')[0]
    else:
        left_side = text
        
    words = [w.strip() for w in left_side.split(' ') if w.strip()]
    if words:
        word = words[0].replace('<', '').replace('>', '').replace('%', '').replace('$', '')
        return word
    return ""

def check_root(word):
    for root in COMMAND_ROOTS:
        if word.startswith(root):
            return root
    return None

def analyze_consensus():
    print("Kraunamos visos 3 transkripcijos...")
    rf_data = load_transcription(FILE_RF)
    it_data = load_transcription(FILE_IT)
    zl_data = load_transcription(FILE_ZL)
    
    # Find all bisection lines in main (RF) file
    rf_bisections = {k: v for k, v in rf_data.items() if "<>" in v or "<->" in v}
    
    total_bisections = len(rf_bisections)
    consensus_stats = {
        "all_agree_is_command": 0,
        "rf_it_agree": 0,
        "rf_zl_agree": 0,
        "only_rf_is_command": 0,
        "no_command_in_rf": 0
    }
    
    detailed_matches = []

    for line_id, rf_text in rf_bisections.items():
        it_text = it_data.get(line_id, "")
        zl_text = zl_data.get(line_id, "")
        
        rf_word = get_first_word(rf_text)
        it_word = get_first_word(it_text)
        zl_word = get_first_word(zl_text)
        
        rf_root = check_root(rf_word)
        it_root = check_root(it_word)
        zl_root = check_root(zl_word)
        
        if rf_root:
            if rf_root == it_root and rf_root == zl_root:
                consensus_stats["all_agree_is_command"] += 1
                if len(detailed_matches) < 20: # Save examples for report
                    detailed_matches.append((line_id, rf_root, rf_word, it_word, zl_word))
            elif rf_root == it_root:
                consensus_stats["rf_it_agree"] += 1
            elif rf_root == zl_root:
                consensus_stats["rf_zl_agree"] += 1
            else:
                consensus_stats["only_rf_is_command"] += 1
        else:
            consensus_stats["no_command_in_rf"] += 1

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 50: Multi-Transcription Consensus Analysis\n\n")
        f.write("In this phase we used 3 independent manuscript transcriptions (`RF1b-er_clean.csv` as main, `IT2a-n_clean.csv` and `ZL3b-n_clean.csv` as parallel). Goal: make sure our discovered operational commands (e.g., `cho-`, `qok-`) are not just optical illusion or error of one transcriber.\n\n")
        
        f.write(f"**Bisection lines found in RF1b file:** {total_bisections}\n\n")
        
        # Matematika
        total_commands = total_bisections - consensus_stats["no_command_in_rf"]
        f.write(f"**Lines STARTING with command in main file:** {total_commands} ({round((total_commands/max(1, total_bisections))*100, 1)}%)\n")
        
        all_3 = consensus_stats["all_agree_is_command"]
        rf_it = consensus_stats["rf_it_agree"]
        rf_zl = consensus_stats["rf_zl_agree"]
        
        f.write("### Konsensuso Lygiai:\n")
        f.write(f"* **Absolute Consensus (All 3 authors confirm SAME operational root):** {all_3} times ({round((all_3/max(1, total_commands))*100, 1)}% of all commands)\n")
        f.write(f"* **Partial Consensus (RF + IT match):** {rf_it} times\n")
        f.write(f"* **Partial Consensus (RF + ZL match):** {rf_zl} times\n")
        f.write(f"* **Weak signal (Only RF sees command):** {consensus_stats['only_rf_is_command']} times\n\n")
        
        f.write("**Conclusion:** If Absolute Consensus is high (e.g. above 70%), it definitively proves command roots are an objective fact on the parchment itself, not human transcription error.\n\n")
        
        f.write("### Absolute Consensus Examples (First 20 lines)\n")
        f.write("| Locus | Recognized Root | RF1b word | IT2a word | ZL3b word |\n")
        f.write("|---|---|---|---|---|\n")
        for m in detailed_matches:
            f.write(f"| `{m[0]}` | **{m[1]}-** | {m[2]} | {m[3]} | {m[4]} |\n")

    print(f"Consensus analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_consensus()
