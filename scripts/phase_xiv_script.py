# VOYNICH MANUSCRIPT: SVD FUNCTIONAL CLUSTERING (PHASE XIV)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import random
from collections import defaultdict, Counter
from sklearn.decomposition import TruncatedSVD
from sklearn.cluster import KMeans

# Configuration
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
MIN_WORD_FREQ = 10     # Exclude rare words to prevent matrix noise
NUM_CLUSTERS = 4       # We hypothesize ~4 functional classes (e.g., Prefix, Core, Suffix, Connector)
SVD_COMPONENTS = 10    # Dimensionality reduction target

def deeply_clean_text(text):
    """Deeply cleans text of residual transcriber marks."""
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def generate_hoax_words(words):
    """
    Shuffles words globally. This destroys left/right topological syntax
    while preserving exact word frequencies.
    """
    shuffled = words.copy()
    random.shuffle(shuffled)
    return shuffled

def build_topological_matrix(words):
    """
    Builds a Left-Right neighborhood matrix. For every word, it records 
    the exact frequencies of words immediately preceding and following it.
    """
    word_counts = Counter(words)
    all_counts = list(word_counts.values())
    threshold = max(5, np.percentile(all_counts, 95)) if all_counts else 5
    valid_words = [w for w, c in word_counts.items() if c >= threshold]
    word_to_index = {w: i for i, w in enumerate(valid_words)}
    
    vocab_size = len(valid_words)
    
    # Left and Right topological boundary matrices
    left_matrix = np.zeros((vocab_size, vocab_size))
    right_matrix = np.zeros((vocab_size, vocab_size))
    
    for i in range(1, len(words) - 1):
        target = words[i]
        left_neighbor = words[i - 1]
        right_neighbor = words[i + 1]
        
        if target in word_to_index:
            t_idx = word_to_index[target]
            if left_neighbor in word_to_index:
                l_idx = word_to_index[left_neighbor]
                left_matrix[t_idx, l_idx] += 1
            if right_neighbor in word_to_index:
                r_idx = word_to_index[right_neighbor]
                right_matrix[t_idx, r_idx] += 1
                
    # Combine both directional spaces horizontally
    combined_matrix = np.hstack((left_matrix, right_matrix))
    
    # Normalize rows to L1 norm (probabilities)
    row_sums = combined_matrix.sum(axis=1)
    row_sums[row_sums == 0] = 1 # Prevent division by zero
    normalized_matrix = combined_matrix / row_sums[:, np.newaxis]
    
    return normalized_matrix, valid_words, word_counts

def apply_svd_and_clustering(matrix, words_list):
    """
    Applies TruncatedSVD for noise reduction and KMeans for blind functional clustering.
    """
    # 1. Dimensionality Reduction
    svd = TruncatedSVD(n_components=SVD_COMPONENTS, random_state=42)
    reduced_matrix = svd.fit_transform(matrix)
    
    # 2. Unsupervised Clustering
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(reduced_matrix)
    
    # 3. Group words by identified cluster
    clusters = defaultdict(list)
    for i, word in enumerate(words_list):
        clusters[cluster_labels[i]].append(word)
        
    return clusters

def execute_pipeline(filepath, is_hoax=False):
    """Runs the complete clustering pipeline for a given text source."""
    if not os.path.exists(filepath):
        return
        
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    full_text = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_text.split()
    
    if is_hoax:
        source_name = "RANDOM_HOAX_BASELINE"
        words = generate_hoax_words(words)
    else:
        source_name = filepath.split('/')[-1]
        
    print(f"\n" + "="*70)
    print(f"[*] EXECUTING SVD CLUSTERING: [{source_name}]")
    print("="*70)
    
    matrix, valid_words, word_counts = build_topological_matrix(words)
    
    if len(valid_words) < max(NUM_CLUSTERS, SVD_COMPONENTS):
        print("    [-] Insufficient valid words for SVD clustering.")
        return
        
    print(f"    [i] Topological Matrix built for {len(valid_words)} unique words.")
    
    # Execute blind clustering
    clusters = apply_svd_and_clustering(matrix, valid_words)
    
    # Output Results
    for cluster_id, cluster_words in clusters.items():
        # Sort words in this cluster by their absolute frequency in the text
        # This helps easily identify what the cluster represents functionally
        sorted_words = sorted(cluster_words, key=lambda w: word_counts[w], reverse=True)
        top_elements = sorted_words[:15] # Display top 15
        
        print(f"\n    [+] ISOLATED FUNCTIONAL CLUSTER #{cluster_id} (Size: {len(cluster_words)} words)")
        print(f"        -> Dominant Nodes: {', '.join(top_elements)}")

def main():
    print("=== Voynich Phase XIV: Tabula Rasa SVD Topological Clustering ===\n")
    print("Objective: Mathematically test Earnhart's 'Paper Computer' theory.")
    print("If the cipher uses predetermined syntax slots, SVD will blindly separate")
    print("prefixes from suffixes entirely based on left/right neighborhood patterns.\n")
    
    # 1. Authentic Transcriptions (Triangulation)
    for filepath in VOYNICH_FILES:
        if os.path.exists(filepath):
            execute_pipeline(filepath)
        else:
            print(f"[-] Error: {filepath} not found.")
            
    # 2. Chaos Control Baseline
    if VOYNICH_FILES and os.path.exists(VOYNICH_FILES[0]):
        execute_pipeline(VOYNICH_FILES[0], is_hoax=True)
        
    print("\n=================================================================")
    print("PHASE XIV COMPLETE. Evaluate functional cluster purity.")
    print("=================================================================")

if __name__ == "__main__":
    main()
# ==============================================================================