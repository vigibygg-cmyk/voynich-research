# ==============================================================================
# VOYNICH MANUSCRIPT: TRI-VARIANT GROUP K-FOLD & PERMUTATION TEST (PHASE XXVII V2)
# Hardened: Quire-Aware GroupKFold, MCC Metrics, Overlapping Chunks
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import warnings
from sklearn.model_selection import GroupKFold, cross_validate, cross_val_predict, permutation_test_score
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, matthews_corrcoef, confusion_matrix, make_scorer
from tqdm import tqdm
warnings.filterwarnings("ignore")

# Configuration
TARGET_FILES = ["voynich_clean_data/RF1b-er_clean.csv"]
N_SPLITS = 5
PERMUTATION_ITERATIONS = 1000
CHUNK_SIZE = 50
OVERLAP_SIZE = 5
STEP_SIZE = CHUNK_SIZE - OVERLAP_SIZE
CLASSES = ["Herbal", "Astronomy", "Balneology", "Recipes"]

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

def build_variant_A(df):
    """VARIANT A: Raw Layout - Original lines"""
    docs, labels, groups = [], [], []
    for _, row in df.iterrows():
        text, folio = str(row['Deep_Clean_Text']).strip(), str(row['Folio'])
        target = get_target_class(folio)
        if text and target:
            docs.append(text); labels.append(target); groups.append(get_quire_id(folio))
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
                docs.append(text); labels.append(target); groups.append(get_quire_id(row['Folio']))
    return np.array(docs), np.array(labels), np.array(groups)

def build_variant_C(df):
    """VARIANT C: Hard Normalization - Continuous stream chunked into overlapping windows."""
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, groups = [], [], []
    for _, row in folio_texts.iterrows():
        target = get_target_class(row['Folio'])
        if target:
            words = row['Deep_Clean_Text'].split()
            for i in range(0, max(1, len(words) - CHUNK_SIZE + 1), STEP_SIZE):
                chunk = words[i:i + CHUNK_SIZE]
                if len(chunk) >= (CHUNK_SIZE // 2):
                    docs.append(" ".join(chunk)); labels.append(target); groups.append(get_quire_id(row['Folio']))
    return np.array(docs), np.array(labels), np.array(groups)

def run_evaluation(docs, labels, groups, variant_name):
    print(f"\n[*] EVALUATING {variant_name}")
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    cv = GroupKFold(n_splits=N_SPLITS)
    cv_iter = list(cv.split(docs, labels, groups))
    
    scoring = {
        'f1_macro': make_scorer(f1_score, average='macro'),
        'mcc': make_scorer(matthews_corrcoef)
    }
    
    cv_results = cross_validate(pipeline, docs, labels, groups=groups, cv=cv, scoring=scoring, n_jobs=-1)
    y_pred = cross_val_predict(pipeline, docs, labels, cv=cv_iter, n_jobs=-1)
    
    f1_mean = np.mean(cv_results['test_f1_macro'])
    mcc_mean = np.mean(cv_results['test_mcc'])
    
    print(f"    F1-Macro: {f1_mean:.4f}")
    print(f"    MCC:      {mcc_mean:.4f}")
    print("\n    [CONFUSION MATRIX]:")
    print(pd.DataFrame(confusion_matrix(labels, y_pred, labels=CLASSES), 
                       index=[f"True_{c}" for c in CLASSES], 
                       columns=[f"Pred_{c}" for c in CLASSES]))

    print(f"\n    [*] Executing Permutation Test ({PERMUTATION_ITERATIONS} iterations)...")
    score, permutation_scores, pvalue = permutation_test_score(
        pipeline, docs, labels, groups=groups, scoring='f1_macro', cv=cv, 
        n_permutations=PERMUTATION_ITERATIONS, n_jobs=-1, random_state=42
    )
    print(f"    P-value: {pvalue:.5f}")

    if f1_mean >= 0.70 and mcc_mean > 0.55 and pvalue < 0.01:
        print("    [!] SALYGA ISPILDYTA: KPI uzraktas atrakintas. Leidziama pereiti i P28.")
    else:
        print("    [-] SALYGA NEISPILDYTA: Modelio tikslumas per zemas (Macro-F1 >= 0.70, MCC > 0.55, p < 0.01).")

def main():
    df = pd.read_csv(TARGET_FILES[0])
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    run_evaluation(*build_variant_A(df), "VARIANT A")
    run_evaluation(*build_variant_B(df), "VARIANT B")
    run_evaluation(*build_variant_C(df), "VARIANT C")

if __name__ == "__main__":
    main()