# VOYNICH MANUSCRIPT: ISOMORPHIC CORPUS COMPARISON (PHASE V)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import math
import random
import numpy as np
from collections import Counter, defaultdict
import os

# Configuration
CORPUS_DIR = "historical_corpora"

# Voynich Triangulation Files
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Bootstrapping Parameters
SAMPLE_SIZE = 5000
BOOTSTRAP_ITERATIONS = 30 # Increased for statistical significance
BPE_MERGES = 200  # Scaled down for 5k word samples

HISTORICAL_FILES = [
    "German_Botany_Medicine.txt",
    "German_Astronomy_Astrology.txt",
    "German_History_Politics.txt",
    "German_General_Unknown.txt",
    "Latin_Alchemy.txt",
    "Latin_Botany_Medicine.txt",
    "Latin_Astronomy_Astrology.txt",
    "Latin_General_Unknown.txt",
    "Ancient_Greek_Botany_Medicine.txt",
    "Dutch_Botany_Medicine.txt",
    "English_Theology_Religion.txt",
    "Finnish_Astronomy_Astrology.txt",      
    "Hungarian_Theology_Religion.txt",    
    "Polish_Theology_Religion.txt"        
]

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def load_voynich_words(filepath):
    if not os.path.exists(filepath):
        return []
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    return full_corpus.split()

def load_historical_words(filename):
    filepath = os.path.join(CORPUS_DIR, filename)
    if not os.path.exists(filepath):
        return []
    
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
    
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower().split()

def calculate_perplexity(corpus_text):
    chars = list(corpus_text)
    total_chars = len(chars)
    if total_chars < 2: return 0.0
    
    unigram_counts = Counter(chars)
    bigram_counts = Counter(zip(chars[:-1], chars[1:]))
    
    entropy = 0.0
    for (c1, c2), bi_count in bigram_counts.items():
        p_c1_c2 = bi_count / (total_chars - 1)
        p_c2_given_c1 = bi_count / unigram_counts[c1]
        entropy -= p_c1_c2 * math.log2(p_c2_given_c1)
        
    return 2 ** entropy

def get_stats(vocab):
    pairs = defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols)-1):
            pairs[symbols[i], symbols[i+1]] += freq
    return pairs

def merge_vocab(pair, v_in):
    v_out = {}
    bigram = re.escape(' '.join(pair))
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out

def calculate_valency(words):
    vocab = Counter(" ".join(list(w)) for w in words)
    
    for _ in range(BPE_MERGES):
        pairs = get_stats(vocab)
        if not pairs: break
        best_pair = max(pairs, key=pairs.get)
        vocab = merge_vocab(best_pair, vocab)
        
    anchor_modifiers = defaultdict(set)
    anchor_frequencies = defaultdict(int)
    
    for bpe_word, freq in vocab.items():
        subwords = bpe_word.split()
        if len(subwords) > 1:
            anchor = subwords[0]
            modifier = "".join(subwords[1:])
            anchor_modifiers[anchor].add(modifier)
            anchor_frequencies[anchor] += freq
            
    freqs = list(anchor_frequencies.values())
    if not freqs: return 0.0
    
    threshold = max(3, np.percentile(freqs, 95))
    robust_anchors = {
        anch: mods for anch, mods in anchor_modifiers.items() 
        if anchor_frequencies[anch] >= threshold
    }
    
    if not robust_anchors:
        return 0.0
        
    total_valency = sum(len(mods) for mods in robust_anchors.values())
    return total_valency / len(robust_anchors)

def bootstrap_analysis(name, words):
    print(f"\n[*] Bootstrapping {name} (Total available words: {len(words)})")
    if len(words) < SAMPLE_SIZE:
        print(f"    [-] Not enough words for full {SAMPLE_SIZE}-word sample. Using available {len(words)} words.")
        sample_size = len(words)
        iterations = 1
    else:
        sample_size = SAMPLE_SIZE
        iterations = BOOTSTRAP_ITERATIONS
        
    perplexities = []
    valencies = []
    
    for i in range(iterations):
        if len(words) > sample_size:
            start_idx = random.randint(0, len(words) - sample_size)
            sample_words = words[start_idx : start_idx + sample_size]
        else:
            sample_words = words
            
        sample_text = " ".join(sample_words)
        
        perp = calculate_perplexity(sample_text)
        val = calculate_valency(sample_words)
        
        perplexities.append(perp)
        valencies.append(val)
        
    avg_perp = sum(perplexities) / len(perplexities)
    avg_val = sum(valencies) / len(valencies)
    
    print(f"    [=] AVERAGE (Over {iterations} runs) -> Perplexity: {avg_perp:.4f} | Valency: {avg_val:.4f}")
    
    return {
        "Corpus": name,
        "Avg_Perplexity": avg_perp,
        "Avg_Valency": avg_val
    }

def process_hoax(filepath):
    words = load_voynich_words(filepath)
    if not words: return None
    
    lengths = [len(w) for w in words]
    chars = list("".join(words))
    random.shuffle(chars)
    
    hoax_words = []
    idx = 0
    for l in lengths:
        hoax_words.append("".join(chars[idx:idx+l]))
        idx += l
        
    return bootstrap_analysis("RANDOM_HOAX_BASELINE", hoax_words)

def main():
    print("=== Voynich Phase V: Isomorphic Historical Corpus Comparison ===\n")
    
    if not os.path.exists(CORPUS_DIR):
        os.makedirs(CORPUS_DIR)
        print(f"[!] Created directory '{CORPUS_DIR}'. Please upload your text files here.")
    
    results = []
    
    # 1. Analyze Voynich Baselines (Triangulation)
    for v_file in VOYNICH_FILES:
        voynich_words = load_voynich_words(v_file)
        if voynich_words:
            base_name = v_file.split('/')[-1].replace('_clean.csv', '')
            res = bootstrap_analysis(f"VM_Baseline ({base_name})", voynich_words)
            results.append(res)
        else:
            print(f"[-] Error: {v_file} not found. Cannot set baseline.")
            
    # Generate Hoax Baseline from the first Voynich file
    if VOYNICH_FILES:
        hoax_res = process_hoax(VOYNICH_FILES[0])
        if hoax_res:
            results.append(hoax_res)
    
    # 2. Analyze Historical Corpora
    for filename in HISTORICAL_FILES:
        words = load_historical_words(filename)
        if words:
            res = bootstrap_analysis(filename.replace('.txt', ''), words)
            results.append(res)
        else:
            print(f"[-] Missing or empty file skipped: {filename}")
            
    # 3. Summary
    if results:
        print("\n=========================================================")
        print("PHASE V: STRUCTURAL FINGERPRINT COMPARISON")
        print("=========================================================")
        df_results = pd.DataFrame(results)
        print(df_results.to_string(index=False))
        print("=========================================================")

if __name__ == "__main__":
    main()
# ==============================================================================