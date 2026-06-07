# ==============================================================================
# VOYNICH MANUSCRIPT: COMPETING MODEL BENCHMARKING (PHASE XXV)
# The Synthetic Gauntlet
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import math
import random
import string
import os
from collections import Counter, defaultdict

# Configuration
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
BPE_MERGE_ITERATIONS = 200
MIN_ANCHOR_FREQ = 15
SAMPLE_SIZE = 5000  # Words per generated corpus (comparable to Voynich sections)

# --- LITURGICAL TEMPLATE PARAMETERS ---
LITURGICAL_TEMPLATES = [
    "dominus {A} et {B} per {C} amen",
    "sanctus {A} gloria {B} in {C}",
    "{A} dei {B} gratia {C} lux",
    "ora pro {A} et {B} dominus {C}",
    "{A} per secula {B} amen {C}"
]
LITURGICAL_SLOTS = {
    "A": ["nobis", "vobis", "omnibus", "sanctis", "deum"],
    "B": ["eternam", "vitam", "pacem", "lucem", "celi"],
    "C": ["christi", "spiritus", "patris", "filii", "domini"]
}

# --- VIGENERE CIPHER PARAMETERS ---
LATIN_SAMPLE_WORDS = [
    "herba", "medicina", "aqua", "folia", "radix", "flores", "succus",
    "oleum", "misce", "recipe", "luna", "sol", "stella", "terra", "ignis",
    "caelum", "corpus", "anima", "natura", "spiritus", "sanguis", "fel",
    "pulvis", "extractum", "tinctura", "infusio", "decoctum", "planta"
]
VIGENERE_KEY = "LAPIS"

# ==============================================================================
# SHARED UTILITIES
# ==============================================================================

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_perplexity(corpus_text):
    """Character-level Bigram Perplexity."""
    chars = list(corpus_text)
    total_chars = len(chars)
    if total_chars < 2:
        return 0.0
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
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i + 1]] += freq
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
    """Morphological Valency via BPE."""
    if not words:
        return 0.0
    vocab = Counter(" ".join(list(w)) for w in words)
    for _ in range(BPE_MERGE_ITERATIONS):
        pairs = get_stats(vocab)
        if not pairs:
            break
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
    robust_anchors = {
        anch: mods for anch, mods in anchor_modifiers.items()
        if anchor_frequencies[anch] >= MIN_ANCHOR_FREQ
    }
    if not robust_anchors:
        return 0.0
    return sum(len(mods) for mods in robust_anchors.values()) / len(robust_anchors)

def get_metrics(words, label):
    sample = words[:SAMPLE_SIZE] if len(words) >= SAMPLE_SIZE else words
    text = " ".join(sample)
    perp = calculate_perplexity(text)
    val = calculate_valency(sample)
    print(f"    [{label}]")
    print(f"        Perplexity : {perp:.4f}")
    print(f"        Valency    : {val:.4f}")
    return {"Model": label, "Perplexity": round(perp, 4), "Valency": round(val, 4)}

# ==============================================================================
# GENERATORS
# ==============================================================================

def build_markov_model(words, n=2):
    model = defaultdict(list)
    for i in range(len(words) - n):
        state = tuple(words[i:i + n])
        next_word = words[i + n]
        model[state].append(next_word)
    return model

def generate_markov_text(model, seed_words, length=SAMPLE_SIZE):
    n = len(list(model.keys())[0])
    current_state = tuple(seed_words[:n])
    output = list(current_state)
    for _ in range(length - n):
        if current_state in model:
            next_word = random.choice(model[current_state])
            output.append(next_word)
            current_state = tuple(output[-n:])
        else:
            current_state = random.choice(list(model.keys()))
    return output

def vigenere_encrypt_word(word, key):
    key_upper = key.upper()
    result = []
    key_idx = 0
    for char in word.upper():
        if char.isalpha():
            shift = ord(key_upper[key_idx % len(key_upper)]) - ord('A')
            encrypted_char = chr((ord(char) - ord('A') + shift) % 26 + ord('A'))
            result.append(encrypted_char.lower())
            key_idx += 1
        else:
            result.append(char)
    return "".join(result)

def generate_vigenere_corpus(key, sample_size=SAMPLE_SIZE):
    random.seed(99)
    plaintext_words = [random.choice(LATIN_SAMPLE_WORDS) for _ in range(sample_size)]
    return [vigenere_encrypt_word(w, key) for w in plaintext_words]

def generate_liturgical_corpus(sample_size=SAMPLE_SIZE):
    random.seed(77)
    words = []
    while len(words) < sample_size:
        template = random.choice(LITURGICAL_TEMPLATES)
        filled = template
        for slot, options in LITURGICAL_SLOTS.items():
            filled = filled.replace(f"{{{slot}}}", random.choice(options))
        words.extend(filled.split())
    return words[:sample_size]

def generate_gibberish_corpus(sample_size=SAMPLE_SIZE):
    random.seed(55)
    voynich_alphabet = list("abcdefghiklmnopqrstuwy")
    words = []
    while len(words) < sample_size:
        length = random.choices(range(2, 10), weights=[1, 3, 5, 5, 4, 3, 2, 1], k=1)[0]
        word = "".join(random.choice(voynich_alphabet) for _ in range(length))
        words.append(word)
    return words

# ==============================================================================
# MAIN PIPELINE
# ==============================================================================

def load_voynich_words(filepath):
    if not os.path.exists(filepath): return []
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    return " ".join(df['Deep_Clean_Text'].dropna().tolist()).split()

def main():
    print("=" * 70)
    print("=== VOYNICH PHASE XXV: THE SYNTHETIC GAUNTLET ===")
    print("=" * 70)
    print("Objective: Demonstrate that no standard model replicates")
    print("the Voynich Perplexity/Valency footprint.\n")

    results = []

    print("[*] STEP 1: VOYNICH BASELINES (Triangulation)")
    print("-" * 70)
    voynich_word_pool = []
    for filepath in VOYNICH_FILES:
        words = load_voynich_words(filepath)
        if words:
            label = f"VM_Baseline ({filepath.split('/')[-1].replace('_clean.csv','')})"
            results.append(get_metrics(words, label))
            voynich_word_pool.extend(words)

    if not voynich_word_pool:
        print("\n[-] FATAL: No Voynich data loaded.")
        return

    print("\n[*] STEP 2: GENERATOR 1 — N-GRAM MARKOV CHAIN")
    print("-" * 70)
    random.seed(42)
    markov_model = build_markov_model(voynich_word_pool, n=2)
    markov_words = generate_markov_text(markov_model, voynich_word_pool[:2], length=SAMPLE_SIZE)
    results.append(get_metrics(markov_words, "Markov_Chain_Bigram"))

    markov_model_3 = build_markov_model(voynich_word_pool, n=3)
    markov_words_3 = generate_markov_text(markov_model_3, voynich_word_pool[:3], length=SAMPLE_SIZE)
    results.append(get_metrics(markov_words_3, "Markov_Chain_Trigram"))

    print("\n[*] STEP 3: GENERATOR 2 — VIGENÈRE CIPHER")
    print("-" * 70)
    results.append(get_metrics(generate_vigenere_corpus("LAPIS"), "Vigenere_Cipher (LAPIS)"))
    results.append(get_metrics(generate_vigenere_corpus("PHILOSOPHORUM"), "Vigenere_Cipher (PHILOSOPHORUM)"))

    print("\n[*] STEP 4: GENERATOR 3 — LITURGICAL FORMULA")
    print("-" * 70)
    results.append(get_metrics(generate_liturgical_corpus(), "Liturgical_Formula"))

    print("\n[*] STEP 5: GENERATOR 4 — CONSTRAINED GIBBERISH")
    print("-" * 70)
    results.append(get_metrics(generate_gibberish_corpus(), "Constrained_Gibberish"))

    print("\n" + "=" * 70)
    print("PHASE XXV: SYNTHETIC GAUNTLET — FINAL COMPARISON TABLE")
    print("=" * 70)
    print(f"{'Model':<45} {'Perplexity':>12} {'Valency':>10}")
    print("-" * 70)

    for r in [x for x in results if x["Model"].startswith("VM_")]:
        print(f"  {'[VOYNICH] ' + r['Model']:<45} {r['Perplexity']:>12.4f} {r['Valency']:>10.4f}")

    print("-" * 70)
    for r in [x for x in results if not x["Model"].startswith("VM_")]:
        print(f"  {r['Model']:<45} {r['Perplexity']:>12.4f} {r['Valency']:>10.4f}")

    print("=" * 70)
    print("\nPHASE XXV COMPLETE. Execute to view Gauntlet results.")

if __name__ == "__main__":
    main()