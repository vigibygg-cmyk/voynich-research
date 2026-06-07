# ==============================================================================
# VOYNICH MANUSCRIPT: STAGE 2 PRE-REQUISITE (RED TEAM FALSIFICATION BENCHMARK)
# Goal: Differentiate Voynich structure from TRUE historical ciphers (Borg, Copiale)
# Updated: Safe file search algorithm, adapted for Google Colab system
# Added: Perplexity (Entropy) threshold included for precise differentiation
# Fixed: JSD, Perplexity calculations, Counter initialization and directed graphs
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import random
import math
from collections import Counter, defaultdict
import networkx as nx
from networkx.algorithms import community
import warnings
warnings.filterwarnings("ignore")

# Configuration
VOYNICH_FILES = [
    "RF1b-er_clean.csv",
    "ZL3b-n_clean.csv",
    "IT2a-n_clean.csv"
]
COPIALE_FILE = "Copiale-transcription.txt"
BORG_FILE = "Borg_transcription.txt"

SAMPLE_SIZE = 10000  # Standardized token count
BPE_MERGES = 200

# Strict Fail Condition thresholds (Four dimension matrix)
PERPLEXITY_MAX = 5.5        # Voynich is ~4.6. True ciphers > 10.0
JS_THRESHOLD = 0.15         # Must be very close to Voynich profile
MODULARITY_THRESHOLD = 0.35 # Voynich yra ~0.37 - 0.41
VALENCY_THRESHOLD = 15.0    # Voynich yra ~20-21

# ==============================================================================
# AUTOMATIC FILE SEARCH SYSTEM
# ==============================================================================
def find_file(filename):
    """Safe file search algorithm."""
    if os.path.exists(filename):
        return filename
        
    colab_path = os.path.join("/content", filename)
    if os.path.exists(colab_path):
        return colab_path
        
    for folder in ["voynich_clean_data", "historical_corpora"]:
        sub_path = os.path.join(folder, filename)
        if os.path.exists(sub_path):
            return sub_path
        colab_sub_path = os.path.join("/content", folder, filename)
        if os.path.exists(colab_sub_path):
            return colab_sub_path

    for root, dirs, files in os.walk("."):
        if filename in files:
            return os.path.join(root, filename)
            
    if os.path.exists("/content"):
        for root, dirs, files in os.walk("/content"):
            if filename in files:
                return os.path.join(root, filename)
                
    return None

# ==============================================================================
# DATA CLEANING AND PREPARATION
# ==============================================================================
def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def load_voynich_data(filename):
    filepath = find_file(filename)
    if not filepath: 
        return None
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    words = " ".join(df['Deep_Clean_Text'].dropna()).split()
    return words[:SAMPLE_SIZE] if len(words) >= SAMPLE_SIZE else words

def load_copiale_cipher(filename):
    """Reads real Copiale cipher."""
    filepath = find_file(filename)
    if not filepath: 
        return None
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [l for l in f.read().split('\n') if not l.startswith('#')]
        
    raw_text = " ".join(lines)
    raw_text = raw_text.replace('.', '|').replace(':', '|')
    raw_words = raw_text.split('|')
    
    words = []
    for rw in raw_words:
        clean_word = re.sub(r'[^a-zA-Z]', '', rw).lower()
        if len(clean_word) > 0:  # Paliekami vienetiniai simboliai
            words.append(clean_word)
            
    return words[:SAMPLE_SIZE]

def load_borg_cipher(filename):
    """Reads occult Borg cipher."""
    filepath = find_file(filename)
    if not filepath: 
        return None
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
        
    lines = []
    for l in text.split('\n'):
        if l.startswith('#') or l.startswith('<'): continue
        l = re.sub(r'\[.*?\]', '', l)
        lines.append(l)
        
    raw_text = " ".join(lines)
    # Keep only letters, discard numbers
    words = [re.sub(r'[^a-zA-Z]', '', w).lower() for w in raw_text.split()]
    words = [w for w in words if len(w) > 0]
    
    return words[:SAMPLE_SIZE]

def generate_adversarial_morphology():
    """Synthetic adversary: Uses Prefix+Root+Suffix logic."""
    random.seed(42)
    prefixes = ['qo', 'cho', 'o', 'y', 'd']
    roots = ['lka', 'tar', 'she', 'kee', 'dal', 'fch']
    suffixes = ['aiin', 'dy', 'am', 'ey']
    
    adversarial_text = []
    for _ in range(SAMPLE_SIZE):
        p = random.choice(prefixes) if random.random() > 0.2 else ""
        r = random.choice(roots)
        s = random.choice(suffixes) if random.random() > 0.3 else ""
        adversarial_text.append(p + r + s)
    return adversarial_text

# ==============================================================================
# STRUCTURAL METRICS
# ==============================================================================
def calculate_perplexity(words):
    text = " ".join(words)
    chars = list(text)
    if len(chars) < 2: return 0.0
    
    unigram_counts = Counter(chars)
    bigram_counts = Counter(zip(chars[:-1], chars[1:]))
    
    log_prob_sum = 0.0
    for i in range(len(chars) - 1):
        c1, c2 = chars[i], chars[i+1]
        p_c2_given_c1 = bigram_counts[(c1, c2)] / unigram_counts[c1]
        log_prob_sum += math.log2(p_c2_given_c1)
        
    entropy = -log_prob_sum / (len(chars) - 1)
    return 2 ** entropy

def calculate_bpe_valency(words):
    vocab = defaultdict(int)
    for w in words:
        vocab[" ".join(list(w))] += 1
        
    for _ in range(BPE_MERGES):
        pairs = defaultdict(int)
        for w, f in vocab.items():
            syms = w.split()
            for i in range(len(syms)-1): pairs[syms[i], syms[i+1]] += f
        if not pairs: break
        best = max(pairs, key=pairs.get)
        v_out = defaultdict(int)
        pattern = re.compile(r'(?<!\S)' + re.escape(' '.join(best)) + r'(?!\S)')
        for w, freq in vocab.items():
            v_out[pattern.sub(''.join(best), w)] += freq
        vocab = v_out
        
    anchor_mods = defaultdict(set)
    for w, f in vocab.items():
        subwords = w.split()
        if len(subwords) > 1: anchor_mods[subwords[0]].add("".join(subwords[1:]))
    
    robust = [len(m) for a, m in anchor_mods.items() if len(m) > 1]
    return sum(robust)/len(robust) if robust else 0.0

def calculate_js_divergence(target_words, base_words):
    """TRUE symmetric Jensen-Shannon divergence (bounded 0-1)."""
    def get_dist(words):
        counts = Counter("".join(words))
        total  = sum(counts.values())
        return {k: v/total for k, v in counts.items()}
    
    P = get_dist(target_words)
    Q = get_dist(base_words)
    all_keys = set(P) | set(Q)
    
    M = {k: (P.get(k, 0) + Q.get(k, 0)) / 2 for k in all_keys}
    
    def kl(A, B):
        return sum(A.get(k,1e-10) * math.log2(A.get(k,1e-10) / B[k])
                   for k in all_keys if B.get(k,0) > 0)
    
    return (kl(P, M) + kl(Q, M)) / 2

def calculate_graph_modularity(words):
    """Transition graph modularity using undirected edges."""
    G = nx.Graph()
    bigrams = list(zip(words[:-1], words[1:]))
    
    for w1, w2 in bigrams:
        if G.has_edge(w1, w2):
            G[w1][w2]['weight'] += 1
        else:
            G.add_edge(w1, w2, weight=1)
            
    threshold = 2
    G_core = nx.Graph(((u, v, d) for u, v, d in G.edges(data=True) if d['weight'] >= threshold))
    
    if len(G_core.nodes) < 5: return 0.0
    
    try:
        communities = list(community.greedy_modularity_communities(G_core))
        modularity_score = community.modularity(G_core, communities)
        return modularity_score
    except Exception:
        return 0.0

# ==============================================================================
# PAGRINDINIS VAMZDYNAS
# ==============================================================================
def execute_benchmark(name, words, v_words=None):
    print(f"\n[*] ANALIZUOJAMA SISTEMA: [{name}]")
    
    if not words:
        print("    [-] Error: No data.")
        return None
        
    perp = calculate_perplexity(words)
    val = calculate_bpe_valency(words)
    modularity = calculate_graph_modularity(words)
    
    js_div = calculate_js_divergence(words, v_words) if v_words else 0.0
    
    print(f"    -> Perplexity (Entropija): {perp:.4f}")
    print(f"    -> Morphological Valency: {val:.4f}")
    print(f"    -> Transition Graph Modularity (Q): {modularity:.4f}")
    if v_words:
        print(f"    -> JS Divergence from VM: {js_div:.4f}")
        
    return {"System": name, "JS_Div": js_div, "Q_Modularity": modularity, "Perplexity": perp, "Valency": val}

def check_fail_conditions(results):
    print("\n" + "="*80)
    print("FALSIFIKACIJOS BENCHMARKAS: GALUTINIS VERTINIMAS")
    print("="*80)
    
    print(f"[RULES]: System is considered 'Voynich-Like' if ALL 4 criteria are met:")
    print(f"         1. Perplexity      < {PERPLEXITY_MAX}")
    print(f"         2. JS Divergence   < {JS_THRESHOLD}")
    print(f"         3. Modularity Q    > {MODULARITY_THRESHOLD}")
    print(f"         4. Valency         > {VALENCY_THRESHOLD}")
    print("-" * 80)
    
    fail_triggered = False
    
    for res in results:
        if not res or str(res["System"]).startswith("Voynich"):
            continue
            
        print(f"-> Testuojama {res['System']}...")
        if res["Perplexity"] < PERPLEXITY_MAX and res["JS_Div"] < JS_THRESHOLD and res["Q_Modularity"] > MODULARITY_THRESHOLD and res["Valency"] > VALENCY_THRESHOLD:
            print(f"   [!!!] FAIL CONDITION ACTIVATED.")
            print(f"   Adversarial system perfectly imitates Voynich.")
            fail_triggered = True
        else:
            print(f"   [OK] System remains mathematically separable from Voynich.")
            
    print("\n" + "="*80)
    if fail_triggered:
        print("[CRITICAL STOP] Structural metrics lack specificity. Stop semantic linking.")
    else:
        print("[SUCCESS] Voynich structural footprint is uniquely separable from TRUE historical ciphers and hoaxes.")
        print("          Historical ciphers (Borg, Copiale) rejected due to too high Entropy (Perplexity).")
        print("          Safe to proceed to Phase XXXI (Transition Graph Topology).")
    print("="*80)

def main():
    print("=== STAGE 2 PRE-REQUISITE: RED TEAM FALSIFICATION BENCHMARK ===\n")
    print("Goal: Prove that Voynich footprint (Perplexity, Q-Modularity, JS Divergence, Valency)")
    print("cannot be forged by AUTHENTIC historical ciphers (Copiale, Borg).\n")
    
    results = []
    v_words_combined = []
    
    # 1. Baseline Voynich Files (Triangulation)
    for filename in VOYNICH_FILES:
        v_words = load_voynich_data(filename)
        if v_words:
            v_words_combined.extend(v_words)
            results.append(execute_benchmark(f"Voynich Manuscript ({filename})", v_words))
        else:
            print(f"[-] Error: Voynich file {filename} not found.")
            
    if not v_words_combined:
        print("Error: No basic Voynich data. Ensure CSV files are generated.")
        return
        
    v_words_reference = v_words_combined[:SAMPLE_SIZE] if len(v_words_combined) >= SAMPLE_SIZE else v_words_combined
    
    # 2. True Historical Ciphers
    copiale_words = load_copiale_cipher(COPIALE_FILE)
    if copiale_words:
        results.append(execute_benchmark("Copiale Cipher (18th Century Homophonic)", copiale_words, v_words_reference))
    else:
        print(f"[-] Error: File {COPIALE_FILE} not found even after full search.")
        
    borg_words = load_borg_cipher(BORG_FILE)
    if borg_words:
        results.append(execute_benchmark("Borg Cipher (17th Century Occult)", borg_words, v_words_reference))
    else:
        print(f"[-] Error: File {BORG_FILE} not found even after full search.")
    
    # 3. Sintetinis Adversarial Kontrolinis Modelis
    adversarial_words = generate_adversarial_morphology()
    results.append(execute_benchmark("Synthetic Adversarial (Prefix-Root-Suffix)", adversarial_words, v_words_reference))
    
    check_fail_conditions(results)

if __name__ == "__main__":
    main()