# ==============================================================================
# VOYNICH MANUSCRIPT: RIGOROUS ABLATION PIPELINE (PHASE XXVIII V2)
# Hardened: Pipeline-safe masking, Bonferroni correction, Cliff's Delta, Bootstrap CI
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import warnings
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score
from sklearn.base import BaseEstimator, TransformerMixin
import scipy.stats as stats
warnings.filterwarnings("ignore")

# Configuration
TARGET_FILES = ["voynich_clean_data/RF1b-er_clean.csv"]
CHUNK_SIZE = 50
OVERLAP_SIZE = 5
CLASSES = ["Herbal", "Astronomy", "Balneology", "Recipes"]

# Structural functional operators (SVD Cluster XIV)
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

class PipelineAblator(BaseEstimator, TransformerMixin):
    def __init__(self, mode="none"):
        self.mode = mode
    def fit(self, X, y=None):
        return self
    def transform(self, X, y=None):
        ablated_X = []
        for text in X:
            words = text.split()
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
        return ablated_X

def build_dataset(df):
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, quires = [], [], []
    for _, row in folio_texts.iterrows():
        target = get_target_class(row['Folio'])
        if not target: continue
        quire = get_quire_id(row['Folio'])
        words = row['Deep_Clean_Text'].split()
        if not words: continue
        step = CHUNK_SIZE - OVERLAP_SIZE
        for i in range(0, max(1, len(words) - CHUNK_SIZE + 1), step):
            chunk = words[i:i + CHUNK_SIZE]
            if len(chunk) >= (CHUNK_SIZE // 2):
                docs.append(" ".join(chunk))
                labels.append(target)
                quires.append(quire)
    return np.array(docs), np.array(labels), np.array(quires)

def cliff_delta(x, y):
    n = len(x)
    m = len(y)
    mat = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            if x[i] > y[j]: mat[i,j] = 1
            elif x[i] < y[j]: mat[i,j] = -1
    return np.mean(mat)

def bootstrap_ci(x, y, n_boot=1000):
    diffs = []
    diff = x - y
    for _ in range(n_boot):
        sample = np.random.choice(diff, size=len(diff), replace=True)
        diffs.append(np.mean(sample))
    return np.percentile(diffs, [2.5, 97.5])

def execute_ablation(docs, labels, quires, mode):
    pipeline = Pipeline([
        ('ablator', PipelineAblator(mode=mode)),
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    logo = LeaveOneGroupOut()
    fold_f1 = []
    
    for train_idx, test_idx in logo.split(docs, labels, groups=quires):
        X_train, X_test = docs[train_idx], docs[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        # Only evaluate on non-empty test sets
        if len(np.unique(y_test)) > 0:
            pipeline.fit(X_train, y_train)
            y_pred = pipeline.predict(X_test)
            fold_f1.append(f1_score(y_test, y_pred, average='macro', labels=CLASSES))
        
    return np.array(fold_f1)

def main():
    print("=== Voynich Phase XXVIII V2: Rigorous Ablation Pipeline ===")
    df = pd.read_csv(TARGET_FILES[0])
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    docs, labels, quires = build_dataset(df)
    
    modes = ["none", "prefix", "suffix", "bpe"]
    results = {}
    
    for mode in modes:
        print(f"[*] Running {mode} ablation...")
        results[mode] = execute_ablation(docs, labels, quires, mode)
        
    base_f1 = results["none"]
    mean_base = np.mean(base_f1)
    print(f"\n[BASELINE] Full Features F1-Macro: {mean_base:.4f}")
    
    alpha = 0.01
    comparisons = len(modes) - 1
    bonferroni_alpha = alpha / comparisons
    
    for mode in modes[1:]:
        ablated_f1 = results[mode]
        mean_abl = np.mean(ablated_f1)
        ril = (mean_base - mean_abl) / mean_base
        delta = cliff_delta(base_f1, ablated_f1)
        ci_lower, ci_upper = bootstrap_ci(base_f1, ablated_f1)
        
        try:
            stat, pval = stats.wilcoxon(base_f1, ablated_f1, alternative='greater')
        except ValueError:
            pval = 1.0 # If zero differences
        
        print(f"\n[-] ABLATION: {mode}")
        print(f"    F1-Macro: {mean_abl:.4f} (RIL: {ril*100:.1f}% loss)")
        print(f"    Cliff's Delta: {delta:.3f}")
        print(f"    Bootstrap 95% CI (Difference): [{ci_lower:.4f}, {ci_upper:.4f}]")
        print(f"    Wilcoxon p-value: {pval:.5e}")
        
        if pval < bonferroni_alpha and delta > 0.33:
            print(f"    [!] SIGNIFICANT (Bonferroni alpha={bonferroni_alpha:.4f}): Feature '{mode}' is critical.")
        else:
            print("    [ ] NOT SIGNIFICANT: Feature impact does not meet strict criteria.")

if __name__ == "__main__":
    main()