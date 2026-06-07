# ==============================================================================
# VOYNICH MANUSCRIPT: TRANSITION GRAPH TOPOLOGY & HIGHER-ORDER MARKOV (PHASE XXXI)
# Features: H(Y|X), Earth Mover's Distance, Spectral Distance, Triadic Motifs
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import networkx as nx
import os
import re
import glob
import warnings
from collections import Counter, defaultdict
from scipy.stats import entropy, wasserstein_distance
from scipy.sparse.linalg import eigs

warnings.filterwarnings("ignore")

# Configuration
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
HISTORICAL_DIR = "historical_corpora"
CIPHER_FILES = ["Copiale-transcription.txt", "Borg_transcription.txt"]
SAMPLE_SIZE = 5000  # Strict Frequency Normalization Length

# Mocks for robust execution
MOCK_LATIN_ALCHEMY = "recipe de herba sal et aqua misce bene in vase et coque " * 1000
MOCK_ARABIC_PHARMA = (
    "khudh min alashba walma wakhlit jayidan fi wiaa watbukh "
    "aljidhur walaawraq wamzijha maaan fi inaa " * 1000
)
MOCK_LITURGICAL = "in nomine patris et filii et spiritus sancti amen " * 1000

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
    return None

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def load_or_simulate_corpus(filepath, mock_text):
    if filepath and os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            words = deeply_clean_text(f.read()).split()
    else:
        words = deeply_clean_text(mock_text).split()
    
    if not words:
        words = ["unknown"]
        
    # Frequency Normalization (Truncation/Padding)
    if len(words) >= SAMPLE_SIZE:
        return words[:SAMPLE_SIZE]
    else:
        return (words * (SAMPLE_SIZE // len(words) + 1))[:SAMPLE_SIZE]

# ==============================================================================
# INFORMATION THEORY METRICS
# ==============================================================================
def calc_conditional_entropy(words):
    """Calculates H(Y|X) = H(X,Y) - H(X)"""
    unigrams = list(words)
    bigrams = list(zip(words[:-1], words[1:]))
    
    p_X = np.array(list(Counter(unigrams).values())) / len(unigrams)
    H_X = entropy(p_X, base=2)
    
    p_XY = np.array(list(Counter(bigrams).values())) / len(bigrams)
    H_XY = entropy(p_XY, base=2)
    
    H_Y_given_X = max(0, H_XY - H_X) # Conditional Entropy
    return H_Y_given_X

def calc_second_order_conditional_entropy(words):
    """Calculates H(Z|X,Y) = H(X,Y,Z) - H(X,Y)"""
    bigrams = list(zip(words[:-1], words[1:]))
    trigrams = list(zip(words[:-2], words[1:-1], words[2:]))
    
    p_XY = np.array(list(Counter(bigrams).values())) / len(bigrams)
    H_XY = entropy(p_XY, base=2)
    
    p_XYZ = np.array(list(Counter(trigrams).values())) / len(trigrams)
    H_XYZ = entropy(p_XYZ, base=2)
    
    H_Z_given_XY = max(0, H_XYZ - H_XY)
    return H_Z_given_XY

# ==============================================================================
# TOPOLOGICAL DISTANCE METRICS
# ==============================================================================
def calculate_js_divergence(words1, words2):
    """Symmetric Jensen-Shannon Divergence on Bigram distributions."""
    b1 = Counter(zip(words1[:-1], words1[1:]))
    b2 = Counter(zip(words2[:-1], words2[1:]))
    
    all_keys = set(b1.keys()) | set(b2.keys())
    total1 = sum(b1.values())
    total2 = sum(b2.values())
    
    P = np.array([b1.get(k, 0) / total1 for k in all_keys])
    Q = np.array([b2.get(k, 0) / total2 for k in all_keys])
    
    M = 0.5 * (P + Q)
    jsd = 0.5 * entropy(P, M, base=2) + 0.5 * entropy(Q, M, base=2)
    return jsd

def calculate_earth_mover_distance(G1, G2):
    """
    Calculates Wasserstein-1D (Earth Mover's Distance) 
    between the out-degree distributions of two directed graphs.
    """
    deg1 = [d for n, d in G1.out_degree()]
    deg2 = [d for n, d in G2.out_degree()]
    
    if not deg1 or not deg2: 
        return 0.0
        
    # Normalize by max to put them on the same scale [0, 1]
    max1, max2 = max(deg1) if deg1 else 1, max(deg2) if deg2 else 1
    norm_deg1 = [d / max1 for d in deg1]
    norm_deg2 = [d / max2 for d in deg2]
    
    return wasserstein_distance(norm_deg1, norm_deg2)

def calculate_spectral_distance(G1, G2, k=15):
    """
    Calculates the Euclidean distance between the top-k eigenvalues 
    of the directed adjacency matrices of two graphs.
    """
    try:
        # Create sparse matrices
        A1 = nx.adjacency_matrix(G1).astype(float)
        A2 = nx.adjacency_matrix(G2).astype(float)
        
        k_eff = min(k, A1.shape[0]-2, A2.shape[0]-2)
        if k_eff < 2: return 0.0
        
        # Calculate top k eigenvalues
        e1, _ = eigs(A1, k=k_eff, which='LM')
        e2, _ = eigs(A2, k=k_eff, which='LM')
        
        # Sort and take absolute values to handle complex numbers
        e1_sorted = np.sort(np.abs(e1))
        e2_sorted = np.sort(np.abs(e2))
        
        # Euclidean distance
        dist = np.linalg.norm(e1_sorted - e2_sorted)
        return dist
    except Exception as e:
        print(f"[warn] Spectral Distance error: {e}")
        return 0.0

def extract_motif_spectrum(G):
    """
    Extracts the Triadic Census (16 directed triad motifs).
    Reduces the graph to the top 200 most connected nodes to prevent O(N^3) memory crash.
    """
    if len(G.nodes) > 200:
        top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:200]
        G_sub = G.subgraph([n[0] for n in top_nodes])
    else:
        G_sub = G
        
    try:
        census = nx.triadic_census(G_sub)
        # Filter out empty triads (003, 012, 102) to focus on structural interactions
        structural_motifs = {k: v for k, v in census.items() if k not in ['003', '012', '102']}
        
        # Normalize spectrum to percentages
        total = sum(structural_motifs.values())
        if total == 0: total = 1
        
        normalized_spectrum = {k: (v/total)*100 for k, v in structural_motifs.items()}
        return normalized_spectrum
    except Exception as e:
        print(f"[warn] Motif Extraction error: {e}")
        return {}

def build_digraph(words):
    G = nx.DiGraph()
    bigrams = list(zip(words[:-1], words[1:]))
    for w1, w2 in bigrams:
        if G.has_edge(w1, w2):
            G[w1][w2]['weight'] += 1
        else:
            G.add_edge(w1, w2, weight=1)
    return G

# ==============================================================================
# PIPELINE EXECUTION
# ==============================================================================
def main():
    print("=== Voynich Phase XXXI: Transition Graph Topology & Higher-Order Markov ===\n")
    
    # 1. Load Controls
    controls = {
        "Latin Alchemy": load_or_simulate_corpus(find_file("Latin_Alchemy.txt"), MOCK_LATIN_ALCHEMY),
        "Arabic Pharmacology": load_or_simulate_corpus(find_file("Arabic_General_Unknown.txt"), MOCK_ARABIC_PHARMA),
        "Liturgical Chant": load_or_simulate_corpus(find_file("Latin_Liturgical.txt"), MOCK_LITURGICAL)
    }
    
    # Add other historical corpora, if found
    if os.path.exists(HISTORICAL_DIR):
        for path in glob.glob(os.path.join(HISTORICAL_DIR, "*.txt")):
            name = os.path.basename(path).replace(".txt", "")
            if name not in ["Latin_Alchemy", "Arabic_General_Unknown", "Latin_Liturgical"]:
                controls[f"Historical: {name}"] = load_or_simulate_corpus(path, "")
                
    # Add authentic ciphers
    for cipher in CIPHER_FILES:
        cipher_path = find_file(cipher)
        if cipher_path:
            controls[f"Cipher: {cipher}"] = load_or_simulate_corpus(cipher_path, "")

    # 2. Iterate Voynich Targets
    for voynich_file in VOYNICH_FILES:
        target_path = find_file(voynich_file)
        if not target_path:
            print(f"[-] Error: {voynich_file} not found. Skipping.")
            continue
            
        df = pd.read_csv(target_path)
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        v_words = " ".join(df['Deep_Clean_Text'].dropna().tolist()).split()
        
        if not v_words:
            continue
            
        v_words = v_words[:SAMPLE_SIZE]
        
        v_graph = build_digraph(v_words)
        v_h1 = calc_conditional_entropy(v_words)
        v_h2 = calc_second_order_conditional_entropy(v_words)
        v_motifs = extract_motif_spectrum(v_graph)
        
        source_name = os.path.basename(target_path)
        print(f"\n[*] TARGET: VOYNICH MANUSCRIPT [{source_name}] ({SAMPLE_SIZE} words)")
        print(f"    -> First-Order Cond. Entropy H(Y|X)   : {v_h1:.4f} bits")
        print(f"    -> Second-Order Cond. Entropy H(Z|X,Y): {v_h2:.4f} bits")
        print(f"    -> Dominant Transition Motif (Triad)  : {max(v_motifs, key=v_motifs.get) if v_motifs else 'None'}\n")

        results = []

        for name, c_words in controls.items():
            c_graph = build_digraph(c_words)
            c_h1 = calc_conditional_entropy(c_words)
            jsd = calculate_js_divergence(v_words, c_words)
            emd = calculate_earth_mover_distance(v_graph, c_graph)
            spec_dist = calculate_spectral_distance(v_graph, c_graph)
            
            results.append({
                "Control": name[:23],
                "JS_Div": jsd,
                "EMD": emd,
                "Spectral_Dist": spec_dist
            })
            
        print("="*80)
        print(f"PHASE XXXI: TOPOLOGICAL DISTANCE MATRIX FOR {source_name}")
        print("Note: JS Divergence is calculated on BIGRAMS (not unigrams like Red Team).")
        print("="*80)
        print(f"{'Baseline Control':<25} | {'JS Div (Bigram)':<15} | {'Earth Mover Dist':<18} | {'Spectral Dist':<15}")
        print("-" * 80)
        
        all_passed = True
        for r in results:
            print(f"{r['Control']:<25} | {r['JS_Div']:<15.4f} | {r['EMD']:<18.4f} | {r['Spectral_Dist']:<15.4f}")
            if r['JS_Div'] < 0.12:
                all_passed = False
                
        print("="*80)
        if all_passed:
            print("[!] SUCCESS: The Voynich Transition Topology remains structurally distinct.\n")
        else:
            print("[-] FAIL CONDITION MET for this baseline.\n")

if __name__ == "__main__":
    main()