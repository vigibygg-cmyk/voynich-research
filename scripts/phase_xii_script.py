# VOYNICH MANUSCRIPT: TAXONOMIC NOMENCLATURE & LEXEME ISOLATION (PHASE XII)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import math
import random
import os
import numpy as np
from collections import Counter, defaultdict

# Configuration - Triangulation
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

MIN_LEXEME_FREQ = 5 # Filter out rare hapax legomena to ensure statistical robustness

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_visual_category(folio_str):
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Unknown"
    num = int(match.group(1))
    
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 88 <= num <= 102: return "Pharmaceutical"
    elif 103 <= num <= 116: return "Recipes"
    else: return "Unknown"

def generate_hoax_dataframe(df):
    """Shuffles characters to simulate a completely unstructured hoax baseline."""
    hoax_df = df.copy()
    full_text = " ".join(hoax_df['Deep_Clean_Text'].dropna().tolist())
    chars = list(full_text.replace(" ", ""))
    random.shuffle(chars)
    
    shuffled_text_blocks = []
    char_idx = 0
    for text in hoax_df['Deep_Clean_Text']:
        if not text or pd.isna(text):
            shuffled_text_blocks.append("")
            continue
        words = text.split()
        new_words = []
        for w in words:
            new_w = "".join(chars[char_idx : char_idx + len(w)])
            new_words.append(new_w)
            char_idx += len(w)
        shuffled_text_blocks.append(" ".join(new_words))
        
    hoax_df['Deep_Clean_Text'] = shuffled_text_blocks
    return hoax_df

def calculate_dynamic_parameters(df):
    """
    BLIND DISCOVERY: Dynamically calculates the Top 20 Stop Words and 
    Top 15 grammatical suffixes purely from the raw dataset provided.
    No hardcoded semantic assumptions are used.
    """
    all_words = []
    for text in df['Deep_Clean_Text'].dropna():
        all_words.extend(text.split())
        
    # 1. Dynamic Stop Words (Top 20 most frequent words)
    word_counts = Counter(all_words)
    all_counts = [count for _, count in word_counts.most_common()]
    threshold = max(2, np.percentile(all_counts, 99.5)) if all_counts else 2
    stop_words = set(w for w, c in word_counts.items() if c >= threshold)    
    # 2. Dynamic Grammatical Suffixes (Top 15 most frequent endings of length 1-4)
    suffix_counts = Counter()
    for word in all_words:
        if word not in stop_words and len(word) >= 4: # Only check substantive words
            for i in range(1, 5): # Extract endings of length 1, 2, 3, 4
                if len(word) - i >= 2: # Ensure a root of at least 2 chars would remain
                    suffix_counts[word[-i:]] += 1
                    
    # Select top 15 and sort by length descending (e.g., strip 'aiin' before 'iin')
    dynamic_suffixes = [s for s, c in suffix_counts.most_common(15)]
    dynamic_suffixes.sort(key=len, reverse=True)
    
    return stop_words, dynamic_suffixes

def voynich_stemmer(word, dynamic_suffixes):
    """
    Deterministic blind stemmer.
    1. Removes prefix 'q' if it functions as a visual separator.
    2. Strips dynamically discovered grammatical suffixes.
    """
    if len(word) < 3:
        return word
        
    # Strip common visual separator prefix 'q'
    if word.startswith('q') and len(word) > 3:
        word = word[1:]
        
    for suffix in dynamic_suffixes:
        if word.endswith(suffix):
            stemmed = word[:-len(suffix)]
            if len(stemmed) >= 2: # Keep the root meaningful
                return stemmed
                
    return word

def isolate_lexemes(text, stop_words, dynamic_suffixes):
    """Strips stop-words and stems the remaining tokens into pure semantic lexemes."""
    if not text or pd.isna(text): return ""
    words = text.split()
    
    lexemes = []
    for w in words:
        if w not in stop_words:
            stemmed = voynich_stemmer(w, dynamic_suffixes)
            lexemes.append(stemmed)
            
    return " ".join(lexemes)

def calculate_lexeme_tfidf(section_lexemes):
    """Calculates TF-IDF on pure, isolated lexemes."""
    global_counts = Counter()
    for lexemes in section_lexemes.values():
        global_counts.update(lexemes)
        
    valid_lexemes = {l for l, c in global_counts.items() if c >= MIN_LEXEME_FREQ}
    
    doc_freq = defaultdict(int)
    for section, lexemes in section_lexemes.items():
        unique_lexemes = set(lexemes).intersection(valid_lexemes)
        for l in unique_lexemes:
            doc_freq[l] += 1
            
    total_docs = len(section_lexemes)
    tfidf_results = defaultdict(dict)
    
    for section, lexemes in section_lexemes.items():
        total_section_lexemes = len(lexemes)
        if total_section_lexemes == 0: continue
            
        section_counts = Counter(l for l in lexemes if l in valid_lexemes)
        
        for lexeme, count in section_counts.items():
            tf = count / total_section_lexemes
            idf = math.log10(total_docs / doc_freq[lexeme])
            score = tf * idf
            if score > 0:
                tfidf_results[section][lexeme] = {
                    'score': score * 1000, # Scaled for readability
                    'count': count,
                    'global_count': global_counts[lexeme]
                }
    return tfidf_results

def analyze_nomenclature(df, source_name):
    print(f"\n" + "="*70)
    print(f"[*] EXECUTING BLIND TAXONOMIC NOMENCLATURE ISOLATION: [{source_name}]")
    print("="*70)
    
    # 1. Dynamically calculate parameters
    stop_words, dynamic_suffixes = calculate_dynamic_parameters(df)
    print(f"    [+] Dynamically Discovered Suffixes to Strip:\n        {dynamic_suffixes}")
    
    # 2. Isolate the pure semantic lexemes (Roots)
    df['Isolated_Lexemes'] = df['Deep_Clean_Text'].apply(lambda x: isolate_lexemes(x, stop_words, dynamic_suffixes))
    
    # 3. Group isolated lexemes by visual category
    section_lexemes = defaultdict(list)
    for _, row in df.iterrows():
        cat = get_visual_category(row['Folio'])
        if cat != "Unknown":
            section_lexemes[cat].extend(str(row['Isolated_Lexemes']).split())
            
    # 4. Calculate TF-IDF on the isolated taxonomic layer
    tfidf_data = calculate_lexeme_tfidf(section_lexemes)
    
    print("\n    [+] ISOLATED TAXONOMIC NOMENCLATURE (Pure Semantic Roots Post-Stemming):")
    if not tfidf_data:
        print("        [-] No significant taxonomic data remained.")
        return
        
    for section in ['Herbal', 'Astronomy', 'Balneology', 'Recipes']:
        if section not in tfidf_data: continue
        
        sorted_lexemes = sorted(tfidf_data[section].items(), key=lambda x: x[1]['score'], reverse=True)
        print(f"        -> {section.upper()} NOMENCLATURE:")
        for lexeme, stats in sorted_lexemes[:4]:
            print(f"             Root Lexeme: '{lexeme:<8}-' | Score: {stats['score']:.2f} | Local: {stats['count']} | Global: {stats['global_count']}")
    print()

def main():
    print("=== Voynich Phase XII: Blind Taxonomic Nomenclature Isolation ===\n")
    print("Hypothesis: Suffix-stripping will expose the underlying, highly specific")
    print("root nouns (Taxonomic Nomenclature) exclusive to each section.\n")
    print("CRITICAL: ALL STOP-WORDS AND SUFFIXES ARE CALCULATED DYNAMICALLY PER FILE.")
    
    # 1. Authentic Transcriptions (Triangulation)
    for filepath in TARGET_FILES:
        if not os.path.exists(filepath):
            print(f"[-] Error: File {filepath} not found.")
            continue
            
        source_name = filepath.split('/')[-1]
        df = pd.read_csv(filepath)
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        analyze_nomenclature(df, source_name)
        
    # 2. Chaos Control Baseline
    if TARGET_FILES and os.path.exists(TARGET_FILES[0]):
        print("\n" + "="*70)
        print("[*] RUNNING CHAOS CONTROL (RANDOM_HOAX_BASELINE)")
        print("    Hypothesis: Randomized characters will fail to produce structured lexeme taxonomy.")
        print("="*70)
        df = pd.read_csv(TARGET_FILES[0])
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        hoax_df = generate_hoax_dataframe(df)
        analyze_nomenclature(hoax_df, "RANDOM_HOAX_BASELINE")

if __name__ == "__main__":
    main()
# ==============================================================================