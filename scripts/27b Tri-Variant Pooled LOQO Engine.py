# ==============================================================================
# VOYNICH MANUSCRIPT: TRI-VARIANT POOLED LOQO VALIDATION (PHASE XXVII-B)
# Hardened: Compares layout variations (A, B, C) under strict Quire-level isolation
# Target Environment: Google Colab
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
from sklearn.metrics import f1_score, matthews_corrcoef, precision_score, recall_score, accuracy_score, confusion_matrix
from tqdm import tqdm
warnings.filterwarnings("ignore")

# Configuration
TARGET_FILES = ["voynich_clean_data/RF1b-er_clean.csv"]
CHUNK_SIZE = 50
OVERLAP_SIZE = 5  # 10% sliding window buffer (5 words)
CLASSES = ["Herbal", "Astronomy", "Balneology", "Recipes"]

def deeply_clean_text(text):
    """Deeply cleans text of residual IVTFF transcriber markings."""
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_target_class(folio_str):
    """Maps physical folios to 4 strict visual categories."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return None
    num = int(match.group(1))
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    return None

def get_quire_id(folio_str):
    """Approximates historical Beinecke MS 408 quire structure (8-folio bounds)."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Quire_Unknown"
    num = int(match.group(1))
    quire_num = ((num - 1) // 8) + 1
    return f"Quire_{quire_num}"

# ==============================================================================
# DATASET GENERATORS
# ==============================================================================

def build_variant_A(df):
    """VARIANT A: Raw Layout - Line by Line (Maximum layout bias)."""
    docs, labels, quires = [], [], []
    for _, row in df.iterrows():
        text = str(row['Deep_Clean_Text']).strip()
        folio = str(row['Folio'])
        target = get_target_class(folio)
        if text and target:
            docs.append(text)
            labels.append(target)
            quires.append(get_quire_id(folio))
    return np.array(docs), np.array(labels), np.array(quires)

def build_variant_B(df):
    """VARIANT B: Soft Normalization - Page-level continuous flow."""
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, quires = [], [], []
    for _, row in folio_texts.iterrows():
        folio = row['Folio']
        target = get_target_class(folio)
        if not target: continue
        text = str(row['Deep_Clean_Text']).strip()
        if text:
            docs.append(text)
            labels.append(target)
            quires.append(get_quire_id(folio))
    return np.array(docs), np.array(labels), np.array(quires)

def build_variant_C(df):
    """VARIANT C: Hard Normalization - 50w chunks with 10% overlap."""
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
# EVALUATION ENGINE
# ==============================================================================

def run_pooled_loqo_evaluation(docs, labels, quires, variant_name):
    print(f"\n" + "="*80)
    print(f"[*] RUNNING POOLED LOQO ON: {variant_name}")
    print(f"    Total Documents: {len(docs)} | Unique Quires: {len(np.unique(quires))}")
    print("=" * 80)
    
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    logo = LeaveOneGroupOut()
    pooled_y_true = []
    pooled_y_pred = []
    
    # Manual fold-by-fold execution to pool predictions safely
    for train_idx, test_idx in logo.split(docs, labels, groups=quires):
        X_train, X_test = docs[train_idx], docs[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        pooled_y_true.extend(y_test)
        pooled_y_pred.extend(y_pred)
        
    pooled_y_true = np.array(pooled_y_true)
    pooled_y_pred = np.array(pooled_y_pred)
    
    # Calculate stable global metrics on pooled data
    f1 = f1_score(pooled_y_true, pooled_y_pred, average='macro')
    mcc = matthews_corrcoef(pooled_y_true, pooled_y_pred)
    acc = accuracy_score(pooled_y_true, pooled_y_pred)
    prec = precision_score(pooled_y_true, pooled_y_pred, average='macro')
    rec = recall_score(pooled_y_true, pooled_y_pred, average='macro')
    cm = confusion_matrix(pooled_y_true, pooled_y_pred, labels=CLASSES)
    
    print("\n    [POOLED OUT-OF-SAMPLE METRICS]:")
    print(f"    -> Accuracy       : {acc:.4f}")
    print(f"    -> Precision Macro: {prec:.4f}")
    print(f"    -> Recall Macro   : {rec:.4f}")
    print(f"    -> F1-Score Macro : {f1:.4f}")
    print(f"    -> Matthews CC    : {mcc:.4f}")
    
    print("\n    [CONFUSION MATRIX]:")
    print(pd.DataFrame(cm, index=[f"True_{c}" for c in CLASSES], columns=[f"Pred_{c}" for c in CLASSES]).to_string())
    
    return f1, mcc, acc

def main():
    print("=== Voynich Phase XXVII-B: Tri-Variant Pooled LOQO Validation ===\n")
    print("Locked KPI success target: F1 > 0.65 and MCC > 0.55 across B and C.\n")
    
    target_file = TARGET_FILES[0]
    if not os.path.exists(target_file):
        print(f"[-] Error: Data file {target_file} not found.")
        return
        
    df = pd.read_csv(target_file)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    df = df[df['Deep_Clean_Text'].str.strip() != '']
    
    # Run the Tri-Variant Pooled LOQO Pipeline
    f1_A, mcc_A, acc_A = run_pooled_loqo_evaluation(*build_variant_A(df), "VARIANT A (Raw Layout Lines)")
    f1_B, mcc_B, acc_B = run_pooled_loqo_evaluation(*build_variant_B(df), "VARIANT B (Soft Normalization - Page Level)")
    f1_C, mcc_C, acc_C = run_pooled_loqo_evaluation(*build_variant_C(df), "VARIANT C (Hard Normalization - 50w Chunks)")
    
    print("\n" + "="*80)
    print("PHASE XXVII-B METRIC COMPARISON MATRIX")
    print("="*80)
    print(f"{'Configuration':<45} | {'Accuracy':<10} | {'F1-Macro':<10} | {'Matthews CC':<10}")
    print("-" * 80)
    print(f"{'Variant A (Raw Layout Lines)':<45} | {acc_A:.4f}     | {f1_A:.4f}     | {mcc_A:.4f}")
    print(f"{'Variant B (Soft Page-level Flow)':<45} | {acc_B:.4f}     | {f1_B:.4f}     | {mcc_B:.4f}")
    print(f"{'Variant C (Hard 50w Chunks + Overlap)':<45} | {acc_C:.4f}     | {f1_C:.4f}     | {mcc_C:.4f}")
    print("="*80)
    print("\nPHASE XXVII-B COMPLETE. Analyze layout-dependency across unseen quires.")

if __name__ == "__main__":
    main()