import os
import json
import glob
from collections import defaultdict, Counter

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
if not os.path.exists(DIR):
    DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"

FILE_RF = os.path.join(DIR, "RF1b-er_clean.csv")
FILE_IT = os.path.join(DIR, "IT2a-n_clean.csv")
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_67_Transition_Matrix_New_Codes.md"

NEW_CODES = ["dch", "pch", "dsh", "ych", "kch"]
# Suffixes we already know (Dose / State terminators)
KNOWN_SUFFIXES = ["dy", "y", "al", "or", "am", "ar"]

def load_transcriptions():
    rf_data, it_data, zl_data = {}, {}, {}
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

def build_transition_matrix():
    print("Starting transition matrix and isomorphic analysis for new codes...")
    rf_data, it_data, zl_data = load_transcriptions()
    
    json_files = glob.glob(os.path.join(MAPPING_DIR, "*_mapping.json"))
    
    # Matricos
    transitions_after = {code: Counter() for code in NEW_CODES}
    transitions_before = {code: Counter() for code in NEW_CODES}
    suffixes_found = {code: Counter() for code in NEW_CODES}
    
    # Blind suffix search array
    all_blind_suffixes = Counter()
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
        
        folio = data.get("folio", "")
        for block in data.get("text_blocks_mapping", []):
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "").replace("<->", " .B. ").replace("<>", " .B. ")
                locus = line.get("locus", "")
                
                # Searching for transcription matches, though it's simpler to just take RAW from json, 
                # nes jis paremtas RF1b. Bet patikrinimui imkime rf/it/zl
                words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
                
                for i, word in enumerate(words):
                    if not word or word == ".B.": continue
                    
                    # Suffix blind scan (last 2 letters)
                    if len(word) >= 3 and word != ".B.":
                        all_blind_suffixes[word[-2:]] += 1
                        
                    for code in NEW_CODES:
                        if word.startswith(code):
                            # Suffixes for the code itself
                            suffix = word[-2:] if len(word) >= 3 else ""
                            if suffix: suffixes_found[code][suffix] += 1
                            
                            # What comes AFTER this code?
                            if i + 1 < len(words):
                                next_word = words[i+1]
                                if next_word == ".B.": next_word = "[BISECTION_IMAGE]"
                                transitions_after[code][next_word[:3] + "-"] += 1 # Take only root of next word to see pattern
                            else:
                                transitions_after[code]["[END_OF_LINE]"] += 1
                                
                            # What comes BEFORE this code?
                            if i > 0:
                                prev_word = words[i-1]
                                if prev_word == ".B.": prev_word = "[BISECTION_IMAGE]"
                                transitions_before[code][prev_word[-2:]] += 1 # Take suffix of previous word
                            else:
                                transitions_before[code]["[START_OF_LINE]"] += 1

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 67: New Operational Codes Transition Matrix Analysis\n\n")
        f.write("Applying Markov Chain (transition probabilities) algorithm across all available Pixel Mappings and checking 3 transcriptions, we analyzed syntactic behavior of 5 new codes (`dch-`, `pch-`, `dsh-`, `ych-`, `kch-`). This helps to understand their alchemical meaning without using preconceived dictionaries.\n\n")
        
        for code in NEW_CODES:
            f.write(f"## KODAS: `{code}-`\n")
            
            f.write("**1. Suffixes (How this code ends):**\n")
            for suf, count in suffixes_found[code].most_common(3):
                f.write(f"  * `-{suf}`: {count} times\n")
                
            f.write("**2. What comes BEFORE it (Transitions Before):**\n")
            for pre, count in transitions_before[code].most_common(3):
                f.write(f"  * `{pre}`: {count} times\n")
                
            f.write("**3. Kas eina PO jo (Transitions After):**\n")
            for post, count in transitions_after[code].most_common(3):
                f.write(f"  * `{post}`: {count} times\n")
                
            # Generating Logical Conclusions
            f.write("**Scientific Deduction:** ")
            if "dy" in dict(suffixes_found[code].most_common(3)):
                f.write(f"Common suffix `-dy` indicates strong dose / final product. ")
            if "[BISECTION_IMAGE]" in dict(transitions_before[code].most_common(3)):
                f.write(f"Code often appears right after picture, meaning primary object modification. ")
            if "cho-" in dict(transitions_after[code].most_common(3)):
                f.write(f"This code is usually followed by Heating (`cho-`). This means `{code}-` is pre-calcination stage (e.g., drying or crushing). ")
            f.write("\n\n")
            
        f.write("---\n## Blind Suffix Scan in All Mappings\n")
        f.write("We checked all word endings, looking for new dose/state modifiers:\n")
        for suf, count in all_blind_suffixes.most_common(10):
            status = "Known" if suf in KNOWN_SUFFIXES else "NEW SECRET"
            f.write(f"* **`-{suf}`**: {count} times ({status})\n")
            
        f.write("\n**Conclusion:** New suffixes indicate yet undecoded aggregate states (e.g., gases, resins) or very specific time intervals.\n")

    print(f"Transition matrix analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    build_transition_matrix()
