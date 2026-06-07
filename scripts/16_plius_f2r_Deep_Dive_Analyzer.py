# ==============================================================================
# VOYNICH MANUSCRIPT: MICROSCOPIC f2r LINE ANALYSIS (DEEP DIVE)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os

# Configuration - Triangulation
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Ontological Key (Mathematically derived from Phases X-XIV)
# 1. Macro-Operators (The Taxonomic Skeleton / Signal)
MACRO_PROCEDURAL = ["lka", "lkc", "lky", "lk"]
MACRO_ENTITY = ["yto", "yp", "dyd", "sho", "cho", "chok", "ctho"] # Added 'cho/sho' from Phase 12 Herbal

# 2. Structural Operators (The Verbose Padding / Operational States)
STATE_MODIFIERS = ['s', 'shedy', 'or', 'ar', 'r', 'char', 'd', 'tar', 'ches', 'sor', 'chos', 'cheos', 'lor', 'os', 'chey']
BASE_STATES = ['ol', 'qol']
TERMINALS = ['aiin', 'daiin', 'am', 'chedy', 'dar', 'qokeey', 'qokeedy', 'al', 'qokain', 'qokedy', 'shey', 'qokaiin', 'dal', 'iin']

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def load_and_find_f2r(filepath):
    """Loads the dataset and extracts the first valid line from Folio f2r."""
    if not os.path.exists(filepath):
        return None, None
        
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    # Filter for folio f2r
    f2r_df = df[df['Folio'] == 'f2r'].copy()
    
    if f2r_df.empty:
        # Fallback: try matching locus string if Folio column is malformed
        f2r_df = df[df['Locus'].str.contains('f2r', na=False, case=False)].copy()
        
    if f2r_df.empty:
        return None, None
        
    # Get the first line that has actual text
    for _, row in f2r_df.iterrows():
        text = str(row['Deep_Clean_Text']).strip()
        if len(text) > 0:
            return row['Locus'], text
            
    return None, None

def naive_naibbe_parser(word):
    """
    Parses a word according to the Naibbe (Verbose Cipher) logic.
    Identifies if a word is part of the hidden "Skeleton" or just "Padding/Noise".
    """
    if any(word.startswith(root) for root in MACRO_PROCEDURAL + MACRO_ENTITY):
        return "[SIGNAL: Taxonomic Skeleton]"
    elif word in STATE_MODIFIERS or word in BASE_STATES or word in TERMINALS or any(word.endswith(t) for t in TERMINALS):
        return "[NOISE: Verbose Padding]"
    else:
        return "[UNRESOLVED / POTENTIAL SIGNAL]"

def paper_computer_parser(word):
    """
    Parses a word according to the Paper Computer (Algorithmic Logic).
    Identifies functional slots (Object -> State -> Terminal).
    """
    if any(word.startswith(root) for root in MACRO_PROCEDURAL):
        return "[COMMAND: Procedural Action]"
    elif any(word.startswith(root) for root in MACRO_ENTITY):
        return "[ENTITY: Botanical/Natural Object]"
    elif word in BASE_STATES:
        return "[BASE: Substrate / Extract]"
    elif word in STATE_MODIFIERS:
        return "[STATE: Operational Transition]"
    elif word in TERMINALS or any(word.endswith(t) for t in TERMINALS):
        return "[YIELD: Quantitative Dose / Closure]"
    else:
        return "[UNKNOWN VARIABLE]"

def analyze_line(source_name, locus, text):
    print(f"\n" + "="*80)
    print(f"[*] SOURCE: {source_name} | LOCUS: {locus}")
    print(f"    ORIGINAL TEXT: {text}")
    print("="*80)
    
    words = text.split()
    
    print("\n--- 1. NAIBBE (VERBOSE CIPHER) INTERPRETATION ---")
    print("Hypothesis: Most words are empty padding hiding a few real taxonomic roots.")
    signal_count = 0
    noise_count = 0
    
    for word in words:
        tag = naive_naibbe_parser(word)
        if "SIGNAL" in tag: signal_count += 1
        elif "NOISE" in tag: noise_count += 1
        print(f"    {word:<12} -> {tag}")
        
    total = len(words)
    print(f"    > SNR Breakdown: {signal_count} Skeleton words ({signal_count/total*100:.1f}%), {noise_count} Padding words ({noise_count/total*100:.1f}%)")

    print("\n--- 2. PAPER COMPUTER (ALGORITHMIC) INTERPRETATION ---")
    print("Hypothesis: Words are not padding, but rigid operational functions (Object->State->Dose).")
    
    for word in words:
        tag = paper_computer_parser(word)
        print(f"    {word:<12} -> {tag}")
        
    print("\n    [ALGORITHMIC SYNTAX FLOW]:")
    flow = " -> ".join([paper_computer_parser(w).split(':')[0].replace('[', '') for w in words])
    print(f"    {flow}")

def main():
    print("=== Voynich f2r Microscopic Algorithmic Parsing ===\n")
    print("Target: Extracting the first readable line from Folio f2r (Herbal Section)")
    print("and blindly applying our mathematical decoding models to it.\n")
    
    for filepath in TARGET_FILES:
        source_name = filepath.split('/')[-1]
        locus, text = load_and_find_f2r(filepath)
        
        if locus and text:
            analyze_line(source_name, locus, text)
        else:
            print(f"[-] Could not extract f2r data from {source_name}")

if __name__ == "__main__":
    main()