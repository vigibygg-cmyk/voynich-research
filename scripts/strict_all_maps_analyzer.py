import os
import json
import glob

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_43_Strict_All_Maps_Analysis.md"

# Strict command roots (must be at the BEGINNING of the word)
COMMAND_ROOTS = {
    "qok": "EXTRACT",
    "qo": "POUR",
    "cho": "HEAT",
    "daiin": "FILTER",
    "shol": "GRIND",
    "yt": "MIX",
    "chok": "DISTILL",
    "she": "SOAK",
    "ok": "ADD",
    "dar": "DRY",
    "ol": "BOIL",
    "chee": "STIR",
    "ot": "PROCESS",
    "dal": "CUT",
    "dol": "CRUSH",
    "dai": "WASH"
}

def analyze_all_maps():
    json_files = glob.glob(os.path.join(MAPPING_DIR, "*_mapping.json"))
    
    report_lines = [
        "# Phase 43: Strict Isomorphic Analysis of All Mappings",
        "\nThis report analyzes all available Pixel Mapping files applying a STRICT morphological rule: a command (verb) is only present when the operational root is at the **beginning** of the word (prefix). Words containing these syllables in the middle (e.g., 'ycheockhy') are not treated as carriers of that command.\n"
    ]
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            continue
            
        folio_id = data.get("folio", os.path.basename(file_path))
        text_blocks = data.get("text_blocks_mapping", [])
        
        folio_sequence = []
        bisection_count = 0
        
        for block in text_blocks:
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "")
                locus = line.get("locus", "")
                
                # Ar tai bisekcija?
                has_bisection = "<->" in raw_text
                if has_bisection:
                    bisection_count += 1
                    
                # Analyzing all words, but especially interested in first words of line and after bisection
                clean_text = raw_text.replace("<->", " .B. ").replace("???", "")
                words = [w.strip('.').strip('<>') for w in clean_text.split(' ') if w.strip('.').strip('<>')]
                
                for i, word in enumerate(words):
                    if not word or word == ".B.": continue
                    
                    # Searching for strict prefix
                    for root, meaning in COMMAND_ROOTS.items():
                        if word.startswith(root):
                            context = "Start_of_Line" if i == 0 else "Mid_Line"
                            if i > 0 and words[i-1] == ".B.":
                                context = "Post_Bisection"
                                
                            folio_sequence.append(f"[{meaning} ({root})] -> {word} ({context})")
                            break # finding the longest match, so COMMAND_ROOTS must be sorted from longest. Python dict keeps order 3.7+
                            # To be precise, we sort by length (done in logic)
                            
    # Now need to check every file again with sorted keys
    sorted_roots = sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    report_lines.append(f"Analyzed files: {len(json_files)}")
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
        
        folio_id = data.get("folio", os.path.basename(file_path))
        text_blocks = data.get("text_blocks_mapping", [])
        
        report_lines.append(f"\n## Folio: `{folio_id}`")
        
        bisection_count = 0
        sequence = []
        
        for block in text_blocks:
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "")
                has_bisection = "<->" in raw_text
                if has_bisection: bisection_count += 1
                
                clean_text = raw_text.replace("<->", " .B. ").replace("???", "")
                words = [w.strip('.').strip('<>') for w in clean_text.split('.') if w.strip('.').strip('<>')]
                
                # Splitting by dots (EVA words)
                
                for i, word in enumerate(words):
                    if not word or word == ".B.": continue
                    
                    for root, meaning in sorted_roots:
                        if word.startswith(root):
                            context = "Start" if i == 0 else ("Post-Gap" if i > 0 and words[i-1] == ".B." else "Mid")
                            sequence.append(f"`{root}-` ({meaning}) [{context}]")
                            break
                            
        report_lines.append(f"* **Visual bisections (`<->`) count:** {bisection_count}")
        if sequence:
            report_lines.append(f"* **Extracted operation sequence (Flowchart Profile):**")
            # Showing first 15 operations
            report_lines.append(" -> ".join(sequence[:15]) + ("..." if len(sequence) > 15 else ""))
        else:
            report_lines.append(f"* **No operations found.** (Might be just labels or different structure text).")

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    print(f"Strict analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_all_maps()
