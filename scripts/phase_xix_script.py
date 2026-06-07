# VOYNICH MANUSCRIPT: LABEL VS. PARAGRAPH STRUCTURAL DIVERGENCE (PHASE XIX)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Structural Functional Operators (Derived from Phase XIV & XVI)
# These represent the "Operational Syntax" or "Padding"
FUNCTIONAL_OPERATORS = {
    'daiin', 'ol', 'aiin', 'chedy', 'shedy', 'chey', 'dar', 'qokeey', 'qokeedy', 
    'al', 'qokain', 'qokedy', 'shey', 'qokaiin', 'dal', 'am', 'iin', # Terminals / Bases
    'ar', 'or', 's', 'r', 'o', 'sar', 'char', 'd', 'tar', 'ches', 'sor', 'chos', 'cheos', 'lor', 'os' # Modifiers
}

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_snr(words):
    """Calculates the percentage of Structural Operators (Noise) vs. Taxonomic Roots (Signal)."""
    total_words = len(words)
    if total_words == 0:
        return 0.0, 0.0
        
    functional_count = sum(1 for w in words if w in FUNCTIONAL_OPERATORS)
    signal_count = total_words - functional_count
    
    functional_pct = (functional_count / total_words) * 100
    signal_pct = (signal_count / total_words) * 100
    
    return signal_pct, functional_pct

def analyze_file(filepath):
    if not os.path.exists(filepath):
        return
        
    df = pd.read_csv(filepath)
    source_name = filepath.split('/')[-1]
    
    print(f"\n[*] ANALYZING FILE: [{source_name}]")
    
    paragraphs_words = []
    labels_words = []
    
    for _, row in df.iterrows():
        locus = str(row['Locus'])
        text = str(row['Clean_Text'])
        
        # Determine if it's a paragraph (@P) or label (@L, @I, @Title)
        # Assuming @P means paragraph and @L/etc means isolated label based on standard IVTFF
        if '@P' in locus:
            clean = deeply_clean_text(text)
            if clean: paragraphs_words.extend(clean.split())
        elif '@L' in locus or '@I' in locus or '@T' in locus:
            clean = deeply_clean_text(text)
            if clean: labels_words.extend(clean.split())
            
    # If the exact locus markup isn't present, try heuristic based on word count
    if not paragraphs_words and not labels_words:
        print("    [!] Standard @P/@L locus tags not found. Using heuristic (Length > 3 = Paragraph).")
        for _, row in df.iterrows():
            clean = deeply_clean_text(str(row['Clean_Text']))
            words = clean.split()
            if len(words) > 3:
                paragraphs_words.extend(words)
            elif len(words) > 0:
                labels_words.extend(words)
                
    total_p = len(paragraphs_words)
    total_l = len(labels_words)
    
    print(f"    -> Extracted {total_p} words from Paragraphs (@P).")
    print(f"    -> Extracted {total_l} words from Labels (@L).")
    
    if total_p > 0 and total_l > 0:
        p_signal, p_noise = calculate_snr(paragraphs_words)
        l_signal, l_noise = calculate_snr(labels_words)
        
        print("\n    [PARAGRAPHS (@P) - Operational Syntax Expected]")
        print(f"       -> Signal (Taxonomic Nouns): {p_signal:.2f}%")
        print(f"       -> Structural Syntax (Padding): {p_noise:.2f}%")
        
        print("\n    [LABELS (@L) - Pure Entities Expected]")
        print(f"       -> Signal (Taxonomic Nouns): {l_signal:.2f}%")
        print(f"       -> Structural Syntax (Padding): {l_noise:.2f}%")
        
        drop_ratio = p_noise / l_noise if l_noise > 0 else float('inf')
        print(f"\n    [!] CONCLUSION: Structural syntax drops by a factor of {drop_ratio:.2f}x in Labels.")

def main():
    print("=== Voynich Phase XIX: Label vs. Paragraph Structural Divergence ===\n")
    print("Hypothesis: If Voynich is an 'Instruction Machine', isolated labels will lack")
    print("the procedural syntax (terminals/states) required in operational paragraphs.\n")
    
    for filepath in TARGET_FILES:
        analyze_file(filepath)
        
    print("\n======================================================================")
    print("PHASE XIX COMPLETE.")
    print("======================================================================")

if __name__ == "__main__":
    main()
# ==============================================================================