# ==============================================================================
# VOYNICH MANUSCRIPT: SEMANTIC PEELING & STOP-WORD FILTRATION (PHASE XI)
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
MIN_WORD_FREQ = 5      # For TF-IDF noise reduction

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'<>', ' ', text)
    text = re.sub(r'\$\w+', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
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
    # FIX: Robust length-preserving hoax generator
    hoax_df = df.copy()
    full_text = " ".join(hoax_df['Deep_Clean_Text'].dropna().tolist())
    words = full_text.split()
    chars = list("".join(words))
    random.shuffle(chars)
    
    shuffled_text_blocks = []
    char_idx = 0
    for text in hoax_df['Deep_Clean_Text']:
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
        
    hoax_df['Deep_Clean_Text'] = shuffled_text_blocks
    return hoax_df

def get_global_stop_words(df):
    """Identifies the most frequent tokens across the entire manuscript dynamically."""
    global_counts = Counter()
    for text in df['Deep_Clean_Text'].dropna():
        global_counts.update(text.split())
        
    freqs = list(global_counts.values())
    if not freqs: return [], global_counts
    
    # Dynamic threshold: Top 0.5% most frequent words (99.5th percentile)
    threshold = np.percentile(freqs, 99.5)
    top_words = [word for word, count in global_counts.items() if count >= threshold]
    top_words.sort(key=lambda w: global_counts[w], reverse=True)
    
    return top_words, global_counts

def peel_text(text, stop_words_set):
    """Removes the structural stop-words to expose the taxonomic layer."""
    if not text or pd.isna(text): return ""
    words = text.split()
    peeled_words = [w for w in words if w not in stop_words_set]
    return " ".join(peeled_words)

def calculate_tfidf(section_texts):
    """Calculates TF-IDF on the peeled texts to find taxonomic anchors."""
    global_counts = Counter()
    for words in section_texts.values():
        global_counts.update(words)
        
    valid_words = {w for w, c in global_counts.items() if c >= MIN_WORD_FREQ}
    
    doc_freq = defaultdict(int)
    for section, words in section_texts.items():
        unique_words = set(words).intersection(valid_words)
        for w in unique_words:
            doc_freq[w] += 1
            
    total_docs = len(section_texts)
    tfidf_results = defaultdict(dict)
    
    for section, words in section_texts.items():
        total_section_words = len(words)
        if total_section_words == 0: continue
            
        section_counts = Counter(w for w in words if w in valid_words)
        
        for word, count in section_counts.items():
            tf = count / total_section_words
            idf = math.log10(total_docs / doc_freq[word])
            score = tf * idf
            if score > 0:
                tfidf_results[section][word] = {
                    'score': score * 1000, # Scaled for readability
                    'count': count
                }
    return tfidf_results

def analyze_peeled_corpus(df, source_name):
    print(f"\n" + "="*70)
    print(f"[*] EXECUTING SEMANTIC PEELING: [{source_name}]")
    print("="*70)
    
    stop_words, global_counts = get_global_stop_words(df)
    stop_words_set = set(stop_words)
    
    print(f"\n    [+] BLIND IDENTIFICATION OF THE 'GARBAGE BARRIER' ({len(stop_words)} dynamic structural tokens):")
    formatted_stops = [f"'{w}' ({global_counts[w]})" for w in stop_words[:20]]
    if len(stop_words) > 20: formatted_stops.append("...")
    print(f"        {', '.join(formatted_stops)}")
    
    df['Peeled_Text'] = df['Deep_Clean_Text'].apply(lambda x: peel_text(x, stop_words_set))
    
    section_texts = defaultdict(list)
    for _, row in df.iterrows():
        cat = get_visual_category(row['Folio'])
        if cat != "Unknown":
            section_texts[cat].extend(str(row['Peeled_Text']).split())
            
    tfidf_data = calculate_tfidf(section_texts)
    
    print("\n    [+] EXPOSING THE TAXONOMIC LAYER (Top TF-IDF Nouns Post-Peeling):")
    if not tfidf_data:
        print("        [-] No significant taxonomic data remained.")
        return
        
    for section in ['Herbal', 'Astronomy', 'Balneology', 'Pharmaceutical', 'Recipes']:
        if section not in tfidf_data: continue
        
        sorted_words = sorted(tfidf_data[section].items(), key=lambda x: x[1]['score'], reverse=True)
        print(f"        -> {section.upper()} SECTION:")
        for word, stats in sorted_words[:5]:
            print(f"             '{word:<10}' | Score: {stats['score']:.2f} | Occurrences: {stats['count']}")
    print()

def main():
    print("=== Voynich Phase XI: Semantic Peeling & 'Garbage' Barrier Extraction ===\n")
    print("Hypothesis: The most frequent tokens are structural code operators, not nouns.")
    print("Removing them will expose the true, section-specific taxonomic dictionary.\n")
    
    for filepath in TARGET_FILES:
        if not os.path.exists(filepath):
            print(f"[-] Error: File {filepath} not found.")
            continue
            
        source_name = filepath.split('/')[-1]
        df = pd.read_csv(filepath)
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        analyze_peeled_corpus(df, source_name)
        
    if TARGET_FILES and os.path.exists(TARGET_FILES[0]):
        print("\n" + "="*70)
        print("[*] RUNNING CHAOS CONTROL (RANDOM_HOAX_BASELINE)")
        print("    Hypothesis: Random text will not yield organized taxonomic clusters after peeling.")
        print("="*70)
        df = pd.read_csv(TARGET_FILES[0])
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        hoax_df = generate_hoax_dataframe(df)
        analyze_peeled_corpus(hoax_df, "RANDOM_HOAX_BASELINE")
        
    print("\n=================================================================")
    print("PHASE XI COMPLETE.")
    print("=================================================================")

if __name__ == "__main__":
    main()