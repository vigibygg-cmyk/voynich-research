# ==============================================================================
# VOYNICH MANUSCRIPT: LABEL INVOCATION ENGINE (PHASE XXI)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import random
from collections import defaultdict, Counter

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def extract_root(word):
    """
    A simplified morphological stemmer to extract the core root of a label.
    Strips common procedural prefixes ('4', 'o', 'y') and suffixes ('9', 'am', 'ay').
    """
    if len(word) <= 3: return word
    
    root = word
    # Strip common prefixes observed by Emlyn-Jones and our algorithms
    for pref in ['4o', '4', 'o', 'y', 'q']:
        if root.startswith(pref) and len(root) > len(pref) + 2:
            root = root[len(pref):]
            break
            
    # Strip common terminals/suffixes
    for suf in ['daiin', 'aiin', 'am', 'ay', '9', 'edy', 'y']:
        if root.endswith(suf) and len(root) > len(suf) + 2:
            root = root[:-len(suf)]
            break
            
    return root

def process_file(filepath, is_hoax=False):
    if not os.path.exists(filepath): return
    
    df = pd.read_csv(filepath)
    source_name = "RANDOM_HOAX_BASELINE" if is_hoax else filepath.split('/')[-1]
    
    # Clean text
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    # Build folio mappings
    folio_paragraphs = defaultdict(list)
    folio_labels = defaultdict(list)
    
    for _, row in df.iterrows():
        folio = str(row['Folio'])
        locus = str(row['Locus'])
        text = str(row['Deep_Clean_Text'])
        
        if not text: continue
        
        words = text.split()
        
        if '@P' in locus:
            folio_paragraphs[folio].extend(words)
        elif '@L' in locus or '@I' in locus or '@T' in locus:
            folio_labels[folio].extend(words)
            
    if not folio_labels or not folio_paragraphs:
        print(f"    [-] Skipping {source_name}: No clear @P / @L separation found.")
        return

    if is_hoax:
        # Shuffle paragraphs across folios to break the local page correlation
        all_para_words = []
        for words in folio_paragraphs.values():
            all_para_words.extend(words)
        random.seed(42)
        random.shuffle(all_para_words)
        
        idx = 0
        for folio, words in folio_paragraphs.items():
            l = len(words)
            folio_paragraphs[folio] = all_para_words[idx:idx+l]
            idx += l

    total_labels_checked = 0
    total_labels_invoked = 0
    
    for folio, labels in folio_labels.items():
        paragraphs = folio_paragraphs.get(folio, [])
        if not paragraphs: continue
        
        # Convert paragraph words to a single string for fast substring matching
        # (This allows us to find the label root embedded in complex procedural words like 4okoe9)
        paragraph_text = " ".join(paragraphs)
        
        for label in labels:
            if len(label) < 3: continue # Ignore 1-2 letter noise
            
            root = extract_root(label)
            total_labels_checked += 1
            
            # Check if root is invoked in the paragraph text
            if root in paragraph_text:
                total_labels_invoked += 1

    if total_labels_checked == 0: return

    invocation_rate = (total_labels_invoked / total_labels_checked) * 100
    
    print(f"\n[*] ANALYZING LABEL-TO-PARAGRAPH INVOCATION: [{source_name}]")
    print(f"    -> Total Labels Analyzed: {total_labels_checked}")
    print(f"    -> Labels Actively Invoked in Same-Page Paragraphs: {total_labels_invoked}")
    print(f"    -> PAGE-LEVEL INVOCATION RATE: {invocation_rate:.2f}%")

def main():
    print("=== Voynich Phase XXI: Label-to-Paragraph Procedural Invocation ===\n")
    print("Objective: Mathematically prove Emlyn-Jones' (2022) hypothesis that labels")
    print("serve as base entities which are then modified with syntax in the main text.\n")
    
    for filepath in TARGET_FILES:
        process_file(filepath)
        
    if TARGET_FILES and os.path.exists(TARGET_FILES[0]):
        print("\n" + "="*70)
        print("[*] EXECUTING CHAOS CONTROL (SHUFFLED PARAGRAPHS)")
        print("="*70)
        process_file(TARGET_FILES[0], is_hoax=True)
        
    print("\n======================================================================")
    print("PHASE XXI COMPLETE.")
    print("======================================================================")

if __name__ == "__main__":
    main()