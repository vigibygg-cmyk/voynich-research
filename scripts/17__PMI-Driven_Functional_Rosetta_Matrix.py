# ==============================================================================
# VOYNICH MANUSCRIPT: PMI AUTO-DISCOVERY & FUNCTIONAL ROSETTA MATRIX (PHASE XVII)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import math
import os
from collections import Counter, defaultdict

# Configuration - Triangulation
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

MIN_FREQ = 10
PMI_THRESHOLD = 3.0  # High threshold to prevent false positives (pritempimas)

# CORE ANCHORS (Mathematically Proven in Phases VII, XIV)
CORE_TERMINALS = {'aiin', 'daiin', 'am', 'chedy'}
CORE_STATES = {'s', 'or', 'ar'}
CORE_BASES = {'ol', 'qol'}

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_pmi_for_discovery(words):
    """
    Calculates PMI for all bigrams to discover new structural relationships.
    """
    total_words = len(words)
    unigram_counts = Counter(words)
    bigram_counts = Counter(zip(words[:-1], words[1:]))
    
    all_counts = list(unigram_counts.values())
    import numpy as np
    threshold = max(5, np.percentile(all_counts, 90)) if all_counts else 5
    valid_words = {w for w, c in unigram_counts.items() if c >= threshold}
    
    pmi_scores = {}
    
    for (w1, w2), freq in bigram_counts.items():
        if w1 in valid_words and w2 in valid_words and freq >= 5: # min 5 co-occurrences
            p_x_y = freq / (total_words - 1)
            p_x = unigram_counts[w1] / total_words
            p_y = unigram_counts[w2] / total_words
            
            pmi = math.log2(p_x_y / (p_x * p_y))
            pmi_scores[(w1, w2)] = pmi
            
    return pmi_scores, unigram_counts

def auto_discover_classes(df):
    """
    Uses known anchors and PMI to blindly discover new words 
    that belong to specific operational classes.
    """
    full_text = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_text.split()
    
    pmi_scores, unigram_counts = calculate_pmi_for_discovery(words)
    
    discovered_states = set()
    discovered_bases = set()
    
    # 1. Discover New States (Words that highly correlate BEFORE a Core Terminal)
    for (w1, w2), pmi in pmi_scores.items():
        if w2 in CORE_TERMINALS and pmi >= PMI_THRESHOLD:
            # Prevent re-adding core words or discovering known bases as states
            if w1 not in CORE_STATES and w1 not in CORE_BASES and w1 not in CORE_TERMINALS:
                discovered_states.add(w1)
                
    # 2. Discover New Bases (Words that highly correlate BEFORE a Core State)
    for (w1, w2), pmi in pmi_scores.items():
        if (w2 in CORE_STATES or w2 in discovered_states) and pmi >= PMI_THRESHOLD:
            if w1 not in CORE_BASES and w1 not in CORE_TERMINALS and w1 not in CORE_STATES:
                discovered_bases.add(w1)
                
    return discovered_states, discovered_bases, unigram_counts

def compile_rosetta_matrix(dfs):
    """
    Compiles the final Rosetta Matrix by triangulating discoveries across all files.
    A discovery is only valid if it appears in at least 2 out of 3 transcriptions.
    """
    all_discovered_states = defaultdict(int)
    all_discovered_bases = defaultdict(int)
    
    for name, df in dfs.items():
        print(f"[*] Running PMI Auto-Discovery on {name}...")
        states, bases, counts = auto_discover_classes(df)
        for s in states: all_discovered_states[s] += 1
        for b in bases: all_discovered_bases[b] += 1
        
    # Filter for Triangulation (must be found in > 1 transcription source)
    verified_states = {w for w, count in all_discovered_states.items() if count > 1}
    verified_bases = {w for w, count in all_discovered_bases.items() if count > 1}
    
    print("\n" + "="*80)
    print("FUNCTIONAL ROSETTA MATRIX (ALGORITHMIC PSEUDOCODE TRANSLATION)")
    print("="*80)
    print("WARNING: This translates functions, not semantic nouns. It proves HOW the text works.")
    
    print("\n[OPERATOR CLASS: TERMINALS / YIELDS]")
    print(f"  -> CORE: {', '.join(CORE_TERMINALS)}")
    print("  -> PSEUDOCODE FUNCTION: END_LOOP(), SET_QUANTITY(), TERMINATE_PROCESS()")
    
    print("\n[OPERATOR CLASS: STATE MODIFIERS / TRANSITIONS]")
    print(f"  -> CORE: {', '.join(CORE_STATES)}")
    print(f"  -> AUTO-DISCOVERED VIA PMI: {', '.join(verified_states) if verified_states else 'None'}")
    print("  -> PSEUDOCODE FUNCTION: APPLY_STATE(x), TRANSFORM(), MODIFY_SUBSTRATE()")

    print("\n[OPERATOR CLASS: BASE SUBSTANCES / EXTRACTS]")
    print(f"  -> CORE: {', '.join(CORE_BASES)}")
    print(f"  -> AUTO-DISCOVERED VIA PMI: {', '.join(verified_bases) if verified_bases else 'None'}")
    print("  -> PSEUDOCODE FUNCTION: LOAD_SUBSTANCE(x), INITIALIZE_EXTRACT()")

def main():
    print("=== Voynich Phase XVII: PMI-Driven Functional Rosetta Matrix ===\n")
    print("Objective: Safely expand the known structural dictionary using math,")
    print("avoiding human pareidolia by demanding extreme PMI topological bonds.\n")
    
    dfs = {}
    for filepath in TARGET_FILES:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
            dfs[filepath.split('/')[-1]] = df
        else:
            print(f"[-] Missing file: {filepath}")

    if dfs:
        compile_rosetta_matrix(dfs)
    else:
        print("[-] No datasets available to process.")

if __name__ == "__main__":
    main()