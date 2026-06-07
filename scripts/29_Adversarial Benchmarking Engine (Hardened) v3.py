# ==============================================================================
# VOYNICH MANUSCRIPT: RIGOROUS NEGATIVE CONTROLS (PHASE XXIX)
# Patobulinta: GridSearchCV (cv=3), ilgio vienodinimas, Friedman testas, BPC suspaudimas
# Fixed: Authentic Voynich classes restored (Herbal, Astronomy, etc.)
# Aplinka: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import zlib
import warnings
from collections import defaultdict
from sklearn.model_selection import LeaveOneGroupOut, GridSearchCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, matthews_corrcoef, make_scorer
from scipy.stats import friedmanchisquare
warnings.filterwarnings("ignore")

# Configuration
VOYNICH_FILE = "voynich_clean_data/RF1b-er_clean.csv"
HISTORICAL_DIR = "historical_corpora"
CHUNK_SIZE = 50
OVERLAP_SIZE = 5
CLASSES = ["Sector_1", "Sector_2", "Sector_3", "Sector_4"]

# --- LATIN AND GERMAN SOURCE TEXTS FOR IMITATION ---
MOCK_MEDIEVAL_LATIN = "in nomine patris et filii et spiritus sancti amen recipe de herba dicta salutis " * 3000
MOCK_MEDIEVAL_RECIPES = "recipe succum de rubea et sal gemme et pulverem piperis et tere simul bene " * 3000

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_bpc(text):
    """Calculates bits per character (BPC), using ZLIB as an entropy indicator."""
    if not text: return 0.0
    encoded = text.encode('utf-8')
    compressed = zlib.compress(encoded, level=9)
    # BPC = (Compressed bytes * 8) / Total characters
    return (len(compressed) * 8) / len(text)

def generate_markov_pseudo_language(word_pool, length):
    """Generates synthetic language using 3-gram Markov chain from word pool."""
    model = defaultdict(list)
    for i in range(len(word_pool) - 3):
        state = tuple(word_pool[i:i+3])
        model[state].append(word_pool[i+3])
    
    current_state = list(model.keys())[np.random.randint(len(model))]
    output = list(current_state)
    for _ in range(length - 3):
        state = tuple(output[-3:])
        if state in model:
            output.append(np.random.choice(model[state]))
        else:
            output.append(np.random.choice(word_pool))
    return output

def build_adversarial_dataset(words, target_length):
    """Splits text into 14 fake quires and 4 fake thematic sectors."""
    # Strict length limit to avoid volume bias
    if len(words) > target_length:
        words = words[:target_length]
    elif len(words) < target_length:
        # Equalize length (bootstrapping) to target, if text too short
        words = (words * (target_length // len(words) + 1))[:target_length]

    words_per_chapter = len(words) // 14
    docs, labels, quires = [], [], []
    
    for ch in range(14):
        ch_start = ch * words_per_chapter
        ch_words = words[ch_start : ch_start + words_per_chapter]
        
        words_per_sector = len(ch_words) // 4
        if words_per_sector < 10: continue
            
        for s in range(4):
            sec_start = s * words_per_sector
            sec_words = ch_words[sec_start : sec_start + words_per_sector]
            
            step = CHUNK_SIZE - OVERLAP_SIZE
            for i in range(0, len(sec_words), step):
                chunk = sec_words[i:i + CHUNK_SIZE]
                if len(chunk) >= (CHUNK_SIZE // 2):
                    docs.append(" ".join(chunk))
                    labels.append(f"Sector_{s+1}")
                    quires.append(f"FakeQuire_{ch+1}")
                    
    return np.array(docs), np.array(labels), np.array(quires)

def get_voynich_target_class(folio_str):
    """Assigns original authentic classes to Voynich text."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return None
    num = int(match.group(1))
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    return None

def get_voynich_quire_id(folio_str):
    """Calculates true quire ID."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Quire_Unknown"
    num = int(match.group(1))
    quire_num = ((num - 1) // 8) + 1
    return f"Quire_{quire_num}"

def build_voynich_dataset(df):
    """Creates variant C baseline using REAL Voynich classes and quires."""
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, quires = [], [], []
    
    all_words = []
    
    for i, row in folio_texts.iterrows():
        words = str(row['Deep_Clean_Text']).split()
        if not words: continue
        all_words.extend(words)
        
        target = get_voynich_target_class(row['Folio'])
        if not target: continue
        quire = get_voynich_quire_id(row['Folio'])
        
        step = CHUNK_SIZE - OVERLAP_SIZE
        for j in range(0, len(words), step):
            chunk = words[j:j + CHUNK_SIZE]
            if len(chunk) >= (CHUNK_SIZE // 2):
                docs.append(" ".join(chunk))
                labels.append(target)
                quires.append(quire)
                
    return np.array(docs), np.array(labels), np.array(quires), all_words

def run_nested_loqo_validation(docs, labels, quires):
    """
    Performs 14-part "Leave-One-Quire-Out" cross-validation.
    Uses GridSearchCV (cv=3) on training set to avoid overfitting.
    """
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', random_state=42))
    ])
    
    param_grid = {
        'clf__C': [0.1, 1.0, 10.0]
    }
    
    logo = LeaveOneGroupOut()
    fold_mcc_scores = []
    
    for train_idx, test_idx in logo.split(docs, labels, groups=quires):
        X_train, X_test = docs[train_idx], docs[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        if len(np.unique(y_test)) < 2 or len(np.unique(y_train)) < 2:
            continue
            
        mcc_scorer = make_scorer(matthews_corrcoef)
        grid_search = GridSearchCV(pipeline, param_grid, cv=3, scoring=mcc_scorer, n_jobs=-1)
        grid_search.fit(X_train, y_train)
        
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)
        
        mcc = matthews_corrcoef(y_test, y_pred)
        fold_mcc_scores.append(mcc)
        
    return fold_mcc_scores

def load_control_corpus(filename, mock_text):
    path = os.path.join(HISTORICAL_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            return deeply_clean_text(f.read()).split()
    return deeply_clean_text(mock_text).split()

def main():
    print("=== Voynich manuscript (Phase XXIX): Negative control tests (Reinforced engine) ===\n")
    print("Improvements: Class assignment error fixed, authentic baseline restored.\n")
    
    if not os.path.exists(VOYNICH_FILE):
        print(f"[-] Error: Not found Voynich source file {VOYNICH_FILE}.")
        return
        
    v_df = pd.read_csv(VOYNICH_FILE)
    v_df['Deep_Clean_Text'] = v_df['Clean_Text'].apply(deeply_clean_text)
    
    # 1. Evaluate Voynich manuscript
    print("[*] STEP 1: PROCESSING VOYNICH TARGET TEXT (Nested LOQO + GridSearch)...")
    v_docs, v_labels, v_quires, v_words = build_voynich_dataset(v_df)
    v_target_length = len(v_words)
    v_bpc = calculate_bpc(" ".join(v_words))
    
    v_fold_mccs = run_nested_loqo_validation(v_docs, v_labels, v_quires)
    v_mean_mcc = np.mean(v_fold_mccs)
    print(f"    -> Average MCC across unseen folds: {v_mean_mcc:.4f} | Compression BPC: {v_bpc:.4f}")
    
    # 2. Prepare adversarial control texts
    adversaries = {
        "Natural Medieval Latin (Control A)": load_control_corpus("Latin_Prose.txt", MOCK_MEDIEVAL_LATIN),
        "Medieval Formulaic Recipes (Control B)": load_control_corpus("Latin_Alchemy.txt", MOCK_MEDIEVAL_RECIPES),
        "Markovian Pseudo-Language (Control C)": generate_markov_pseudo_language(v_words, length=v_target_length)
    }
    
    adv_results = {}
    statistical_distributions = [v_fold_mccs]
    
    print("\n[*] STEP 2: PROCESSING ADVERSARIAL CONTROL TEXTS (Equalizing length)...")
    for name, words in adversaries.items():
        print(f"    -> Vertinama: {name}")
        adv_docs, adv_labels, adv_quires = build_adversarial_dataset(words, target_length=v_target_length)
        adv_bpc = calculate_bpc(" ".join(words[:v_target_length]))
        
        adv_fold_mccs = run_nested_loqo_validation(adv_docs, adv_labels, adv_quires)
        adv_mean_mcc = np.mean(adv_fold_mccs)
        
        print(f"       Average MCC: {adv_mean_mcc:.4f} | BPC: {adv_bpc:.4f} | MCC gap to VM: {v_mean_mcc - adv_mean_mcc:+.4f}")
        
        adv_results[name] = {"mcc": adv_mean_mcc, "bpc": adv_bpc, "gap": v_mean_mcc - adv_mean_mcc}
        statistical_distributions.append(adv_fold_mccs)
        
    # 3. Statistinis testavimas
    print("\n[*] STEP 3: NON-PARAMETRIC STATISTICAL TESTING (Friedman test)")
    
    min_folds = min(len(dist) for dist in statistical_distributions)
    trimmed_distributions = [dist[:min_folds] for dist in statistical_distributions]
    
    stat, p_val = friedmanchisquare(*trimmed_distributions)
    
    print("="*90)
    print("PHASE XXIX COMPLETED: REINFORCED CONTROL TESTS COMPARISON MATRIX")
    print("="*90)
    print(f"{'Corpus name':<42} | {'Average MCC':<10} | {'MCC gap':<10} | {'Compress. (BPC)':<12}")
    print("-" * 90)
    print(f"{'Voynich manuscript (Baseline)':<42} | {v_mean_mcc:.4f}     | {'0.0000':<10} | {v_bpc:.4f} bits/symbol")
    
    for name, res in adv_results.items():
        print(f"{name:<42} | {res['mcc']:.4f}     | {res['gap']:+.4f}    | {res['bpc']:.4f} bitai/simbolis")
    print("="*90)
    
    print(f"\n[STATISTICAL SIGNIFICANCE]: Friedman test p-value = {p_val:.6e}")
    if p_val < 0.05:
        print("[!] SUCCESS: MCC score difference is statistically significant (p < 0.05).")
    else:
        print("[-] FAILURE: Models behave identically statistically across unseen folds.")

if __name__ == "__main__":
    main()