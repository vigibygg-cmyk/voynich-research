# ==============================================================================
# VOYNICH MANUSCRIPT: DIRECTIONAL FLOW & DEPENDENCY GRAPH (PHASE XV)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import random

# Configuration - Triangulation
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Blind SVD Clusters extracted directly from Phase XIV's Unsupervised K-Means Output
STATE_MODIFIERS = {'ar', 'or', 's', 'r', 'o', 'sar', 'char', 'd', 'tar', 'ches', 'sor', 'chos', 'cheos', 'lor', 'os'}
TERMINALS = {'daiin', 'ol', 'aiin', 'chedy', 'shedy', 'chey', 'dar', 'qokeey', 'qokeedy', 'al', 'qokain', 'qokedy', 'shey', 'qokaiin', 'dal'}

def deeply_clean_text(text):
    """Deeply cleans text of residual transcriber marks."""
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_directional_flow(words):
    """
    Calculates Markov transition frequencies between the predefined functional classes.
    Checks the asymmetry of the flow: A -> B versus B -> A.
    """
    flow_forward = 0  # [STATE] -> [TERMINAL]
    flow_backward = 0 # [TERMINAL] -> [STATE]
    
    for i in range(len(words) - 1):
        current_word = words[i]
        next_word = words[i + 1]
        
        # Check Forward Transition (Valid Algorithmic Sequence)
        if current_word in STATE_MODIFIERS and next_word in TERMINALS:
            flow_forward += 1
            
        # Check Backward Transition (Syntax Violation / Natural Language Bidirectionality)
        elif current_word in TERMINALS and next_word in STATE_MODIFIERS:
            flow_backward += 1
            
    total_transitions = flow_forward + flow_backward
    
    if total_transitions == 0:
        return 0, 0, 0.0, 0.0
        
    forward_pct = (flow_forward / total_transitions) * 100
    backward_pct = (flow_backward / total_transitions) * 100
    
    return flow_forward, flow_backward, forward_pct, backward_pct

def generate_hoax_words(words):
    """Shuffles words globally to destroy syntactic flow while preserving exact frequencies."""
    shuffled = words.copy()
    random.seed(42) # Seeded for reproducibility
    random.shuffle(shuffled)
    return shuffled

def process_file(filepath, is_hoax=False):
    """Executes the directional flow calculation for a given corpus."""
    if not os.path.exists(filepath):
        return
        
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_text = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_text.split()
    
    if is_hoax:
        source_name = "RANDOM_HOAX_BASELINE"
        words = generate_hoax_words(words)
    else:
        source_name = filepath.split('/')[-1]
        
    print(f"\n[*] ANALYZING DIRECTIONAL FLOW: [{source_name}]")
    
    fwd, bwd, fwd_pct, bwd_pct = calculate_directional_flow(words)
    
    if fwd + bwd == 0:
        print("    [-] Insufficient data to calculate transitions.")
        return
        
    print(f"    -> Forward Flow  [STATE -> TERMINAL]: {fwd:<4} occurrences ({fwd_pct:.2f}%)")
    print(f"    -> Backward Flow [TERMINAL -> STATE]: {bwd:<4} occurrences ({bwd_pct:.2f}%)")
    
    if fwd_pct > 80 and not is_hoax:
        print("    [!] CONCLUSION: Strict UNIDIRECTIONAL algorithmic graph confirmed.")
    elif is_hoax:
        print("    [i] BASELINE CONTROL: Note the destruction of flow asymmetry (approaches random chance).")

def main():
    print("=== Voynich Phase XV: Dependency Graph & Directional Flow Analysis ===\n")
    print("Objective: Mathematically test if operations are strictly 'closed' after a state change.")
    print("Testing clusters blindly isolated by the Phase XIV SVD algorithm.\n")
    
    # 1. Authentic Transcriptions (Triangulation)
    for filepath in TARGET_FILES:
        if os.path.exists(filepath):
            process_file(filepath)
        else:
            print(f"[-] Error: {filepath} not found.")
            
    # 2. Chaos Control Baseline
    if TARGET_FILES and os.path.exists(TARGET_FILES[0]):
        print("\n" + "="*70)
        print("[*] EXECUTING CHAOS CONTROL (RANDOM_HOAX_BASELINE)")
        print("="*70)
        process_file(TARGET_FILES[0], is_hoax=True)
        
    print("\n=================================================================")
    print("PHASE XV COMPLETE. Evaluate the directional asymmetry of the syntax.")
    print("=================================================================")

if __name__ == "__main__":
    main()