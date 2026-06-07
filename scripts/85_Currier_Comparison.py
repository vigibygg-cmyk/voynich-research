import os
import sys
import collections

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# This script implements Phase 82, Hypothesis C: Currier A vs B "Code Versions" comparison.
# We look for whether A and B use the same syntax rules (prefixes/suffixes).

TRANSCRIPTION_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Transkript\RF1b-er.txt"

# Hardest part - recognize A and B languages. In RF transcription it is usually marked by '$L=A' or '$L=B' 
# in page header. If none - use standard historical division by page numbers.
# Bendrai priimta (nors supaprastintai): Herbal A yra daugiausia Quire 1-8. Herbal B yra daugiausia Quire 9+.
# But we will check file tags directly.

def analyze_currier_languages():
    if not os.path.exists(TRANSCRIPTION_FILE):
        print(f"Klaida: Nerastas failas {TRANSCRIPTION_FILE}")
        return

    currier_a_words = []
    currier_b_words = []
    
    current_language = "UNKNOWN"
    
    # Hardcoding a few known A and B pages for checking if the file lacks tags
    # A kalba (paprastai f1-f24)
    # B kalba (paprastai farmacija f88-f116, bio f75-f84)
    known_a_folios = ['f1v', 'f2r', 'f2v', 'f3r', 'f3v', 'f4r', 'f4v', 'f5r']
    known_b_folios = ['f75r', 'f75v', 'f76r', 'f88r', 'f88v', 'f89r', 'f100r', 'f102r']

    print(f"Skaitomas failas: {TRANSCRIPTION_FILE}")
    
    with open(TRANSCRIPTION_FILE, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            # Searching for language tag (if any) e.g. <f1v> <! $Q=A $L=A
            if line.startswith('<f') and '<!' in line:
                if '$L=A' in line:
                    current_language = "A"
                elif '$L=B' in line:
                    current_language = "B"
                else:
                    current_language = "UNKNOWN"
                continue
            
            # If line is textual (starts with <f)
            if line.startswith('<f') and current_language in ["A", "B"]:
                # Remove the locus tag (e.g. <f1v.1,@P0>)
                text_part = line.split('>', 1)[1] if '>' in line else line
                # Very simple cleaning: take words
                words = text_part.replace('.', ' ').replace(',', ' ').replace('<->', ' ').split()
                clean_words = [w for w in words if w.isalpha() and len(w) > 2] # Only real words
                
                if current_language == "A":
                    currier_a_words.extend(clean_words)
                else:
                    currier_b_words.extend(clean_words)

    print(f"\nCollected words:")
    print(f"Currier A (Pvz. Herbal pradiniai): {len(currier_a_words)}")
    print(f"Currier B (Pvz. Bio/Pharma sekcijos): {len(currier_b_words)}")
    
    if len(currier_a_words) == 0 or len(currier_b_words) == 0:
         print("ERROR: Failed to separate Currier A and B languages from file. Better locus mapping needed.")
         return
         
    # Analysis: Most frequent prefixes and Suffixes
    def get_affixes(words, length=2):
        prefixes = collections.Counter([w[:length] for w in words if len(w) > length])
        suffixes = collections.Counter([w[-length:] for w in words if len(w) > length])
        return prefixes, suffixes
        
    a_pref, a_suff = get_affixes(currier_a_words, 2)
    b_pref, b_suff = get_affixes(currier_b_words, 2)
    
    print("\n## TOP 10 Prefixes Comparison")
    print(f"| Position | Currier A | Frequency A | Currier B | Frequency B |")
    print(f"|-------|-----------|------------|-----------|------------|")
    top_a_p = a_pref.most_common(10)
    top_b_p = b_pref.most_common(10)
    for i in range(10):
        print(f"| {i+1} | `{top_a_p[i][0]}-` | {top_a_p[i][1]} | `{top_b_p[i][0]}-` | {top_b_p[i][1]} |")

    print("\n## TOP 10 Suffixes Comparison")
    print(f"| Position | Currier A | Frequency A | Currier B | Frequency B |")
    print(f"|-------|-----------|------------|-----------|------------|")
    top_a_s = a_suff.most_common(10)
    top_b_s = b_suff.most_common(10)
    for i in range(10):
        print(f"| {i+1} | `-{top_a_s[i][0]}` | {top_a_s[i][1]} | `-{top_b_s[i][0]}` | {top_b_s[i][1]} |")

    # Unique markers: What is only A, but not B?
    def find_unique(counter1, counter2, threshold=50):
        unique = []
        for item, count in counter1.items():
            if count > threshold and counter2[item] < count * 0.1: # at least 10 times rarer in other language
                unique.append((item, count, counter2[item]))
        return sorted(unique, key=lambda x: x[1], reverse=True)
        
    print("\n## Dialect Differences (Code Version Changes)")
    a_unique_pref = find_unique(a_pref, b_pref, 30)
    b_unique_pref = find_unique(b_pref, a_pref, 30)
    
    print("\n**Characteristic only to Currier A (Old pages):**")
    for item, c1, c2 in a_unique_pref[:5]: print(f"- Prefix `{item}-` (Found A: {c1}, B: {c2})")
    
    print("\n**Characteristic only to Currier B (Pharmacy/Bio):**")
    for item, c1, c2 in b_unique_pref[:5]: print(f"- Prefix `{item}-` (Found B: {c1}, A: {c2})")

analyze_currier_languages()
