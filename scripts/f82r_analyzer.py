import os
import json
import re

MAPPING_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING\f82r_mapping.json"
CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
TARGET_FILES = ["Latin_Alchemy.txt", "English_Alchemy.txt"]
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_46_f82r_Analysis.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT",
    "qo": "POUR/FILTER",
    "cho": "HEAT",
    "daiin": "FILTER",
    "shol": "GRIND",
    "yt": "MIX",
    "chok": "DISTILL",
    "she": "SOAK/WASH",
    "ok": "ADD",
    "dar": "DRY",
    "ol": "BOIL",
    "chee": "STIR",
    "ot": "PROCESS",
    "dal": "CUT",
    "dol": "CRUSH",
    "dai": "WASH"
}

F82R_ENGLISH = {
    "1_POUR_FILTER": ["pour", "filter", "strain", "distill", "water", "aqua"],
    "2_EXTRACT": ["extract", "draw", "sublime"],
    "3_SOAK_WASH": ["soak", "wash", "bathe", "steep", "imbibe", "cleanse"],
    "4_ADD": ["add", "put", "inject"],
    "5_HEAT_BOIL": ["boil", "heat", "warm", "fire"]
}

F82R_LATIN = {
    "1_POUR_FILTER": ["funde", "cola", "percola", "distilla", "aqua", "balneo"],
    "2_EXTRACT": ["extrahe", "trahe", "sublima"],
    "3_SOAK_WASH": ["macera", "lava", "ablue", "infunde"],
    "4_ADD": ["adde", "mitte", "immitte"],
    "5_HEAT_BOIL": ["coque", "calefacere", "ebullire", "ignis"]
}

WINDOW_SIZE = 150 

def analyze_f82r():
    print("Skaitomas f82r mapping failas...")
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    text_blocks = data.get("text_blocks_mapping", [])
    
    sequence = []
    
    # Strict profile extraction
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
                        if context in ["Start", "Post-Gap"]: # Focusing only on bisections and starts
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
        flowchart = F82R_ENGLISH if "English" in filename else F82R_LATIN
        
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
        f.write("# Phase 46: Folio f82r Deep Analysis (Balneology and Pipes)\n\n")
        f.write("In this phase particularly complex page f82r is examined, where we see women in pools and red-blue striped cylindrical pipes. Applying Strict Morphology rule we extracted bisection commands and performed isomorphic search.\n\n")
        
        f.write("## 1. Operations Chain (Flowchart Profile)\n")
        f.write("Commands extracted only from line starts and continuous bisections (`<->`) right side (Post-Gap), where text directly hits the pipe:\n")
        
        counts = {}
        for s in sequence: counts[s] = counts.get(s, 0) + 1
        
        f.write(f"Dominant commands for f82r pipes and pools:\n")
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            f.write(f"* **{k}**: {v} times\n")
            
        f.write("\n## 2. Isomorphic Translation (Historical Recipe Matches)\n")
        f.write(f"Based on f82r profile (dominated by POUR, EXTRACT, SOAK, ADD), we scanned alchemy corpus.\n")
        f.write(f"**Found unique matches:** {len(valid_recipes)}\n\n")
        
        for i, recipe in enumerate(valid_recipes[:5]):
            f.write(f"### Atitikmuo `{recipe['file']}`\n")
            for step, kws in recipe["matches"].items():
                f.write(f"* **{step}**: {', '.join(kws)}\n")
            f.write(f"> **Tekstas:** {recipe['text']}\n\n")

if __name__ == "__main__":
    analyze_f82r()
