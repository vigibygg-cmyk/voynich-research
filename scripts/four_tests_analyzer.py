import os
import json
import re

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
CORPORA_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\historical_corpora"
TARGET_FILES = ["Latin_Alchemy.txt", "English_Alchemy.txt"]
OUTPUT_REPORT = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_51_Four_Hypothesis_Tests.md"

COMMAND_ROOTS = {
    "qok": "EXTRACT", "qo": "POUR", "cho": "HEAT", "daiin": "FILTER",
    "shol": "GRIND", "yt": "MIX", "chok": "DISTILL", "she": "SOAK",
    "ok": "ADD", "dar": "DRY", "ol": "BOIL", "chee": "STIR",
    "ot": "PROCESS", "dal": "CUT", "dol": "CRUSH", "dai": "WASH"
}

def load_mapping(folio):
    path = os.path.join(MAPPING_DIR, f"{folio}_mapping.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def analyze_f99v(data, f):
    f.write("## Test 1: f99v (Pharmacy roots and vessels)\n")
    f.write("**Hypothesis:** In Pharmacy section commands must change to microscopic doses / storage (e.g., DRY, PROCESS, GRIND).\n")
    
    text_blocks = data.get("text_blocks_mapping", [])
    commands_found = {}
    
    for block in text_blocks:
        for line in block.get("lines", []):
            raw_text = line.get("raw_text", "").replace("<->", " .B. ").replace("???", "")
            words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
            for i, word in enumerate(words):
                if not word or word == ".B.": continue
                for root, meaning in sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True):
                    if word.startswith(root) and (i == 0 or (i > 0 and words[i-1] == ".B.")):
                        commands_found[meaning] = commands_found.get(meaning, 0) + 1
                        break
                        
    f.write("**Rezultatai:**\n")
    if commands_found:
        for cmd, count in sorted(commands_found.items(), key=lambda x: x[1], reverse=True)[:5]:
            f.write(f"* **{cmd}**: {count} times\n")
        
        # Test if DRY/PROCESS/GRIND dominate over EXTRACT/DISTILL
        storage = commands_found.get("DRY", 0) + commands_found.get("PROCESS", 0) + commands_found.get("GRIND", 0)
        macro = commands_found.get("EXTRACT", 0) + commands_found.get("DISTILL", 0)
        f.write(f"\n*Saugiklio patikrinimas:* Saugojimo/Apdorojimo komandos ({storage}) vs Ekstrakcijos komandos ({macro}).\n")
    else:
        f.write("No commands found.\n")

def analyze_f76r(data, f):
    f.write("\n## Test 2: f76r (Balneology and Reverse Local Model)\n")
    f.write("**Hypothesis:** Nymph/pool labels on same page migrate into operational paragraphs as ingredients.\n")
    
    labels = []
    paragraphs_words = []
    
    for block in data.get("text_blocks_mapping", []):
        for line in block.get("lines", []):
            locus = line.get("locus", "")
            raw_text = line.get("raw_text", "").replace("<->", " .B. ").replace("???", "")
            words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
            
            if "L" in locus: # Labels (@Ln, @Lt, etc)
                labels.extend([w for w in words if len(w) > 2])
            elif "P" in locus: # Paragraphs
                paragraphs_words.extend([w for w in words if w != ".B."])
                
    f.write(f"Found isolated labels (Taxons): {len(set(labels))}\n")
    matches = []
    for label in set(labels):
        if label in paragraphs_words or any(label in w for w in paragraphs_words if len(w)>3):
            matches.append(label)
            
    f.write(f"Successfully tracked labels in operational text: {len(matches)}\n")
    if matches:
        f.write("*Tracked words:* " + ", ".join(matches) + "\n")

def analyze_f8v(data, f):
    f.write("\n## Test 3: f8v (Great Bisection Highway)\n")
    f.write("**Hypothesis:** Find the longest operation sequence and apply historical Sliding Window isomorphic translation.\n")
    
    sequence = []
    raw_sequence = []
    
    for block in data.get("text_blocks_mapping", []):
        for line in block.get("lines", []):
            raw_text = line.get("raw_text", "").replace("<->", " .B. ").replace("???", "")
            words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
            for i, word in enumerate(words):
                if not word or word == ".B.": continue
                for root, meaning in sorted(COMMAND_ROOTS.items(), key=lambda x: len(x[0]), reverse=True):
                    if word.startswith(root) and (i == 0 or (i > 0 and words[i-1] == ".B.")):
                        sequence.append(meaning)
                        raw_sequence.append(root)
                        break

    f.write(f"Extracted {len(sequence)} operation long chain:\n")
    f.write(" -> ".join(sequence) + "\n\n")
    
    # Izomorfinis bandymas
    if len(sequence) >= 5:
        f.write("**Attempting to find historical match (Top 5 steps)...**\n")
        f.write("Due to length we perform scan via full Sliding Window method (awaiting further modules).\n")
    else:
        f.write("Chain too short or bisections do not form a long highway.\n")

def analyze_f69v(data, f):
    f.write("\n## Test 4: f69v (Astronomical Ring)\n")
    f.write("**Hypothesis:** Star wheel and Radial labels encode time/astronomical cycles, without manufacturing commands.\n")
    
    radial = 0
    commands = 0
    for block in data.get("text_blocks_mapping", []):
        for line in block.get("lines", []):
            locus = line.get("locus", "")
            raw_text = line.get("raw_text", "").replace("<->", "").replace("???", "")
            words = [w.strip('.').strip('<>') for w in raw_text.split('.') if w.strip('.').strip('<>')]
            
            if "Ri" in locus or "R" in locus:
                radial += 1
            elif "P0" in locus:
                if words:
                    for root in COMMAND_ROOTS:
                        if words[0].startswith(root):
                            commands += 1
                            break
                            
    f.write(f"Found radial/ring labels: {radial}\n")
    f.write(f"Found usual manufacturing commands in paragraphs: {commands}\n")

def run_tests():
    print("Starting 4 strict falsification tests...")
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("# Strict Hypothesis Checking (f99v, f76r, f8v, f69v)\n\n")
        
        # Test 1
        d_f99v = load_mapping("f99v")
        if d_f99v: analyze_f99v(d_f99v, f)
        
        # Test 2
        d_f76r = load_mapping("f76r")
        if d_f76r: analyze_f76r(d_f76r, f)
        
        # Test 3
        d_f8v = load_mapping("f8v")
        if d_f8v: analyze_f8v(d_f8v, f)
            
        # Test 4
        d_f69v = load_mapping("f69v")
        if d_f69v: analyze_f69v(d_f69v, f)

    print(f"Testai baigti. Rezultatai: {OUTPUT_REPORT}")

if __name__ == "__main__":
    run_tests()
