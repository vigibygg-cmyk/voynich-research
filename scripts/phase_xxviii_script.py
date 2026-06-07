# VOYNICH MANUSCRIPT: SYSTEMATIC ABLATION STUDIES (PHASE XXVIII)
# Hardened: Pipeline-Safe Masking, Quire-Aware GroupKFold, RIL, Bootstrap CI
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import warnings
from sklearn.base import BaseEstimator, TransformerMixin
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
ALPHA_LEVEL = 0.05 # Base significance level

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
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Quire_Unknown"
    num = int(match.group(1))
    quire_num = ((num - 1) // 8) + 1
    return f"Quire_{quire_num}"

# ==============================================================================
# PIPELINE-SAFE CUSTOM TRANSFORMER FOR ABLATION
# ==============================================================================
class TextAblator(BaseEstimator, TransformerMixin):
    """
    Custom Scikit-Learn Transformer to perform feature ablation strictly WITHIN 
    the cross-validation pipeline. This prevents global data leakage.
    """
    def __init__(self, mode=None):
        self.mode = mode

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        if not self.mode:
            return X
            
        ablated_X = []
        for doc in X:
            words = doc.split()
            ablated_words = []
            for w in words:
                if self.mode == "prefix":
                    ablated_words.append(w[2:] if len(w) > 2 else "")
                elif self.mode == "suffix":
                    ablated_words.append(w[:-3] if len(w) > 3 else "")
                elif self.mode == "bpe":
                    if w not in FUNCTIONAL_OPERATORS:
                        ablated_words.append(w)
                else:
                    ablated_words.append(w)
            ablated_X.append(" ".join([w for w in ablated_words if w != ""]))
            
        return np.array(ablated_X)

def build_raw_variant_C(df):
    """
    VARIANT C (Hard Normalization): 50-word chunks per folio with 10% overlap.
    Returns RAW text. Ablation happens later in the CV pipeline.
    """
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, quires = [], [], []
    
    for _, row in folio_texts.iterrows():
        folio = row['Folio']
        target = get_target_class(folio)
        if not target: continue
        quire = get_quire_id(folio)
        words = row['Deep_Clean_Text'].split()
        if not words: continue
        
        step = CHUNK_SIZE - OVERLAP_SIZE
        for i in range(0, len(words), step):
            chunk = words[i:i + CHUNK_SIZE]
            if len(chunk) >= (CHUNK_SIZE // 2):
                docs.append(" ".join(chunk))
                labels.append(target)
                quires.append(quire)
                
    return np.array(docs), np.array(labels), np.array(quires)

# ==============================================================================
# STATISTICAL METRICS (RIL, Cliff's Delta, Bootstrap CI)
# ==============================================================================
def calculate_cliffs_delta(x, y):
    n1, n2 = len(x), len(y)
    greater, less = 0, 0
    for i in x:
        for j in y:
            if i > j: greater += 1
            elif i < j: less += 1
    return (greater - less) / (n1 * n2)

def compute_paired_bootstrap_ci(baseline_scores, ablated_scores, n_bootstraps=10000):
    """Computes a 95% Confidence Interval for the F1 Drop using paired bootstrapping."""
    diffs = np.array(baseline_scores) - np.array(ablated_scores)
    bootstrapped_means = [np.mean(np.random.choice(diffs, size=len(diffs), replace=True)) for _ in range(n_bootstraps)]
    return np.percentile(bootstrapped_means, 2.5), np.percentile(bootstrapped_means, 97.5)

def evaluate_model_pipeline(docs, labels, quires, ablation_mode=None):
    """Executes the pipeline-safe GroupKFold cross-validation."""
    pipeline = Pipeline([
        ('ablator', TextAblator(mode=ablation_mode)),
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    cv = GroupKFold(n_splits=N_SPLITS)
    scoring = {'f1_macro': 'f1_macro', 'mcc': make_scorer(matthews_corrcoef)}
    
    cv_results = cross_validate(pipeline, docs, labels, groups=quires, cv=cv, scoring=scoring, n_jobs=-1)
    return cv_results['test_f1_macro'], cv_results['test_mcc']

def main():
    print("=== Voynich Phase XXVIII: Rigorous Feature Importance & Ablation ===")
    print("Upgrades: Pipeline-Safe Masking, Bonferroni Correction, RIL, Bootstrap CI\n")
    
    target_file = TARGET_FILES[0]
    if not os.path.exists(target_file):
        print(f"[-] Error: Data file {target_file} not found.")
        return
        
    df = pd.read_csv(target_file)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    df = df[df['Deep_Clean_Text'].str.strip() != '']
    
    # Generate Raw Variant C Base Dataset
    docs, labels, quires = build_raw_variant_C(df)
    
    print("-" * 90)
    print(f"[*] BASELINE MODEL (FULL FEATURES)")
    print(f"    Total Chunks: {len(docs)} | Unique Quires: {len(np.unique(quires))}")
    
    baseline_f1_folds, baseline_mcc_folds = evaluate_model_pipeline(docs, labels, quires, ablation_mode=None)
    baseline_f1_mean = np.mean(baseline_f1_folds)
    
    print(f"    -> Mean F1-Macro : {baseline_f1_mean:.4f} (+/- {np.std(baseline_f1_folds):.4f})")
    print(f"    -> Mean MCC      : {np.mean(baseline_mcc_folds):.4f} (+/- {np.std(baseline_mcc_folds):.4f})")
    print("-" * 90)
    
    ablation_modes = ["prefix", "suffix", "bpe"]
    descriptions = {
        "prefix": "Removed word-initial 2 chars (-prefix)",
        "suffix": "Removed word-final 3 chars (-suffix)",
        "bpe": "Removed Phase XIV SVD Operators (-BPE)"
    }
    
    # Calculate Bonferroni Adjusted Alpha
    adjusted_alpha = ALPHA_LEVEL / len(ablation_modes)
    print(f"[*] Statistical Rigor: Applying Bonferroni Correction (Adjusted Alpha = {adjusted_alpha:.4f})\n")
    
    results = []
    
    for mode in ablation_modes:
        print(f"[*] RUNNING ABLATION: [{descriptions[mode]}]")
        abl_f1_folds, abl_mcc_folds = evaluate_model_pipeline(docs, labels, quires, ablation_mode=mode)
        abl_f1_mean = np.mean(abl_f1_folds)
        
        # 1. Absolute Drop
        f1_drop = baseline_f1_mean - abl_f1_mean
        
        # 2. Relative Information Loss (RIL)
        ril = (f1_drop / baseline_f1_mean) * 100 if baseline_f1_mean > 0 else 0
        
        # 3. Paired Bootstrap Confidence Interval for the F1 Drop
        ci_lower, ci_upper = compute_paired_bootstrap_ci(baseline_f1_folds, abl_f1_folds)
        
        # 4. Wilcoxon & Cliff's Delta
        try:
            stat, p_val = wilcoxon(baseline_f1_folds, abl_f1_folds, alternative='greater')
        except ValueError:
            p_val = 1.0 # Edge case handling for exact ties
            
        cliffs_delta = calculate_cliffs_delta(baseline_f1_folds, abl_f1_folds)
        
        print(f"    -> Mean F1-Macro : {abl_f1_mean:.4f} (Absolute Drop: -{f1_drop:.4f})")
        print(f"    -> Relative Info Loss (RIL): {ril:.1f}% signal destroyed")
        print(f"    -> 95% Bootstrap CI (Drop) : [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"    -> Cliff's Delta           : {cliffs_delta:.4f} ({'Large' if cliffs_delta > 0.33 else 'Moderate/Small'})")
        print(f"    -> Wilcoxon p-value        : {p_val:.5f} ({'Significant' if p_val < adjusted_alpha else 'Not Significant'})")
        print()
        
        results.append({
            "Mode": descriptions[mode][:25],
            "F1": abl_f1_mean,
            "Drop": f1_drop,
            "RIL": ril,
            "Delta": cliffs_delta,
            "CI": f"[{ci_lower:.3f}, {ci_upper:.3f}]"
        })
        
    print("=" * 100)
    print("PHASE XXVIII COMPLETE: SYSTEMATIC FEATURE IMPORTANCE MATRIX")
    print("=" * 100)
    print(f"{'Ablation Target':<27} | {'F1-Macro':<10} | {'F1 Drop':<10} | {'RIL (%)':<10} | {'Cliff Î”':<10} | {'95% CI (Drop)'}")
    print("-" * 100)
    print(f"{'Baseline (Full Features)':<27} | {baseline_f1_mean:.4f}     | {'0.0000':<10} | {'0.0%':<10} | {'0.0000':<10} | N/A")
    for r in results:
        print(f"{r['Mode']:<27} | {r['F1']:.4f}     | -{r['Drop']:.4f}   | {r['RIL']:.1f}%      | {r['Delta']:.4f}     | {r['CI']}")
    print("=" * 100)

if __name__ == "__main__":
    main()
# ==============================================================================