# ==============================================================================
# VOYNICH MANUSCRIPT: VISUAL CONTEXT EXTRACTION (PHASE VIII)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import random

# Configuration - Triangulation Enforced
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
SAMPLE_SIZE = 3 # We extract 3 samples from each file, total 9 samples per anchor

def deeply_clean_text(text):
    """Cleans text, but preserves physical illustration breaks."""
    text = str(text)
    
    # PRESERVE PHYSICAL BREAKS: Replace <-> before cleaning other tags
    text = text.replace('<->', ' drawingbreak ')
    
    # Standartinis valymas
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_visual_category(folio_str):
    """Assigns page to one of main manuscript categories (checking all sections)."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Unknown"
    num = int(match.group(1))
    
    if (1 <= num <= 66) or num == 87: return "Herbal (Plants/Roots)"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy (Stars/Cosmos)"
    elif 75 <= num <= 84: return "Balneology (Pools/Nymphs/Bio)"
    elif 88 <= num <= 102: return "Pharmaceutical (Containers/Jars)"
    elif 103 <= num <= 116: return "Recipes (Text Blocks/Stars)"
    else: return "Unknown"

def extract_prefix_context(df, prefix, source_name):
    """Extracts lines containing specified macro-operator (prefix)."""
    matching_lines = []
    for _, row in df.iterrows():
        text = str(row['Deep_Clean_Text'])
        if not text: continue
        
        words = text.split()
        if any(w.startswith(prefix) for w in words):
            cat = get_visual_category(row['Folio'])
            matching_lines.append((row['Locus'], cat, text))
            
    if not matching_lines:
        return
        
    random.seed(42) # To make results reproducible
    samples = random.sample(matching_lines, min(SAMPLE_SIZE, len(matching_lines)))
    
    for locus, cat, txt in samples:
        # Highlight search word
        highlighted_txt = re.sub(rf'\b({prefix}\w*)\b', r'>>\1<<', txt)
        # Restore illustration break
        highlighted_txt = highlighted_txt.replace("drawingbreak", "[---PICTURE_BREAK---]")
        
        print(f"    -> [{source_name}] [Folio: {locus}] [Visual: {cat}]")
        print(f"       Text: {highlighted_txt}\n")

def extract_chain_context(df, chain, source_name):
    """Extracts lines with exact hard syntactic chain."""
    chain_str = " ".join(chain)
    
    matching_lines = []
    for _, row in df.iterrows():
        text = str(row['Deep_Clean_Text'])
        if not text: continue
        
        if chain_str in text:
            cat = get_visual_category(row['Folio'])
            matching_lines.append((row['Locus'], cat, text))
            
    if not matching_lines:
        return
        
    random.seed(101) 
    samples = random.sample(matching_lines, min(SAMPLE_SIZE, len(matching_lines)))
    
    for locus, cat, txt in samples:
        # Highlight chain
        highlighted_txt = txt.replace(chain_str, f">>{chain_str}<<")
        highlighted_txt = highlighted_txt.replace("drawingbreak", "[---PICTURE_BREAK---]")
        
        print(f"    -> [{source_name}] [Folio: {locus}] [Visual: {cat}]")
        print(f"       Text: {highlighted_txt}\n")

def main():
    print("=== Voynich Phase VIII: Isomorphic Matrix Visual Decoding ===\n")
    print("OBJECTIVE: Blindly extract context for TF-IDF validated anchors across ALL sources and ALL sections.\n")
    
    # Load all files
    dfs = {}
    for filepath in TARGET_FILES:
        if os.path.exists(filepath):
            df = pd.read_csv(filepath)
            df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
            dfs[filepath.split('/')[-1]] = df
        else:
            print(f"[-] Missing file: {filepath}")

    if not dfs:
        return

    # 1. Test Recipe/Procedural Macro-Operator
    print(f"[*] EXTRACTING CONTEXT FOR PROCEDURAL MACRO-OPERATORS: 'lka-', 'lkc-'")
    for source_name, df in dfs.items():
        extract_prefix_context(df, "lka", source_name)
        extract_prefix_context(df, "lkc", source_name)
        
    # 2. Test Natural/Physical Entity Macro-Operators
    print(f"[*] EXTRACTING CONTEXT FOR NATURAL MACRO-OPERATORS: 'yto-', 'yp-'")
    for source_name, df in dfs.items():
        extract_prefix_context(df, "yto", source_name)
        extract_prefix_context(df, "yp", source_name)
        
    # 3. Test the Hard Syntactic Chain
    chain_target = ["ol", "s", "aiin"]
    print(f"[*] EXTRACTING CONTEXT FOR HARD SYNTACTIC CHAIN: 'ol -> s -> aiin'")
    for source_name, df in dfs.items():
        extract_chain_context(df, chain_target, source_name)
    
    print("======================================================================")
    print("EXTRACTION COMPLETE. Proceed to formulate the Ontological Dictionary Key.")
    print("======================================================================")

if __name__ == "__main__":
    main()