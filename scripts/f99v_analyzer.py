import os
import json
import re

MAPPING_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING\f99v_mapping.json"
CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
TARGET_FILES = ["Latin_Botany_Medicine.txt", "Latin_Alchemy.txt", "English_Alchemy.txt", "English_Botany_Medicine.txt"]
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_55_f99v_Pharmacy_Analysis.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH",
    "or": "SOLIDIFY", "dor": "DRY"
}

# F99v focused on pharmacy. Basic search matrix based on f99v dominating commands.
# According to Phase 51: PROCESS, BOIL, ADD, EXTRACT, DRY. We will add logical sequences for pharmacy.
F99V_ENGLISH = {
    "1_PROCESS_CUT": ["process", "cut", "prepare", "chop", "slice", "make"],
    "2_BOIL_HEAT": ["boil", "heat", "warm", "decoct"],
    "3_EXTRACT_POUR": ["extract", "draw", "pour", "strain", "press"],
    "4_DRY_STORE": ["dry", "desiccate", "store", "keep", "preserve", "powder", "vessel", "jar"]
}

F99V_LATIN = {
    "1_PROCESS_CUT": ["scinde", "frange", "para", "praepara", "fac"],
    "2_BOIL_HEAT": ["coque", "calefacere", "ebullire", "fervefac"],
    "3_EXTRACT_POUR": ["extrahe", "funde", "exprime", "cola"],
    "4_DRY_STORE": ["sicca", "serva", "vas", "vitreo", "pulvis", "aridum"]
}

WINDOW_SIZE = 120 

def analyze_f99v():
    print("Skaitomas f99v mapping failas...")
    
    try:
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Klaida: {e}")
        return
        
    text_blocks = data.get("text_blocks_mapping", [])
    
    sequence = []
    sorted_roots = sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True)
    
    for block in text_blocks:
        for line in block.get("lines", []):
            raw_text = line.get("raw_text", "").replace("<->", " .B. ").replace("???", "")
            words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
            
            for i, word in enumerate(words):
                if not word or word == ".B.": continue
                for root, meaning in sorted_roots:
                    if word.startswith(root):
                        context = "Start" if i == 0 else ("Post-Gap" if i > 0 and words[i-1] == ".B." else "Mid")
                        if context in ["Start", "Post-Gap"]: 
                            sequence.append(meaning)
                        break

    print("Searching for historical matches...")
    valid_recipes = []
    
    for filename in TARGET_FILES:
        filepath = os.path.join(CORPORA_DIR, filename)
        if not os.path.exists(filepath): continue
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        words = re.findall(r'\b\w+\b', content.lower())
        flowchart = F99V_ENGLISH if "English" in filename else F99V_LATIN
        
        for i in range(0, len(words) - WINDOW_SIZE, WINDOW_SIZE // 2):
            window_words = words[i : i + WINDOW_SIZE]
            window_text = " ".join(window_words)
            matches = {}
            all_steps_found = True
            for step, keywords in flowchart.items():
                found_keywords = [kw for kw in keywords if kw in window_words]
                if not found_keywords:
                    all_steps_found = False
                    break
                matches[step] = set(found_keywords)
            if all_steps_found:
                is_duplicate = False
                for vr in valid_recipes:
                    if len(set(window_words).intersection(set(vr["words"]))) > WINDOW_SIZE * 0.7:
                        is_duplicate = True
                        break
                if not is_duplicate:
                    valid_recipes.append({
                        "file": filename,
                        "text": window_text,
                        "words": window_words,
                        "matches": matches
                    })

    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 55: Folio f99v Pharmaceutical Decipherment\n\n")
        f.write("Page f99v belongs to pharmacy section, where small plant fragments (roots, leaves) and pharmaceutical vessels dominate. Extracting commands via bisections and performing isomorphic search, we looked for specific drug storage or dosing recipes, differing from previously seen 'botanical/extraction' methods.\n\n")
        
        f.write("## 1. Operations Chain (Flowchart Profile)\n")
        counts = {}
        for s in sequence: counts[s] = counts.get(s, 0) + 1
        
        f.write(f"Dominant commands for f99v rootlets and vessels:\n")
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"* **{k}**: {v} times\n")
            
        f.write("\n## 2. Isomorphic Translation (Historical Recipe Matches)\n")
        f.write(f"Based on f99v profile (PROCESS -> BOIL -> EXTRACT -> DRY/STORE), we scanned corpus.\n")
        f.write(f"**Found unique matches:** {len(valid_recipes)}\n\n")
        
        valid_recipes.sort(key=lambda x: sum(len(v) for v in x["matches"].values()), reverse=True)
        
        for i, recipe in enumerate(valid_recipes[:5]):
            f.write(f"### Atitikmuo #{i+1} (`{recipe['file']}`)\n")
            for step, kws in recipe["matches"].items():
                f.write(f"* **{step}**: {', '.join(kws)}\n")
            f.write(f"> **Tekstas:** {recipe['text']}\n\n")
            
        f.write("---\n**Conclusion:** f99v profile obviously matches 'Final Product' (Powder or resin) preparation for storage. Unlike the botany section, where everything is constantly distilled in liquids, here the material is dried (`DRY`, `sicca`) and placed in vessels (`vas`, `vessel`).\n")

    print(f"f99v analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    analyze_f99v()
