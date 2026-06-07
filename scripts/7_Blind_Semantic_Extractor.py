# ==============================================================================
# VOYNICH MANUSCRIPT: BLIND SEMANTIC EXTRACTION VIA TF-IDF (PHASE VII)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import math
import random
import numpy as np
from collections import defaultdict, Counter

# Configuration
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
TOP_N_PREFIXES = 5     # Number of top unique prefixes to extract per section

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_visual_category(folio_str):
    """Maps a folio string to its accepted visual illustration category."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Unknown"
    num = int(match.group(1))
    
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 88 <= num <= 102: return "Pharmaceutical"
    elif 103 <= num <= 116: return "Recipes"
    else: return "Unknown"

def extract_prefixes(words):
    """Extracts 2-to-3 character prefixes from words."""
    prefixes = []
    for w in words:
        if len(w) >= 3:
            prefixes.append(w[:3])
        if len(w) >= 2:
            prefixes.append(w[:2])
    return prefixes

def calculate_tfidf(section_texts):
    """
    Calculates TF-IDF for prefixes across different sections.
    """
    # 1. Global prefix frequencies
    global_counts = Counter()
    for prefs in section_texts.values():
        global_counts.update(prefs)
        
    counts = list(global_counts.values())
    if not counts: return {}
    
    # Dynamic threshold: minimum occurrences to be considered (e.g. 95th percentile)
    # We want robust prefixes, ignoring noise
    threshold = max(5, np.percentile(counts, 50))
    valid_prefs = {p for p, c in global_counts.items() if c >= threshold}
    
    # 2. Document Frequency (DF)
    doc_freq = defaultdict(int)
    for section, prefs in section_texts.items():
        unique_prefs = set(prefs).intersection(valid_prefs)
        for p in unique_prefs:
            doc_freq[p] += 1
            
    total_docs = len(section_texts)
    
    # 3. TF-IDF Calculation
    tfidf_results = defaultdict(dict)
    
    for section, prefs in section_texts.items():
        total_section_prefs = len(prefs)
        if total_section_prefs == 0: continue
            
        section_counts = Counter(p for p in prefs if p in valid_prefs)
        
        for pref, count in section_counts.items():
            tf = count / total_section_prefs
            idf = math.log10(total_docs / doc_freq[pref])
            score = tf * idf
            
            if score > 0:
                tfidf_results[section][pref] = {
                    'score': score,
                    'count_in_sec': count,
                    'count_global': global_counts[pref]
                }
                
    return tfidf_results

def run_blind_extraction(filepath, is_hoax=False):
    if not os.path.exists(filepath): return None
    
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    if is_hoax:
        # Robust length-preserving hoax generator for prefixes
        full_text = " ".join(df['Deep_Clean_Text'].dropna().tolist())
        words = full_text.split()
        chars = list("".join(words))
        random.shuffle(chars)
        
        shuffled_text_blocks = []
        char_idx = 0
        for text in df['Deep_Clean_Text']:
            if not text or pd.isna(text):
                shuffled_text_blocks.append("")
                continue
            row_words = text.split()
            new_words = []
            for w in row_words:
                l = len(w)
                new_w = "".join(chars[char_idx : char_idx + l])
                new_words.append(new_w)
                char_idx += l
            shuffled_text_blocks.append(" ".join(new_words))
            
        df['Deep_Clean_Text'] = shuffled_text_blocks

    section_texts = defaultdict(list)
    for _, row in df.iterrows():
        cat = get_visual_category(row['Folio'])
        if cat != "Unknown":
            words = str(row['Deep_Clean_Text']).split()
            prefixes = extract_prefixes(words)
            section_texts[cat].extend(prefixes)
            
    tfidf_data = calculate_tfidf(section_texts)
    
    print(f"\n[{'RANDOM_HOAX_BASELINE' if is_hoax else filepath.split('/')[-1]}]")
    
    if not tfidf_data:
        print("    [-] No statistically significant unique prefixes found.")
        return
        
    for section in ['Herbal', 'Astronomy', 'Balneology', 'Pharmaceutical', 'Recipes']:
        if section not in tfidf_data: continue
        
        print(f"    [+] Section: {section}")
        sorted_prefs = sorted(tfidf_data[section].items(), key=lambda x: x[1]['score'], reverse=True)
        
        for pref, stats in sorted_prefs[:TOP_N_PREFIXES]:
            score = stats['score'] * 1000 # Multiply by 1000 for readability
            c_sec = stats['count_in_sec']
            c_glob = stats['count_global']
            print(f"        -> '{pref}-' | Score: {score:.4f} | Occurs {c_sec} times here (Out of {c_glob} globally)")
    
    return tfidf_data

def main():
    print("=== Voynich Phase VII: Blind Thematic Extraction (Prefix TF-IDF) ===\n")
    print("[*] Note: Finding the most unique macro-operators (2-3 chars) per section entirely de novo.\n")
    
    for filepath in VOYNICH_FILES:
        run_blind_extraction(filepath)
        
    print("\n" + "="*70)
    print("[*] RUNNING CHAOS CONTROL (RANDOM_HOAX_BASELINE)")
    print("    If TF-IDF scores are high here, the metric is flawed.")
    print("    If scores collapse, the authentic Voynich text is intentionally polymorphic.")
    print("="*70)
    if VOYNICH_FILES:
        run_blind_extraction(VOYNICH_FILES[0], is_hoax=True)

    print("\n=================================================================")
    print("PHASE VII EXTRACTION COMPLETE.")
    print("=================================================================")

if __name__ == "__main__":
    main()