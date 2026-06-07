import json
import os
import glob
from collections import defaultdict

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
REPORT_FILE = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_36_Cross_Folio_Validation.md"

# 12 Spagyric/Alchemical Operational Roots (from external theories & Vigslist)
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
    "chee": "STIR"
}

# Modifiers/Terminators (Yield States)
TERMINATOR_DOSE = {
    "dy": "YIELD: High Dose",
    "y": "YIELD: Standard Dose",
    "al": "STATE: Liquid",
    "or": "STATE: Solid/Powder",
    "am": "STATE: Gas/Vapor"
}

def analyze_folios():
    json_files = glob.glob(os.path.join(MAPPING_DIR, "*_mapping.json"))
    
    # Statistika
    folio_stats = {}
    total_commands_found = 0
    total_words_analyzed = 0
    
    # Locus pasiskirstymas
    locus_command_distribution = defaultdict(int)
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            continue
            
        folio_id = data.get("folio", os.path.basename(file_path))
        text_blocks = data.get("text_blocks_mapping", [])
        
        folio_stats[folio_id] = {
            "commands_matched": 0,
            "terminators_matched": 0,
            "bisections": 0,
            "labels": 0
        }
        
        for block in text_blocks:
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "")
                locus = line.get("locus", "")
                
                # Check bisections
                if "<->" in raw_text:
                    folio_stats[folio_id]["bisections"] += 1
                
                # Check if it's a label locus (@L)
                if "@L" in locus or "=L" in locus or "+L" in locus:
                    folio_stats[folio_id]["labels"] += 1
                
                # Clean text and split words
                clean_text = raw_text.replace("<->", ".").replace("???", "")
                words = [w.strip() for w in clean_text.split('.') if w.strip()]
                
                for i, word in enumerate(words):
                    total_words_analyzed += 1
                    is_command = False
                    
                    # Tikriname komandas (Roots)
                    for root in COMMAND_ROOTS:
                        if word.startswith(root):
                            folio_stats[folio_id]["commands_matched"] += 1
                            total_commands_found += 1
                            is_command = True
                            
                            # If it is first line word, write locus type
                            if i == 0:
                                locus_type = locus.split(',')[1].strip('>') if ',' in locus else "UNKNOWN"
                                locus_command_distribution[locus_type] += 1
                            break
                    
                    # Tikriname pabaigas (Terminators)
                    for term in TERMINATOR_DOSE:
                        if word.endswith(term):
                            folio_stats[folio_id]["terminators_matched"] += 1
                            break
                            
    # Generate report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Cross-Folio Pixel Mapping Validation\n\n")
        f.write("This test was done to avoid pseudoscience ('overfitting'). If 5-block 'Pasigraphic Engine' and 12 spagyric roots theory is correct, roots (e.g., `cho-`, `qok-`) must systematically repeat regardless if it is botany page (with roots), or balneology (with nymphs and pools).\n\n")
        
        f.write(f"**Total words analyzed:** {total_words_analyzed}\n")
        f.write(f"**Found [INITIATOR/COMMAND] matches:** {total_commands_found} ({round((total_commands_found/max(1, total_words_analyzed))*100, 2)}% of all words)\n\n")
        
        f.write("## 1. Rezultatai pagal Folio\n")
        f.write("| Folio ID | Bisections `<->` | Labels (@L) | Found Commands | Found Modifiers (Dose) |\n")
        f.write("|---|---|---|---|---|\n")
        for f_id, stats in folio_stats.items():
            f.write(f"| {f_id} | {stats['bisections']} | {stats['labels']} | {stats['commands_matched']} | {stats['terminators_matched']} |\n")
            
        f.write("\n## 2. Command Distribution by Loci (First line word)\n")
        f.write("Our theory posits that paragraph starts (`@P0`, `+P0`) are mostly command instructions, while labels (`@Lp`, `@Ln`) – ingredients (`[TAXON]`).\n")
        for loc, count in sorted(locus_command_distribution.items(), key=lambda x: x[1], reverse=True):
            f.write(f"* **{loc}**: {count} command roots\n")

    print(f"Cross-validation completed. Report: {REPORT_FILE}")

if __name__ == "__main__":
    analyze_folios()
