# ==============================================================================
# VOYNICH MANUSCRIPT: PMI MATRIX AND SYNTACTIC CHAINS (PHASE III)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import math
import random
import numpy as np
from collections import Counter
import os

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def calculate_pmi_matrix(words):
    total_words = len(words)
    if total_words < 2: return []

    unigram_counts = Counter(words)
    bigrams = list(zip(words[:-1], words[1:]))
    bigram_counts = Counter(bigrams)

    # FIX: Remove hardcoded 15. Use 95th percentile of bigrams occurring > 1 time
    multi_freqs = [v for v in bigram_counts.values() if v > 1]
    if not multi_freqs:
        return []
    threshold = max(3, np.percentile(multi_freqs, 95))

    pmi_results = []
    for (w1, w2), bigram_freq in bigram_counts.items():
        if bigram_freq >= threshold:
            p_x_y = bigram_freq / (total_words - 1)
            p_x = unigram_counts[w1] / total_words
            p_y = unigram_counts[w2] / total_words
            
            pmi = math.log2(p_x_y / (p_x * p_y))
            
            pmi_results.append({
                'Word 1': w1,
                'Word 2': w2,
                'Freq(W1,W2)': bigram_freq,
                'Freq(W1)': unigram_counts[w1],
                'Freq(W2)': unigram_counts[w2],
                'PMI': round(pmi, 4)
            })
            
    return sorted(pmi_results, key=lambda x: x['PMI'], reverse=True)

def process_file(filepath):
    print(f"\n[{filepath.split('/')[-1]}] Generating PMI Matrix...")
    if not os.path.exists(filepath): return None
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_corpus.split()
    
    pmi_data = calculate_pmi_matrix(words)
    if not pmi_data: return None
        
    top_pmi = pmi_data[0]['PMI']
    print(f"    [+] Total Unique Bigrams Analyzed (Dynamic Threshold): {len(pmi_data)}")
    print(f"    [+] Maximum PMI Score Detected: {top_pmi}")
    print("    [*] Top 5 Hardest Syntactic Chains (Highest PMI):")
    for item in pmi_data[:5]:
        print(f"        -> '{item['Word 1']}' + '{item['Word 2']}' (PMI: {item['PMI']} | Occurrences: {item['Freq(W1,W2)']})")

    return {
        "File": filepath.split('/')[-1],
        "Max_PMI": top_pmi,
        "Analyzed_Pairs": len(pmi_data)
    }

def generate_hoax_baseline(words):
    shuffled_words = words.copy()
    random.shuffle(shuffled_words)
    return shuffled_words

def process_hoax(filepath):
    print(f"\n[RANDOM_HOAX_BASELINE] Generating random syntax from {filepath.split('/')[-1]}...")
    if not os.path.exists(filepath): return None
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    original_words = full_corpus.split()
    
    hoax_words = generate_hoax_baseline(original_words)
    pmi_data = calculate_pmi_matrix(hoax_words)
    
    if not pmi_data:
        print(f"    [-] Total Unique Bigrams Analyzed: 0")
        return {"File": "RANDOM_HOAX_BASELINE", "Max_PMI": 0.0, "Analyzed_Pairs": 0}
        
    top_pmi = pmi_data[0]['PMI']
    print(f"    [+] Total Unique Bigrams Analyzed: {len(pmi_data)}")
    print(f"    [+] Maximum PMI Score Detected: {top_pmi}")
    return {"File": "RANDOM_HOAX_BASELINE", "Max_PMI": top_pmi, "Analyzed_Pairs": len(pmi_data)}

def main():
    print("=== Voynich Phase III: PMI Matrix and Hard Syntactic Chains ===")
    results = []
    for filepath in TARGET_FILES:
        res = process_file(filepath)
        if res: results.append(res)
    if TARGET_FILES:
        hoax_res = process_hoax(TARGET_FILES[0])
        if hoax_res: results.append(hoax_res)
    print("\n=========================================================")
    print("PHASE III PMI SUMMARY:")
    print("=========================================================")
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    print("=========================================================")

if __name__ == "__main__":
    main()