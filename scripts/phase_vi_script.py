# VOYNICH MANUSCRIPT: PHYLOGENETIC PROFILING & SYNTACTIC CHAINS (PHASE VI)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import math
from collections import Counter
import numpy as np
import os

# Configuration
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Pre-computed Phase V results (Dynamic from 30 iterations)
PHASE_5_DATA = {
    "Voynich (RF1b-er)": (4.2815, 58.4354),
    "Voynich (ZL3b-n)": (4.3424, 56.5594),
    "Voynich (IT2a-n)": (4.1676, 56.6609),
    "RANDOM_HOAX_BASELINE": (14.1414, 131.5391),
    "German_Botany_Medicine": (10.0158, 52.3528),
    "German_Astronomy_Astrology": (8.6145, 43.5799),
    "German_History_Politics": (8.6201, 48.4662),
    "German_General_Unknown": (8.5670, 40.5298),
    "Latin_Alchemy": (10.0612, 77.6664),
    "Latin_Botany_Medicine": (11.1891, 69.7878),
    "Latin_Astronomy_Astrology": (9.9984, 75.0028),
    "Latin_General_Unknown": (9.7492, 62.4101),
    "Dutch_Botany_Medicine": (10.3331, 60.8292),
    "English_Theology_Religion": (8.3154, 42.1073),
    "Finnish_Astronomy_Astrology": (9.7319, 68.3931),
    "Hungarian_Theology_Religion": (11.1234, 65.7854),
    "Polish_Theology_Religion": (10.4819, 69.9855)
}

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'<>', ' ', text)
    text = re.sub(r'\$\w+', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def analyze_n_partite_chains(filepath, n_words):
    if not os.path.exists(filepath):
        return None

    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_corpus.split()
    
    if len(words) < n_words: return None
    
    ngrams = list(zip(*[words[i:] for i in range(n_words)]))
    ngram_counts = Counter(ngrams)
    
    counts = list(ngram_counts.values())
    multi_counts = [c for c in counts if c > 1]
    if not multi_counts: return None
    
    # Dynamic frequency threshold (99.5th percentile for trigrams to avoid noise)
    threshold = max(3, np.percentile(multi_counts, 99.5))
    
    valid_chains = {chain: count for chain, count in ngram_counts.items() if count >= threshold}
    sorted_chains = sorted(valid_chains.items(), key=lambda x: x[1], reverse=True)
    return sorted_chains

def calculate_phylogenetic_distances():
    names = list(PHASE_5_DATA.keys())
    perplexities = np.array([PHASE_5_DATA[name][0] for name in names])
    valencies = np.array([PHASE_5_DATA[name][1] for name in names])
    
    std_perp = np.std(perplexities)
    std_val = np.std(valencies)
    mean_perp = np.mean(perplexities)
    mean_val = np.mean(valencies)
    
    norm_perplexities = (perplexities - mean_perp) / std_perp
    norm_valencies = (valencies - mean_val) / std_val
    
    v_indices = [names.index(n) for n in names if "Voynich" in n]
    v_norm_perp = np.mean([norm_perplexities[i] for i in v_indices])
    v_norm_val = np.mean([norm_valencies[i] for i in v_indices])
    
    distances = []
    for i, name in enumerate(names):
        if "Voynich" in name: continue
        
        dist = math.sqrt((norm_perplexities[i] - v_norm_perp)**2 + (norm_valencies[i] - v_norm_val)**2)
        distances.append({
            "Corpus": name,
            "Phylogenetic_Distance": round(dist, 4)
        })
        
    return sorted(distances, key=lambda x: x['Phylogenetic_Distance'])

def main():
    print("=== Voynich Phase VI: Phylogenetic Profiling & Multi-Partite Chains ===\n")
    
    print("[*] STEP 1: VALIDATING 3-STEP (Trigram) AND 4-STEP (Tetragram) CHAINS")
    for filepath in VOYNICH_FILES:
        print(f"\n    [+] Source: {filepath.split('/')[-1]}")
        
        chains_3 = analyze_n_partite_chains(filepath, 3)
        if chains_3:
            print(f"        --- Top 5 Tripartite (3-word) Chains (Dynamic Threshold) ---")
            for chain, count in chains_3[:5]:
                print(f"        {count} occurrences: [ {' -> '.join(chain)} ]")
        else:
            print(f"        [-] No valid tripartite chains found.")
        
        chains_4 = analyze_n_partite_chains(filepath, 4)
        if chains_4:
            print(f"        --- Top 5 Quadrupartite (4-word) Chains (Dynamic Threshold) ---")
            for chain, count in chains_4[:5]:
                print(f"        {count} occurrences: [ {' -> '.join(chain)} ]")
        else:
            print(f"        [-] No valid quadrupartite chains found.")

    print("\n" + "="*70)
    print("[*] STEP 2: UNBIASED PHYLOGENETIC STRUCTURAL DISTANCE")
    print("    (Calculated via Standardized Euclidean Distance of Entropy & Valency)")
    print("    * Lower distance = Closer structural lineage to the Voynich Manuscript")
    print("="*70)
    
    phylo_distances = calculate_phylogenetic_distances()
    
    df_phylo = pd.DataFrame(phylo_distances)
    df_phylo.index = df_phylo.index + 1 
    print(df_phylo.to_string())
    
    print("\n=================================================================")
    print("PHASE VI COMPLETE.")
    print("=================================================================")

if __name__ == "__main__":
    main()
# ==============================================================================