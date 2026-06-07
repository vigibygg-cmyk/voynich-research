# VOYNICH MANUSCRIPT: LIGHTWEIGHT MASKED LANGUAGE MODELING (PHASE XXXII)
# Features: 70/30 Holdout, Laplace Smoothing, Competing Ontologies, Bootstrap CI
# Target Environment: Google Colab
# FIXED: Shuffled Ontology now shuffles words between classes, not just labels.
# FIXED: Historical controls get a mock ontology for fair comparison.
# FIXED (v3): Shifted from Latin to German Botany / Finnish to match Phase V/VI Phylogenetic proximity.
# FIXED (v4): Deterministic Sets, ZeroDivisionError protection, Cleaned Seed Logic.
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import math
import random
import warnings
from collections import Counter, defaultdict

warnings.filterwarnings("ignore")

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Fixed according to Phases V/VI: We use languages structurally (agglutinative/composite)
# are closest to the Voynich manuscript, to make the test as strict as possible.
HISTORICAL_CONTROLS = [
    "German_Botany_Medicine.txt",
    "Finnish_Astronomy_Astrology.txt"
]

HISTORICAL_DIR = "historical_corpora"

MASK_PROBABILITY = 0.15
TRAIN_RATIO = 0.70
BOOTSTRAP_ITERATIONS = 1000

# TRUE ONTOLOGY (Derived from Phases VII, XIV, XVII)
TRUE_ONTOLOGY = {
    "BASE": ['ol', 'qol', 'al', 'chol'],
    "STATE": ['s', 'or', 'ar', 'r', 'shedy', 'chey', 'char', 'tar', 'os', 'ches'],
    "DOSE": ['aiin', 'daiin', 'am', 'chedy', 'dar', 'qokeey', 'qokedy', 'shey'],
    "ENTITY": ['sho', 'cho', 'yto', 'yp', 'dyd', 'shdar', 'ot', 'oto'],
    "PROCEDURAL": ['lka', 'lkc', 'lky', 'lk']
}

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def find_file(filename):
    """Safely locates a file across Colab directories."""
    if os.path.exists(filename): return filename
    colab_path = os.path.join("/content", filename)
    if os.path.exists(colab_path): return colab_path
    for folder in ["voynich_clean_data", "historical_corpora"]:
        sub_path = os.path.join(folder, filename)
        if os.path.exists(sub_path): return sub_path
    for root, _, files in os.walk("."):
        if filename in files: return os.path.join(root, filename)
    return None

def load_corpus(filepath):
    """Loads and cleans the dataset into a flat list of words."""
    path = find_file(filepath)
    if not path: return []
    
    if path.endswith('.csv'):
        df = pd.read_csv(path)
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        return " ".join(df['Deep_Clean_Text'].dropna().tolist()).split()
    else:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return deeply_clean_text(f.read()).split()

# ==============================================================================
# COMPETING ONTOLOGIES GENERATOR
# ==============================================================================
def create_ontology_mappers(train_words, is_voynich=True):
    """Generates the True, Random, Frequency, and Shuffled ontologies."""
    # Resetuojame seed funkcijos lygmeniu klasifikacijai
    random.seed(42)
    unique_words = list(set(train_words))
    
    # 1. True Ontology Mapper
    true_mapper = {}
    
    if is_voynich:
        for cat, words in TRUE_ONTOLOGY.items():
            for w in words:
                true_mapper[w] = cat
    else:
        # Fix: Generate fake ontology for historical control texts,
        # since they lack Voynich words and True Ontology would not work there.
        word_counts = Counter(train_words)
        top_words = [w for w, c in word_counts.most_common(40)]
        mock_cats = ["MOCK_BASE", "MOCK_STATE", "MOCK_DOSE", "MOCK_ENTITY", "MOCK_PROCEDURAL"]
        for i, w in enumerate(top_words):
            true_mapper[w] = mock_cats[i % len(mock_cats)]
            
    # FIXED: sorted(set(...)) ensures deterministic iteration in all environments
    categories = sorted(set(true_mapper.values())) if true_mapper else ["DUMMY_CLASS"]
            
    # 2. Random Ontology Mapper
    random_mapper = {}
    if categories:
        for w in unique_words:
            if random.random() < 0.15:  # Reduce to ~15% coverage to match realistic ontology density
                random_mapper[w] = random.choice(categories)
            
    # 3. Frequency Pseudo-Ontology Mapper
    freq_mapper = {}
    word_counts = Counter(train_words)
    sorted_words = [w for w, c in word_counts.most_common()] if word_counts else []
    
    # FIXED: Apsauga nuo ZeroDivisionError trumpuose korpusuose
    chunk_size = max(1, len(sorted_words) // len(categories)) if categories else 1
    
    for i, w in enumerate(sorted_words):
        if random.random() < 0.15:
            cat_idx = min(i // chunk_size, len(categories) - 1)
            freq_mapper[w] = f"FREQ_CLASS_{cat_idx}"
            
    # 4. Shuffled Labels Ontology Mapper (FIXED LOGIC)
    # FIX: Now we truly shuffle word class dependencies!
    shuffled_mapper = {}
    mapped_words = list(true_mapper.keys())
    mapped_cats = list(true_mapper.values())
    random.shuffle(mapped_cats) # Swap the true values!
    
    for w, cat in zip(mapped_words, mapped_cats):
        shuffled_mapper[w] = cat
        
    return {
        "True_Ontology": true_mapper,
        "Random_Ontology": random_mapper,
        "Frequency_Ontology": freq_mapper,
        "Shuffled_Ontology": shuffled_mapper
    }

def get_class(word, mapper):
    """Returns the class of a word if it exists in the mapper, otherwise the word itself."""
    if not mapper: return word 
    return mapper.get(word, word)

# ==============================================================================
# MLM ENGINE (TRAINING & PREDICTION)
# ==============================================================================
class LightweightMLM:
    def __init__(self, ontology_mapper=None):
        self.ontology_mapper = ontology_mapper
        self.context_target_counts = defaultdict(Counter)
        self.context_totals = Counter()
        self.vocab = set()
        
    def train(self, words):
        """Builds trigram conditional probability tables: P(Target | Context_L, Context_R)"""
        for i in range(1, len(words) - 1):
            ctx_l = get_class(words[i-1], self.ontology_mapper)
            ctx_r = get_class(words[i+1], self.ontology_mapper)
            target = words[i]
            
            context = (ctx_l, ctx_r)
            self.context_target_counts[context][target] += 1
            self.context_totals[context] += 1
            self.vocab.add(target)
            
    def predict_log_prob(self, ctx_l, ctx_r, target):
        """Returns log2 probability with Laplace (Add-1) Smoothing."""
        context = (get_class(ctx_l, self.ontology_mapper), get_class(ctx_r, self.ontology_mapper))
        
        count_target = self.context_target_counts[context].get(target, 0)
        count_context = self.context_totals[context]
        vocab_size = len(self.vocab)
        
        # Laplace Smoothing: P(w|c) = (Count(c, w) + 1) / (Count(c) + |V|)
        prob = (count_target + 1) / (count_context + vocab_size)
        return math.log2(prob)

def calculate_bootstrap_ci(log_probs):
    """Calculates 95% Confidence Interval for Perplexity using Bootstrapping."""
    n = len(log_probs)
    if n == 0: return 0.0, 0.0
    
    perplexities = []
    for _ in range(BOOTSTRAP_ITERATIONS):
        sample = np.random.choice(log_probs, size=n, replace=True)
        avg_log_prob = np.mean(sample)
        perplexities.append(2 ** (-avg_log_prob))
        
    return np.percentile(perplexities, 2.5), np.percentile(perplexities, 97.5)

# ==============================================================================
# PIPELINE EXECUTION
# ==============================================================================
def run_mlm_evaluation(words, source_name, is_voynich=True):
    print(f"\n" + "="*80)
    print(f"[*] EXECUTING MLM PREDICTION BENCHMARK: [{source_name}]")
    print("="*80)
    
    # 1. 70/30 Strict Holdout Split
    split_idx = int(len(words) * TRAIN_RATIO)
    train_words = words[:split_idx]
    test_words = words[split_idx:]
    
    # FIXED: Edge case protection for short datasets
    if len(test_words) < 10:
        print(f"    [-] Test set too short ({len(test_words)} tokens). Skipping.")
        return
    
    print(f"    [i] Split: {len(train_words)} Train tokens | {len(test_words)} Unseen Test tokens.")
    
    # 2. Select Masked Indices in Test Set (15%)
    valid_indices = range(1, len(test_words) - 1)
    k_masks = int(len(test_words) * MASK_PROBABILITY)
    
    # FIXED: Reset seed here to ensure masked_indices are identical 
    # across all corpus evaluations regardless of prior mapping steps.
    random.seed(42)
    masked_indices = set(random.sample(valid_indices, k_masks))
    
    print(f"    [i] Masking {k_masks} target tokens in the Unseen Test Set.")
    
    # 3. Create Ontologies based strictly on Training Data
    mappers = create_ontology_mappers(train_words, is_voynich=is_voynich)
    mappers["Baseline_No_Ontology"] = None 
    
    results = {}
    
    for model_name, mapper in mappers.items():
        # Train Model
        mlm = LightweightMLM(ontology_mapper=mapper)
        mlm.train(train_words)
        
        # Test Model
        log_probs = []
        for i in masked_indices:
            ctx_l = test_words[i-1]
            ctx_r = test_words[i+1]
            target = test_words[i]
            
            lp = mlm.predict_log_prob(ctx_l, ctx_r, target)
            log_probs.append(lp)
            
        # Calculate Metrics
        avg_log_prob = np.mean(log_probs)
        perplexity = 2 ** (-avg_log_prob)
        ci_lower, ci_upper = calculate_bootstrap_ci(log_probs)
        
        results[model_name] = {
            "Perplexity": perplexity,
            "CI_Lower": ci_lower,
            "CI_Upper": ci_upper,
            "Entropy_Bits": -avg_log_prob
        }
        
    # Analyze and Output
    baseline_pp = results["Baseline_No_Ontology"]["Perplexity"]
    baseline_ent = results["Baseline_No_Ontology"]["Entropy_Bits"]
    
    print(f"\n    [PREDICTION METRICS ON MASKED TOKENS]")
    print(f"    {'Model Ontology':<25} | {'Perplexity':<10} | {'Δ Drop (↓ = better)':<18} | {'Info Gain (Bits)':<18} | {'95% CI (Perplexity)'}")
    print("-" * 105)
    
    for name, data in results.items():
        pp = data['Perplexity']
        pp_drop = baseline_pp - pp if name != "Baseline_No_Ontology" else 0.0
        ig = baseline_ent - data['Entropy_Bits'] if name != "Baseline_No_Ontology" else 0.0
        ci = f"[{data['CI_Lower']:.2f}, {data['CI_Upper']:.2f}]"
        
        # Added note regarding Frequency_Ontology independent space
        note = " (independent class space)" if name == "Frequency_Ontology" else ""
        
        print(f"    {name+note:<25} | {pp:<10.4f} | {pp_drop:>17.4f} | {ig:>16.4f} | {ci}")
        
    # Gating Logic
    true_drop = baseline_pp - results["True_Ontology"]["Perplexity"]
    shuf_drop = baseline_pp - results["Shuffled_Ontology"]["Perplexity"]
    rand_drop = baseline_pp - results["Random_Ontology"]["Perplexity"]
    
    print("\n    [GATING CRITERIA CHECK]")
    
    if true_drop > 0.15:
        print(f"    [+] True Ontology passed basic Perplexity Reduction threshold (Δ > 0.15).")
        
        # Check against False Ontologies
        if shuf_drop >= (0.8 * true_drop) or rand_drop >= (0.8 * true_drop):
            print(f"    [-] FAIL CONDITION MET: Pseudo-ontologies achieved >= 80% of the True gain.")
            print(f"        The 'True Ontology' is likely a statistical artifact of dimensionality reduction.")
        else:
            print(f"    [!] SUCCESS: True Ontology significantly outperformed adversarial ontologies.")
            print(f"        Latent Semantic Classes represent genuine, non-circular predictive structure.")
    else:
        print(f"    [-] FAIL CONDITION MET: True Ontology did not sufficiently reduce perplexity.")

def main():
    print("=== Voynich Phase XXXII: Lightweight Masked Language Modeling (MLM) ===")
    print("Objective: Test predictive validity of Latent Semantic Classes without circularity.")
    print("Guards: 70/30 Split, Laplace Smoothing, Competing Adversarial Ontologies.\n")
    print("Fixed: Deterministic Sets, ZeroDivisionError protection, Cleaned Seed Logic.\n")
    
    # Run on primary Voynich file
    target_file = TARGET_FILES[0]
    voynich_words = load_corpus(target_file)
    
    if voynich_words:
        run_mlm_evaluation(voynich_words, target_file.split('/')[-1], is_voynich=True)
    else:
        print(f"[-] Error: Could not load Voynich dataset {target_file}")
        return

    # Run on Historical Controls (Phylogenetically similar structures)
    for control_file in HISTORICAL_CONTROLS:
        control_words = load_corpus(control_file)
        if control_words:
            run_mlm_evaluation(control_words, f"{control_file} (Historical Control)", is_voynich=False)
        else:
            print(f"[-] Info: Historical control {control_file} not found locally, skipping.")
        
    print("\n=================================================================")
    print("PHASE XXXII COMPLETE. Evaluate the Information Gain (Bits).")
    print("=================================================================")

if __name__ == "__main__":
    main()
# ==============================================================================