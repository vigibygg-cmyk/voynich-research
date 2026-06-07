# ==============================================================================
# VOYNICH MANUSCRIPT: ENTROPY AND MORPHOLOGICAL VALENCY SCRIPT (PHASE II)
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
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
BPE_MERGE_ITERATIONS = 1500

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

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

def calculate_morphological_valency(vocab_bpe):
    anchor_modifiers = defaultdict(set)
    anchor_frequencies = defaultdict(int)
    for bpe_word, freq in vocab_bpe.items():
        subwords = bpe_word.split()
        if len(subwords) > 1:
            anchor = subwords[0]
            modifier = "".join(subwords[1:])
            anchor_modifiers[anchor].add(modifier)
            anchor_frequencies[anchor] += freq
            
    freqs = list(anchor_frequencies.values())
    if not freqs:
        return 0.0, {}
        
    # FIX: Dynamic threshold instead of hardcoded 50
    # We only consider the top 5% of anchors by frequency to avoid hapax legomena noise
    threshold = max(5, np.percentile(freqs, 95))
    
    robust_anchors = {
        anch: mods for anch, mods in anchor_modifiers.items() 
        if anchor_frequencies[anch] >= threshold
    }
    
    if not robust_anchors:
        return 0.0, {}
        
    total_valency = sum(len(mods) for mods in robust_anchors.values())
    avg_valency = total_valency / len(robust_anchors)
    return avg_valency, robust_anchors

def process_file(filepath):
    print(f"\n[{filepath.split('/')[-1]}] Loading and deep-cleaning the corpus...")
    if not os.path.exists(filepath):
        return None
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_corpus.split()
    print(f"    [i] Total words processed: {len(words)}")
    perplexity = calculate_perplexity(full_corpus)
    print(f"    [+] Character Bigram Perplexity: {perplexity:.4f}")
    vocab = Counter(" ".join(list(w)) for w in words)
    for i in range(BPE_MERGE_ITERATIONS):
        pairs = get_stats(vocab)
        if not pairs: break
        best_pair = max(pairs, key=pairs.get)
        vocab = merge_vocab(best_pair, vocab)
    valency, robust_anchors = calculate_morphological_valency(vocab)
    print(f"    [+] Morphological Valency Score: {valency:.4f}")
    sorted_anchors = sorted(robust_anchors.items(), key=lambda x: len(x[1]), reverse=True)
    top_anchors_str = ", ".join([f"'{a}' ({len(m)})" for a, m in sorted_anchors[:3]])
    print(f"    [*] Top 3 Anchors: {top_anchors_str}")
    return {
        "File": filepath.split('/')[-1],
        "Words": len(words),
        "Perplexity": perplexity,
        "Valency": valency
    }

def generate_hoax_baseline(corpus_text):
    # FIX: Robust Hoax Generator that preserves word lengths!
    words = corpus_text.split()
    lengths = [len(w) for w in words]
    chars = list("".join(words))
    random.shuffle(chars)
    
    hoax_words = []
    idx = 0
    for l in lengths:
        hoax_words.append("".join(chars[idx:idx+l]))
        idx += l
    return " ".join(hoax_words)

def process_hoax(filepath):
    print(f"\n[RANDOM_HOAX_BASELINE] Generating random noise from {filepath.split('/')[-1]}...")
    if not os.path.exists(filepath): return None
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    original_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    hoax_corpus = generate_hoax_baseline(original_corpus)
    words = hoax_corpus.split()
    print(f"    [i] Total pseudo-words generated: {len(words)}")
    perplexity = calculate_perplexity(hoax_corpus)
    print(f"    [+] Character Bigram Perplexity: {perplexity:.4f}")
    vocab = Counter(" ".join(list(w)) for w in words)
    for i in range(BPE_MERGE_ITERATIONS):
        pairs = get_stats(vocab)
        if not pairs: break
        best_pair = max(pairs, key=pairs.get)
        vocab = merge_vocab(best_pair, vocab)
    valency, robust_anchors = calculate_morphological_valency(vocab)
    print(f"    [+] Morphological Valency Score: {valency:.4f}")
    sorted_anchors = sorted(robust_anchors.items(), key=lambda x: len(x[1]), reverse=True)
    top_anchors_str = ", ".join([f"'{a}' ({len(m)})" for a, m in sorted_anchors[:3]]) if sorted_anchors else "None"
    print(f"    [*] Top 3 Anchors: {top_anchors_str}")
    return {
        "File": "RANDOM_HOAX_BASELINE",
        "Words": len(words),
        "Perplexity": perplexity,
        "Valency": valency
    }

def main():
    print("=== Voynich Phase II: Entropy and Morphological Valency (Triangulation) ===")
    results = []
    for filepath in TARGET_FILES:
        res = process_file(filepath)
        if res: results.append(res)
    if TARGET_FILES:
        hoax_res = process_hoax(TARGET_FILES[0])
        if hoax_res: results.append(hoax_res)
    print("\n=========================================================")
    print("PHASE II TRIANGULATION SUMMARY:")
    print("=========================================================")
    df_results = pd.DataFrame(results)
    print(df_results.to_string(index=False))
    print("=========================================================")

if __name__ == "__main__":
    main()