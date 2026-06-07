import os
import re

CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
TARGET_FILES = ["Latin_Botany_Medicine.txt", "Latin_Alchemy.txt", "English_Alchemy.txt"]
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_44_Dual_Folio_Translation.md"

# F87v Profilis: FILTER/POUR -> ADD -> SOAK/EXTRACT -> BOIL -> STIR
F87V_LATIN = {
    "1_POUR_FILTER": ["cola", "funde", "percola", "exprime", "funda"],
    "2_ADD": ["adde", "mitte", "immitte", "adjice"],
    "3_SOAK_EXTRACT": ["macera", "infunde", "extrahe", "trahe"],
    "4_BOIL": ["coque", "ebullire", "fervefac", "coquatur"],
    "5_STIR": ["agita", "move", "misce", "tere"]
}
F87V_ENGLISH = {
    "1_POUR_FILTER": ["pour", "filter", "strain", "press", "empty"],
    "2_ADD": ["add", "put", "cast"],
    "3_SOAK_EXTRACT": ["soak", "steep", "extract", "draw", "imbibe"],
    "4_BOIL": ["boil", "seethe", "heat", "warm"],
    "5_STIR": ["stir", "mix", "agitate"]
}

# F103r Profilis: MIX/CUT -> POUR/WASH -> SOAK -> ADD -> DISTILL
F103R_LATIN = {
    "1_MIX_CUT": ["misce", "tere", "scinde", "frange", "trita"],
    "2_POUR_WASH": ["funde", "lava", "ablue", "purga"],
    "3_SOAK": ["macera", "infunde", "imbibe"],
    "4_ADD": ["adde", "mitte", "immitte"],
    "5_DISTILL": ["distilla", "destilla", "sublima"]
}
F103R_ENGLISH = {
    "1_MIX_CUT": ["mix", "cut", "chop", "pound", "grind", "bruise"],
    "2_POUR_WASH": ["pour", "wash", "cleanse", "purge"],
    "3_SOAK": ["soak", "steep", "infuse", "imbibe"],
    "4_ADD": ["add", "put"],
    "5_DISTILL": ["distill", "sublime", "ascend"]
}

WINDOW_SIZE = 120 # Wider window for more complex 5-step sequences

def search_recipe(flowchart_en, flowchart_lat, folio_name, words, filename, valid_recipes):
    flowchart = flowchart_en if "English" in filename else flowchart_lat
    
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
                    "folio": folio_name,
                    "file": filename,
                    "text": window_text,
                    "words": window_words,
                    "matches": matches
                })

def dual_translation():
    f87v_recipes = []
    f103r_recipes = []
    
    for filename in TARGET_FILES:
        filepath = os.path.join(CORPORA_DIR, filename)
        if not os.path.exists(filepath): continue
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        words = re.findall(r'\b\w+\b', content.lower())
        
        search_recipe(F87V_ENGLISH, F87V_LATIN, "f87v", words, filename, f87v_recipes)
        search_recipe(F103R_ENGLISH, F103R_LATIN, "f103r", words, filename, f103r_recipes)
            
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Etapas 44: Dvigubas Izomorfinis Vertimas (f87v ir f103r)\n\n")
        
        f.write("## 1. FOLIO F87V (Two plant roots and stem)\n")
        f.write(f"**Recipes found:** {len(f87v_recipes)}\n")
        f.write("**Searched chain:** POUR/FILTER -> ADD -> SOAK/EXTRACT -> BOIL -> STIR\n\n")
        for i, recipe in enumerate(f87v_recipes[:3]):
            f.write(f"### Atitikmuo `{recipe['file']}`\n")
            for step, kws in recipe["matches"].items():
                f.write(f"* **{step}**: {', '.join(kws)}\n")
            f.write(f"> **Tekstas:** {recipe['text']}\n\n")
            
        f.write("---\n## 2. FOLIO F103R (Stars and Recipes)\n")
        f.write(f"**Recipes found:** {len(f103r_recipes)}\n")
        f.write("**Searched chain:** MIX/CUT -> POUR/WASH -> SOAK -> ADD -> DISTILL\n\n")
        for i, recipe in enumerate(f103r_recipes[:3]):
            f.write(f"### Atitikmuo `{recipe['file']}`\n")
            for step, kws in recipe["matches"].items():
                f.write(f"* **{step}**: {', '.join(kws)}\n")
            f.write(f"> **Tekstas:** {recipe['text']}\n\n")

if __name__ == "__main__":
    dual_translation()
