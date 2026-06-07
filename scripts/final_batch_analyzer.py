import os
import json
import glob

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_48_Final_Batch_Analysis.md"

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

def analyze_final_batch():
    # Only focus on the newly uploaded files for this specific report
    target_folios = ["f49v", "f88r", "f105v", "f67r1", "f82r"]
    
    report_lines = [
        "# Phase 48: Final Analysis of New Mappings",
        "\nAnalyzed the last uploaded Pixel Mapping files: f49v (Botany), f88r (Pharmacy Vessels), f105v (Stars and Recipes). These pages were selected as particularly complex tests.\n"
    ]
    
    sorted_roots = sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for folio in target_folios:
        file_path = os.path.join(MAPPING_DIR, f"{folio}_mapping.json")
        if not os.path.exists(file_path): continue
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except: continue
        
        text_blocks = data.get("text_blocks_mapping", [])
        
        report_lines.append(f"\n## Folio: `{folio}`")
        
        bisection_count = 0
        sequence = []
        
        for block in text_blocks:
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "")
                has_bisection = "<->" in raw_text
                if has_bisection: bisection_count += 1
                
                clean_text = raw_text.replace("<->", " .B. ").replace("???", "")
                words = [w.strip('.').strip('<>') for w in clean_text.split('.') if w.strip('.').strip('<>')]
                
                for i, word in enumerate(words):
                    if not word or word == ".B.": continue
                    
                    for root, meaning in sorted_roots:
                        if word.startswith(root):
                            context = "Start" if i == 0 else ("Post-Gap" if i > 0 and words[i-1] == ".B." else "Mid")
                            if context in ["Start", "Post-Gap"]: # Strict logic
                                sequence.append(f"`{root}-` ({meaning})")
                            break
                            
        report_lines.append(f"* **Visual bisections (`<->`) count:** {bisection_count}")
        if sequence:
            report_lines.append(f"* **Extracted Strict Operation Sequence (Flowchart Profile):**")
            report_lines.append(" -> ".join(sequence[:20]) + ("..." if len(sequence) > 20 else ""))
            
            # Count operations
            counts = {}
            for s in sequence: counts[s] = counts.get(s, 0) + 1
            report_lines.append("\n* **Dominant operations on this page:**")
            for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                report_lines.append(f"  * {k}: {v} times")
        else:
            report_lines.append(f"* **No operations found.**")

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))

    print(f"Final analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_final_batch()
