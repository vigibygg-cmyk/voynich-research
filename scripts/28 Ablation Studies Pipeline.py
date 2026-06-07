# ==============================================================================
# VOYNICH MANUSCRIPT: SYSTEMATIC ABLATION STUDIES (PHASE XXVIII)
# Hardened: Quire-Aware GroupKFold, MCC, Wilcoxon Test & Cliff's Delta
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import warnings
from sklearn.model_selection import GroupKFold, cross_validate
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, matthews_corrcoef, make_scorer
from scipy.stats import wilcoxon
warnings.filterwarnings("ignore")

# Configuration
TARGET_FILES = ["voynich_clean_data/RF1b-er_clean.csv"]
N_SPLITS = 5
CHUNK_SIZE = 50
OVERLAP_SIZE = 5  # 10% sliding window buffer (5 words)
CLASSES = ["Herbal", "Astronomy", "Balneology", "Recipes"]

# Highly cohesive structural operators isolated blindly in Phase XIV SVD
FUNCTIONAL_OPERATORS = {
    'daiin', 'ol', 'aiin', 'chedy', 'shedy', 'chey', 'dar', 'qokeey', 'qokeedy', 
    'al', 'qokain', 'qokedy', 'shey', 'qokaiin', 'dal', 'am', 'iin', 
    'ar', 'or', 's', 'r', 'o', 'sar', 'char', 'd', 'tar', 'ches', 'sor', 'chos', 'cheos', 'lor', 'os'
}

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_target_class(folio_str):
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return None
    num = int(match.group(1))
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    return None

def get_quire_id(folio_str):
    """
    Groups folios into quires based on historical Beinecke MS 408 collation.
    Approximated using an 8-folio standard quire framework.
    """
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Quire_Unknown"
    num = int(match.group(1))
    quire_num = ((num - 1) // 8) + 1
    return f"Quire_{quire_num}"

def ablate_text(words, mode):
    """Systematically strips structural features from raw tokens."""
    ablated_words = []
    for w in words:
        if mode == "prefix":
            # Mask word-initial 2 characters
            ablated_words.append(w[2:] if len(w) > 2 else "")
        elif mode == "suffix":
            # Mask word-final 3 characters
            ablated_words.append(w[:-3] if len(w) > 3 else "")
        elif mode == "bpe":
            # Remove cohesive functional operators entirely
            if w not in FUNCTIONAL_OPERATORS:
                ablated_words.append(w)
        else:
            ablated_words.append(w)
    return " ".join([w for w in ablated_words if w != ""])

def build_variant_C_with_overlap(df, ablation_mode=None):
    """
    VARIANT C (Hard Normalization): 50-word chunks per folio, 
    integrated with a 10% sliding window buffer and feature ablation.
    """
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, groups, quires = [], [], [], []
    
    for _, row in folio_texts.iterrows():
        folio = row['Folio']
        target = get_target_class(folio)
        if not target: continue
        quire = get_quire_id(folio)
        
        words = row['Deep_Clean_Text'].split()
        if not words: continue
        
        # Apply ablation on the word stream before chunking
        if ablation_mode:
            processed_text = ablate_text(words, ablation_mode)
            words = processed_text.split()
            if not words: continue
            
        # Sliding Window Splitter (50 words, 5 words overlap)
        step = CHUNK_SIZE - OVERLAP_SIZE
        for i in range(0, len(words), step):
            chunk = words[i:i + CHUNK_SIZE]
            if len(chunk) >= (CHUNK_SIZE // 2):
                docs.append(" ".join(chunk))
                labels.append(target)
                groups.append(folio)
                quires.append(quire)
                
    return np.array(docs), np.array(labels), np.array(quires)

def calculate_cliffs_delta(x, y):
    """Calculates Cliff's Delta effect size for non-parametric distributions."""
    n1, n2 = len(x), len(y)
    greater = 0
    less = 0
    for i in x:
        for j in y:
            if i > j: greater += 1
            elif i < j: less += 1
    return (greater - less) / (n1 * n2)

def calculate_cohens_d(x, y):
    """Calculates Cohen's d effect size."""
    diff_mean = np.mean(x) - np.mean(y)
    pooled_std = np.sqrt((np.var(x, ddof=1) + np.var(y, ddof=1)) / 2)
    return diff_mean / pooled_std if pooled_std > 0 else 0.0

def evaluate_model_on_folds(docs, labels, quires):
    """Performs strict Quire-level split and returns raw fold metrics."""
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    cv = GroupKFold(n_splits=N_SPLITS)
    
    # Custom scoring dictionary to extract fold-by-fold MCC alongside F1
    mcc_scorer = make_scorer(matthews_corrcoef)
    scoring = {
        'f1_macro': 'f1_macro',
        'mcc': mcc_scorer
    }
    
    cv_results = cross_validate(pipeline, docs, labels, groups=quires, cv=cv, scoring=scoring, n_jobs=-1)
    return cv_results['test_f1_macro'], cv_results['test_mcc']

def main():
    print("=== Voynich Phase XXVIII: Systematic Ablation Studies ===")
    print("Locked KPI success target: F1 > 0.70 and MCC > 0.55 on Unseen Test Quires.\n")
    
    target_file = TARGET_FILES[0]
    if not os.path.exists(target_file):
        print(f"[-] Error: Data file {target_file} not found.")
        return
        
    df = pd.read_csv(target_file)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    df = df[df['Deep_Clean_Text'].str.strip() != '']
    
    # 1. Evaluate Baseline Model (Full Features)
    docs_full, labels_full, quires_full = build_variant_C_with_overlap(df, ablation_mode=None)
    full_f1, full_mcc = evaluate_model_on_folds(docs_full, labels_full, quires_full)
    
    print("-" * 80)
    print(f"[*] BASELINE MODEL (FULL FEATURES)")
    print(f"    Total Chunks: {len(docs_full)} | Unique Quires: {len(np.unique(quires_full))}")
    print(f"    -> Mean F1-Macro : {np.mean(full_f1):.4f} (+/- {np.std(full_f1):.4f})")
    print(f"    -> Mean MCC      : {np.mean(full_mcc):.4f} (+/- {np.std(full_mcc):.4f})")
    print("-" * 80)
    
    # Ablation Targets
    ablation_modes = ["prefix", "suffix", "bpe"]
    descriptions = {
        "prefix": "Removed word-initial 2 chars (-prefix)",
        "suffix": "Removed word-final 3 chars (-suffix)",
        "bpe": "Removed Phase XIV SVD Functional Terminals/Modifiers (-BPE)"
    }
    
    ablation_results = {}
    
    for mode in ablation_modes:
        print(f"\n[*] RUNNING ABLATION: [{descriptions[mode]}]")
        docs_abl, labels_abl, quires_abl = build_variant_C_with_overlap(df, ablation_mode=mode)
        abl_f1, abl_mcc = evaluate_model_on_folds(docs_abl, labels_abl, quires_abl)
        
        # Calculate statistics
        f1_drop = np.mean(full_f1) - np.mean(abl_f1)
        mcc_drop = np.mean(full_mcc) - np.mean(abl_mcc)
        
        # Wilcoxon Signed-Rank Test
        try:
            stat, p_val = wilcoxon(full_f1, abl_f1, alternative='greater')
        except ValueError:
            # Handles edge case of zero variance difference
            p_val = 1.0
            
        # Effect Sizes
        cohens_d = calculate_cohens_d(full_f1, abl_f1)
        cliffs_delta = calculate_cliffs_delta(full_f1, abl_f1)
        
        print(f"    -> Mean F1-Macro : {np.mean(abl_f1):.4f} (Drop: {f1_drop:+.4f})")
        print(f"    -> Mean MCC      : {np.mean(abl_mcc):.4f} (Drop: {mcc_drop:+.4f})")
        print(f"    -> Wilcoxon p-val: {p_val:.5f} ({'Significant' if p_val < 0.05 else 'Not Significant'})")
        print(f"    -> Cohen's d     : {cohens_d:.4f}")
        print(f"    -> Cliff's Delta : {cliffs_delta:.4f}")
        
        ablation_results[mode] = {
            "f1_mean": np.mean(abl_f1),
            "f1_drop": f1_drop,
            "p_val": p_val,
            "d": cohens_d
        }
        
    print("\n" + "="*80)
    print("PHASE XXVIII COMPLETE: SYSTEMATIC FEATURE IMPORTANCE MATRIX")
    print("="*80)
    print(f"{'Model Configuration':<30} | {'F1-Macro':<10} | {'F1 Drop':<10} | {'Wilcoxon p':<12} | {'Cohen d':<8}")
    print("-" * 80)
    print(f"{'Full Model (Baseline)':<30} | {np.mean(full_f1):.4f}     | {'0.0000':<10} | {'N/A':<12} | {'0.0000':<8}")
    for mode in ablation_modes:
        res = ablation_results[mode]
        print(f"{descriptions[mode][:28]:<30} | {res['f1_mean']:.4f}     | {res['f1_drop']:+.4f}    | {res['p_val']:.5f}     | {res['d']:.4f}")
    print("="*80)

if __name__ == "__main__":
    main()