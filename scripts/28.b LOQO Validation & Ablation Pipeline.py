# ==============================================================================
# VOYNICH MANUSCRIPT: POOLED LEAVE-ONE-QUIRE-OUT (LOQO) VALIDATION (PHASE XXVIII-B)
# Hardened: Solves Class-Quire Imbalance by pooling out-of-fold predictions
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

def ablate_text(words, mode):
    ablated_words = []
    for w in words:
        if mode == "prefix":
            ablated_words.append(w[2:] if len(w) > 2 else "")
        elif mode == "suffix":
            ablated_words.append(w[:-3] if len(w) > 3 else "")
        elif mode == "bpe":
            if w not in FUNCTIONAL_OPERATORS:
                ablated_words.append(w)
        else:
            ablated_words.append(w)
    return " ".join([w for w in ablated_words if w != ""])

def build_variant_C_with_overlap(df, ablation_mode=None):
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, quires = [], [], []
    
    for _, row in folio_texts.iterrows():
        folio = row['Folio']
        target = get_target_class(folio)
        if not target: continue
        quire = get_quire_id(folio)
        
        words = row['Deep_Clean_Text'].split()
        if not words: continue
        
        if ablation_mode:
            processed_text = ablate_text(words, ablation_mode)
            words = processed_text.split()
            if not words: continue
            
        step = CHUNK_SIZE - OVERLAP_SIZE
        for i in range(0, len(words), step):
            chunk = words[i:i + CHUNK_SIZE]
            if len(chunk) >= (CHUNK_SIZE // 2):
                docs.append(" ".join(chunk))
                labels.append(target)
                quires.append(quire)
                
    return np.array(docs), np.array(labels), np.array(quires)

def execute_pooled_loqo(docs, labels, quires):
    """
    Performs true Leave-One-Quire-Out (LOQO) validation and collects
    predictions globally before calculating metrics to prevent empty-fold bias.
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    logo = LeaveOneGroupOut()
    
    # Global arrays to store pooled out-of-fold predictions
    pooled_y_true = []
    pooled_y_pred = []
    
    # Manual loop with progress bar over the unique quires
    for train_idx, test_idx in logo.split(docs, labels, groups=quires):
        X_train, X_test = docs[train_idx], docs[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        pipeline.fit(X_train, y_train)
        y_pred = pipeline.predict(X_test)
        
        pooled_y_true.extend(y_test)
        pooled_y_pred.extend(y_pred)
        
    pooled_y_true = np.array(pooled_y_true)
    pooled_y_pred = np.array(pooled_y_pred)
    
    # Calculate stable global metrics
    f1 = f1_score(pooled_y_true, pooled_y_pred, average='macro')
    mcc = matthews_corrcoef(pooled_y_true, pooled_y_pred)
    acc = accuracy_score(pooled_y_true, pooled_y_pred)
    prec = precision_score(pooled_y_true, pooled_y_pred, average='macro')
    rec = recall_score(pooled_y_true, pooled_y_pred, average='macro')
    cm = confusion_matrix(pooled_y_true, pooled_y_pred, labels=CLASSES)
    
    return f1, mcc, acc, prec, rec, cm

def main():
    print("=== Voynich Phase XXVIII-B: Pooled LOQO & Ablation Engine ===")
    print("Pre-registered goal: Pooled Macro F1 > 0.70 and MCC > 0.55\n")
    
    target_file = TARGET_FILES[0]
    if not os.path.exists(target_file):
        print(f"[-] Error: Data file {target_file} not found.")
        return
        
    df = pd.read_csv(target_file)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    df = df[df['Deep_Clean_Text'].str.strip() != '']
    
    # 1. Evaluate Baseline Model (Full Features)
    print("[*] Training Baseline Model (14 LOQO folds, pooling predictions)...")
    docs_full, labels_full, quires_full = build_variant_C_with_overlap(df, ablation_mode=None)
    f1_full, mcc_full, acc_full, prec_full, rec_full, cm_full = execute_pooled_loqo(docs_full, labels_full, quires_full)
    
    print("-" * 80)
    print(f"[*] POOLED LOQO BASELINE PERFORMANCE (UNSEEN QUIRES):")
    print(f"    -> Accuracy       : {acc_full:.4f}")
    print(f"    -> Precision Macro: {prec_full:.4f}")
    print(f"    -> Recall Macro   : {rec_full:.4f}")
    print(f"    -> F1-Score Macro : {f1_full:.4f}")
    print(f"    -> Matthews CC    : {mcc_full:.4f}")
    print("\n    [CONFUSION MATRIX]:")
    print(pd.DataFrame(cm_full, index=[f"True_{c}" for c in CLASSES], columns=[f"Pred_{c}" for c in CLASSES]).to_string())
    print("-" * 80)
    
    # 2. Run Ablations
    ablation_modes = ["prefix", "suffix", "bpe"]
    descriptions = {
        "prefix": "Removed word-initial 2 chars (-prefix)",
        "suffix": "Removed word-final 3 chars (-suffix)",
        "bpe": "Removed SVD Functional Terminals/Modifiers (-BPE)"
    }
    
    ablation_results = {}
    
    for mode in ablation_modes:
        print(f"\n[*] RUNNING LOQO ABLATION: [{descriptions[mode]}]...")
        docs_abl, labels_abl, quires_abl = build_variant_C_with_overlap(df, ablation_mode=mode)
        f1_abl, mcc_abl, _, _, _, _ = execute_pooled_loqo(docs_abl, labels_abl, quires_abl)
        
        f1_drop = f1_full - f1_abl
        mcc_drop = mcc_full - mcc_abl
        
        print(f"    -> Mapped F1-Macro : {f1_abl:.4f} (Drop: {f1_drop:+.4f})")
        print(f"    -> Mapped MCC      : {mcc_abl:.4f} (Drop: {mcc_drop:+.4f})")
        
        ablation_results[mode] = {
            "f1_mean": f1_abl,
            "f1_drop": f1_drop,
            "mcc_mean": mcc_abl,
            "mcc_drop": mcc_drop
        }
        
    print("\n" + "="*80)
    print("PHASE XXVIII-B COMPLETE: SYSTEMATIC POOLED ABLATION MATRIX")
    print("="*80)
    print(f"{'Model Configuration':<30} | {'F1-Macro':<10} | {'F1 Drop':<10} | {'MCC':<10} | {'MCC Drop':<10}")
    print("-" * 80)
    print(f"{'Full Model (Baseline)':<30} | {f1_full:.4f}     | {'0.0000':<10} | {mcc_full:.4f}     | {'0.0000':<10}")
    for mode in ablation_modes:
        res = ablation_results[mode]
        print(f"{descriptions[mode][:28]:<30} | {res['f1_mean']:.4f}     | {res['f1_drop']:+.4f}    | {res['mcc_mean']:.4f}     | {res['mcc_drop']:+.4f}")
    print("="*80)

if __name__ == "__main__":
    main()