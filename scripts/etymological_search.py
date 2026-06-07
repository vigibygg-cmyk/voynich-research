import os
import re
from collections import Counter

CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
TARGET_FILES = ["Latin_Botany_Medicine.txt", "Latin_Alchemy.txt", "German_Botany_Medicine.txt"]
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_52_Etymological_Search.md"

# Tracked isolated [TAXON] words (ingredients) from f75v
TARGET_TAXONS = ["qokal", "otal", "okeey"]

# Phonetic hypotheses (Based on Matarrese and Alchemical specifics)
PHONETIC_MAPPINGS = {
    "qokal": [r"\balkali\b", r"\bkali\b", r"\bkal\b", r"\bkohl\b", r"\bcoal\b", r"\bcalx\b", r"\bcalc\w*"],
    "otal": [r"\botal\w*", r"\bodal\w*", r"\battal\w*", r"\bvitriol\w*", r"\bol\w*m\b", r"\badel\b"],
    "okeey": [r"\boche\w*", r"\baqua\b", r"\boke\w*", r"\bacetum\b", r"\boculus\b", r"\beiche\b"]
}

def etymological_search():
    print("Starting etymological / linguistic search...")
    
    results = {taxon: [] for taxon in TARGET_TAXONS}
    
    for filename in TARGET_FILES:
        filepath = os.path.join(CORPORA_DIR, filename)
        if not os.path.exists(filepath): continue
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().lower()
            
        for taxon, patterns in PHONETIC_MAPPINGS.items():
            for pattern in patterns:
                # Randame visus atitikmenis
                matches = re.finditer(pattern, content)
                for match in matches:
                    word = match.group(0)
                    # Take the context (window) around the word
                    start = max(0, match.start() - 60)
                    end = min(len(content), match.end() + 60)
                    context = content[start:end].replace('\n', ' ')
                    
                    results[taxon].append({
                        "word": word,
                        "file": filename,
                        "context": context
                    })
                    
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Phase 52: Etymological and Linguistic Search (Symbol Grounding)\n\n")
        f.write("As per user request we moved to EXACT word meanings search. We selected three best tracked ingredients (Taxons) from f75v page: `qokal`, `otal`, `okeey`. Applying Matarrese phonetic principles and alchemical vocabulary, we searched for phonetic and graphic matches in Latin and Old High German corpora.\n\n")
        
        for taxon in TARGET_TAXONS:
            f.write(f"## Tyrimo objektas: `{taxon}`\n")
            
            if taxon == "qokal":
                f.write("**Linguistic Hypothesis:** Voynich 'q' often acts as prefix. Remainder 'okal' phonetically perfectly matches 'Alkali' (Arabic al-qaly – plant ash salt) or Latin 'Calx' (lime). Our isomorphic translation f87v/f82r exactly showed tartar and salt extraction!\n\n")
            elif taxon == "otal":
                f.write("**Linguistic Hypothesis:** May be related to German 'Odal/Adel' (noble metal) or Latin 'Ol-' (Oleum - oil) or 'Vitriol'.\n\n")
            elif taxon == "okeey":
                f.write("**Linguistic Hypothesis:** Phonetically similar to 'Aqua' (water), 'Acetum' (vinegar) or German 'Eiche' (oak).\n\n")

            matches = results[taxon]
            f.write(f"**Found matches in historical texts:** {len(matches)}\n")
            
            # Counting most popular words
            word_counts = Counter([m["word"] for m in matches])
            f.write("**Most common phonetic matches:**\n")
            for w, c in word_counts.most_common(5):
                f.write(f"* `{w}`: {c} times\n")
                
            f.write("\n**Context examples (Top 3):**\n")
            # Selecting one example for the best words
            shown = 0
            for w, _ in word_counts.most_common(3):
                for m in matches:
                    if m["word"] == w:
                        f.write(f"> **{m['word']}** (from `{m['file']}`): ...{m['context']}...\n\n")
                        shown += 1
                        break
                if shown >= 3: break
            f.write("---\n")

    print(f"Etymological analysis complete. Report: {OUTPUT_REPORT}")

if __name__ == "__main__":
    etymological_search()
