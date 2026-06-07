import os
import re

CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
TARGET_FILES = ["Latin_Botany_Medicine.txt", "Latin_Alchemy.txt", "English_Alchemy.txt"]
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_41_Isomorphic_Translation.md"

VOYNICH_FLOWCHART_LATIN = {
    "1_MIX": ["misce", "tere", "trita", "mista", "commixta", "contere"],     
    "2_HEAT": ["calefacere", "ignis", "coque", "coquatur", "fervefac", "calore"], 
    "3_POUR": ["funde", "cola", "exprime", "infunde", "percola"],             
    "4_SOLID": ["pulvis", "sicca", "aridum", "pulverem", "cinerem"]             
}

VOYNICH_FLOWCHART_ENGLISH = {
    "1_MIX": ["mix", "grind", "mingle", "pound", "stamp", "bruise"],     
    "2_HEAT": ["heat", "fire", "boil", "seethe", "warm", "burn"], 
    "3_POUR": ["pour", "filter", "strain", "press", "distill"],             
    "4_SOLID": ["powder", "dry", "dust", "ashes", "solid"]             
}

WINDOW_SIZE = 80 # Increase window to 80 words, considering medieval syntax

def search_isomorphic_recipes():
    valid_recipes = []
    
    for filename in TARGET_FILES:
        filepath = os.path.join(CORPORA_DIR, filename)
        if not os.path.exists(filepath): continue
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        words = re.findall(r'\b\w+\b', content.lower())
        
        flowchart = VOYNICH_FLOWCHART_ENGLISH if "English" in filename else VOYNICH_FLOWCHART_LATIN
        
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
        f.write("# Phase 41: Extremely Cautious Isomorphic Translation (Extended Corpus)\n\n")
        f.write(f"Scanned files: {', '.join(TARGET_FILES)}. Window: {WINDOW_SIZE} words.\n\n")
        f.write(f"**Found unique 80-word recipes with identical f1v logical sequence:** {len(valid_recipes)}\n\n")
        
        if valid_recipes:
            for i, recipe in enumerate(valid_recipes[:10]):
                f.write(f"### {i+1}. Atitikmuo Korpuse: `{recipe['file']}`\n")
                f.write("**Identified operation chain:**\n")
                for step, kws in recipe["matches"].items():
                    f.write(f"* **{step}**: {', '.join(kws)}\n")
                f.write(f"\n> **Excerpt:**\n> {recipe['text']}\n\n")
        else:
            f.write("Failed to find a single recipe.\n")

if __name__ == "__main__":
    search_isomorphic_recipes()
