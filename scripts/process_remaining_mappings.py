import os
import json
from collections import Counter

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_63_Remaining_Mappings_Analysis.md"

TARGET_FILES = ["f85r1_mapping.json", "f86v3_mapping.json", "f86v4_mapping.json", "f86v5_mapping.json", "f86v6_mapping.json", "fRos_mapping.json"]

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH",
    "or": "SOLIDIFY", "dor": "DRY"
}

def analyze_remaining():
    print("Analyzing remaining mapping files...")
    sorted_roots = sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 63: Remaining 'Rosettes' Mappings Analysis\n\n")
        f.write("As per user request, we scanned all remaining uploaded 6-page foldout (Rosettes) JSON files. Goal: determine if manufacturing (alchemical) commands exist in other rosette parts, or this whole foldout is purely cosmological/philosophical map (without manufacturing instructions).\n\n")
        
        for filename in TARGET_FILES:
            filepath = os.path.join(MAPPING_DIR, filename)
            if not os.path.exists(filepath):
                continue
                
            try:
                with open(filepath, 'r', encoding='utf-8') as jf:
                    data = json.load(jf)
            except Exception as e:
                f.write(f"Klaida skaitant {filename}: {e}\n")
                continue
                
            folio_id = data.get("folio", filename)
            text_blocks = data.get("text_blocks_mapping", [])
            
            total_words = 0
            command_hits = Counter()
            
            for block in text_blocks:
                for line in block.get("lines", []):
                    raw_text = line.get("raw_text", "").replace("<->", " .B. ").replace("???", "")
                    words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
                    
                    for i, word in enumerate(words):
                        if not word or word == ".B.": continue
                        total_words += 1
                        
                        # Checking only line starts (or after bisection)
                        context = "Start" if i == 0 else ("Post-Gap" if i > 0 and words[i-1] == ".B." else "Mid")
                        if context in ["Start", "Post-Gap"]:
                            for root, meaning in sorted_roots:
                                if word.startswith(root):
                                    command_hits[meaning] += 1
                                    break
                                    
            f.write(f"## Folio: `{folio_id}`\n")
            f.write(f"* **Analyzed words:** {total_words}\n")
            
            if command_hits:
                f.write(f"* **Found Manufacturing Commands:**\n")
                for cmd, count in command_hits.most_common():
                    f.write(f"  * `{cmd}`: {count} times\n")
            else:
                f.write(f"* **Manufacturing Commands:** 0. (This confirms non-operational status).\n")
                
        f.write("\n---\n**General Conclusion:** Based on command frequency, we can see if certain rosettes act as 'reactors' (have manufacturing commands), or if they are just part of a macro-map, similar to f85r2.\n")

    print(f"Analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_remaining()
