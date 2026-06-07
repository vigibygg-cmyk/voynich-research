# ==============================================================================
# VOYNICH MANUSCRIPT: TRI-VARIANT GROUP K-FOLD & PERMUTATION TEST (PHASE XXVII)
# Optimized: GroupKFold cross-validation with aligned permutations and tqdm
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import warnings
from sklearn.model_selection import GroupKFold, cross_validate, cross_val_predict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, f1_score, confusion_matrix
from tqdm import tqdm
warnings.filterwarnings("ignore")

# Configuration
TARGET_FILES = ["voynich_clean_data/RF1b-er_clean.csv"]
N_SPLITS = 5
PERMUTATION_ITERATIONS = 1000
CHUNK_SIZE = 50
CLASSES = ["Herbal", "Astronomy", "Balneology", "Recipes"]

def deeply_clean_text(text):
    """Clean raw IVTFF text lines into standardized alphabetic streams."""
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_target_class(folio_str):
    """Identify the visual domain of the physical folio."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return None
    num = int(match.group(1))
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    return None

def build_variant_A(df):
    """VARIANT A: Raw Layout - Original lines (Prone to layout bias)."""
    docs, labels, groups = [], [], []
    for _, row in df.iterrows():
        text, folio = str(row['Deep_Clean_Text']).strip(), str(row['Folio'])
        target = get_target_class(folio)
        if text and target:
            docs.append(text); labels.append(target); groups.append(folio)
    return np.array(docs), np.array(labels), np.array(groups)

def build_variant_B(df):
    """VARIANT B: Soft Normalization - Preserves page order, removes line boundaries."""
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, groups = [], [], []
    for _, row in folio_texts.iterrows():
        target = get_target_class(row['Folio'])
        if target:
            text = str(row['Deep_Clean_Text']).strip()
            if text:
                docs.append(text); labels.append(target); groups.append(row['Folio'])
    return np.array(docs), np.array(labels), np.array(groups)

def build_variant_C(df):
    """VARIANT C: Hard Normalization - Continuous stream chunked into 50-word windows."""
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, groups = [], [], []
    for _, row in folio_texts.iterrows():
        target = get_target_class(row['Folio'])
        if target:
            words = row['Deep_Clean_Text'].split()
            for i in range(0, len(words), CHUNK_SIZE):
                chunk = words[i:i + CHUNK_SIZE]
                if len(chunk) >= (CHUNK_SIZE // 2):
                    docs.append(" ".join(chunk)); labels.append(target); groups.append(row['Folio'])
    return np.array(docs), np.array(labels), np.array(groups)

def run_evaluation(docs, labels, groups, variant_name):
    print(f"\n[*] EVALUATING {variant_name}")
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    cv = GroupKFold(n_splits=N_SPLITS)
    # Create group-constrained folds
    cv_iter = list(cv.split(docs, labels, groups))
    
    # 1. Calculate Standard Cross-Validation Metrics
    cv_results = cross_validate(pipeline, docs, labels, groups=groups, cv=cv, 
                                scoring=['f1_macro', 'precision_macro', 'recall_macro', 'accuracy'], n_jobs=-1)
    
    # 2. Out-of-fold predictions for Confusion Matrix
    y_pred = cross_val_predict(pipeline, docs, labels, cv=cv_iter, n_jobs=-1)
    
    print(f"    F1-Macro: {np.mean(cv_results['test_f1_macro']):.4f}")
    print("\n    [CONFUSION MATRIX]:")
    print(pd.DataFrame(confusion_matrix(labels, y_pred, labels=CLASSES), 
                       index=[f"True_{c}" for c in CLASSES], 
                       columns=[f"Pred_{c}" for c in CLASSES]))

    # 3. Permutation Test (Null Distribution) using global configuration
    print(f"\n    [*] Executing Permutation Test ({PERMUTATION_ITERATIONS} iterations)...")
    perm_scores = []
    rng = np.random.RandomState(42)
    
    for _ in tqdm(range(PERMUTATION_ITERATIONS), desc="    Calculating Permutations", leave=True):
        y_perm = rng.permutation(labels)
        res = cross_validate(pipeline, docs, y_perm, groups=groups, cv=cv, scoring='f1_macro', n_jobs=-1)
        perm_scores.append(np.mean(res['test_score']))
    
    p_val = (np.sum(np.array(perm_scores) >= np.mean(cv_results['test_f1_macro'])) + 1) / (PERMUTATION_ITERATIONS + 1)
    print(f"    P-value: {p_val:.5f}")

def main():
    df = pd.read_csv(TARGET_FILES[0])
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    run_evaluation(*build_variant_A(df), "VARIANT A")
    run_evaluation(*build_variant_B(df), "VARIANT B")
    run_evaluation(*build_variant_C(df), "VARIANT C")

if __name__ == "__main__":
    main()