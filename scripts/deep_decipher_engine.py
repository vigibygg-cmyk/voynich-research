import json
import os
import re

# Nustatymai
MAPPING_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING\f1v_mapping.json"
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_36_f1v_Experimental_Decipherment.md"

# Spagyric / Pharmaceutical roots (Examples, based on external research)
COMMAND_ROOTS = {
    "qok": "EXTRACT (Tincture)",
    "qo": "POUR (Pour liquid)",
    "cho": "HEAT (Kaitinti/Virti)",
    "daiin": "FILTER (Filtruoti)",
    "shol": "GRIND (Smulkinti)",
    "yt": "MIX (Mix)",
    "chok": "DISTILL (Distiliuoti)"
}

# Modifikatoriai ir Priesagos (Terminators)
TERMINATOR_DOSE = {
    "dy": "YIELD: High Dose / Final Product",
    "y": "YIELD: Standard Dose",
    "al": "STATE: Liquid",
    "or": "STATE: Solid/Powder"
}

def parse_word(word):
    """
    Parses a single EVA word into the 5-block Pasigraphic format.
    """
    command = "UNKNOWN_PROCESS"
    dose = "UNKNOWN_YIELD"
    
    # Simple prefix/root extraction
    for root, meaning in COMMAND_ROOTS.items():
        if word.startswith(root):
            command = meaning
            break
            
    # Simple suffix extraction
    for suffix, meaning in TERMINATOR_DOSE.items():
        if word.endswith(suffix):
            dose = meaning
            break
            
    if command == "UNKNOWN_PROCESS" and dose == "UNKNOWN_YIELD":
        return f"DATA_TOKEN({word})"
        
    return f"[{command}] -> [BASE: {word}] -> [{dose}]"

def decipher_folio(mapping_path):
    print(f"Deciphering file: {mapping_path}")
    
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Klaida nuskaitant JSON: {e}")
        return
        
    folio_id = data.get("folio", "Unknown")
    visual_anchors = data.get("visual_anchors", {})
    text_blocks = data.get("text_blocks_mapping", [])
    
    report_lines = [
        f"# Phase 36 Experimental Decipherment: Folio {folio_id}",
        "---",
        "**Theoretical Basis:** Pasigraphic Instruction Engine (5 Block Syntax) + Pharmaceutical Loci",
        ""
    ]
    
    report_lines.append("## 1. Identifikuoti Vizualiniai Inkarai ([TAXON] Kontekstas)")
    for anchor, details in visual_anchors.items():
        report_lines.append(f"* **{anchor}**: {details.get('description', '')}")
        
    report_lines.append("\n## 2. Instructions (Flowchart) Decipherment by Locus")
    
    for block in text_blocks:
        block_id = block.get("block_id", "Unknown Block")
        report_lines.append(f"\n### Blokas: {block_id}")
        
        for line_data in block.get("lines", []):
            locus = line_data.get("locus", "")
            raw_text = line_data.get("raw_text", "")
            interaction = line_data.get("interaction", "None")
            
            # Patikriname bisekcijas
            has_bisection = "<->" in raw_text
            
            report_lines.append(f"\n**Lokusas:** `{locus}`")
            report_lines.append(f"> **Originalus Tekstas:** {raw_text}")
            if has_bisection:
                report_lines.append(f"> **Visual Bisection:** Yes. Text avoids visual anchor (Modifier: Space barrier).")
                
            # Analyze first word as [INITIATOR/COMMAND]
            words = raw_text.split('.')
            if words:
                first_word = words[0].strip()
                translation = parse_word(first_word)
                report_lines.append(f"> **Dekoduota Instrukcija:** `{translation}`")
                
    # Save report
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("\n".join(report_lines))
        
    print(f"Decipherment report generated: {OUTPUT_REPORT}")

if __name__ == "__main__":
    decipher_folio(MAPPING_FILE)
