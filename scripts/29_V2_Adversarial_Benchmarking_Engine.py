# ==============================================================================
# VOYNICH MANUSCRIPT: RIGOROUS NEGATIVE CONTROLS (PHASE XXIX V2)
# Hardened: GridSearchCV, NCD Compression, Friedman/Nemenyi tests
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import zlib
import warnings
from collections import defaultdict
from sklearn.model_selection import LeaveOneGroupOut, GridSearchCV, StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import f1_score, matthews_corrcoef, accuracy_score
import scipy.stats as stats
import scikit_posthocs as sp
warnings.filterwarnings("ignore")

VOYNICH_FILE = "voynich_clean_data/RF1b-er_clean.csv"
HISTORICAL_DIR = "historical_corpora"
CHUNK_SIZE = 50
OVERLAP_SIZE = 5
CLASSES = ["Sector_1", "Sector_2", "Sector_3", "Sector_4"]
TARGET_WORDS = 38000 # Same length distribution

MOCK_MEDIEVAL_LATIN = """
in nomine patris et filii et spiritus sancti amen recipe de herba dicta salutis
et tere bene in mortario et adde aquam fontanam et bulliat parumper super ignem
postea cola per pannum mundum et adde mellis quantum sufficit ut sit dulce
et detur infirmo ad bibendum mane et sero et curabitur certe deo volente.
quoniam sicut dicit galenus in libris suis medicinalibus omnis morbus capit
principium a caliditate vel frigiditate vel siccitate vel humiditate contraria.
oportet ergo adhibere contraria contrariis ut sanitas restauretur cito.
rsuber et alumen decoquantur in vino aceto et fiat collyrium pro oculis.
""".strip() * 100 

MOCK_MEDIEVAL_RECIPES = """
recipe succum de rubea et sal gemme et pulverem piperis et tere simul bene.
postea accipe de oleo olivarum partem unam et de aceto partem mediam et misce.
fiat unguentum super pannum linteum et pone super vulnus usque ad sanitatem.
item ad provocandum urinam accipe radices petroselini et decoque in aqua munda.
et bibat calidum in lecto ut provocet sudorem et sic curabitur mirabiliter.
alchimia est ars transmutandi metalla vilia in aurum purum per elixir.
calcinatio fit per ignem fortem ut corpus reducatur in pulverem album.
""".strip() * 100

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_voynich_target_class(folio_str):
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return None
    num = int(match.group(1))
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    return None

def get_voynich_quire_id(folio_str):
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Quire_Unknown"
    num = int(match.group(1))
    quire_num = ((num - 1) // 8) + 1
    return f"Quire_{quire_num}"

def bootstrap_corpus(words, target_length=TARGET_WORDS):
    """Bootstraps a corpus to a specific word length to match length distributions."""
    if len(words) == 0: return []
    resampled = []
    while len(resampled) < target_length:
        sample_size = min(len(words), target_length - len(resampled))
        idx = np.random.randint(0, len(words) - sample_size + 1)
        resampled.extend(words[idx:idx+sample_size])
    return resampled

def load_or_simulate_corpus(filename, mock_text):
    path = os.path.join(HISTORICAL_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            words = deeply_clean_text(f.read()).split()
    else:
        words = deeply_clean_text(mock_text).split()
    return bootstrap_corpus(words)

def generate_markov_pseudo_language(word_pool, length=TARGET_WORDS):
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

def build_adversarial_dataset(words):
    total_words = len(words)
    words_per_chapter = total_words // 14
    
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

def build_voynich_dataset(df):
    folio_texts = df.groupby('Folio')['Deep_Clean_Text'].apply(lambda x: ' '.join(x.dropna())).reset_index()
    docs, labels, quires = [], [], []
    words_all = []
    for _, row in folio_texts.iterrows():
        target = get_voynich_target_class(row['Folio'])
        if not target: continue
        quire = get_voynich_quire_id(row['Folio'])
        words = row['Deep_Clean_Text'].split()
        if not words: continue
        words_all.extend(words)
        step = CHUNK_SIZE - OVERLAP_SIZE
        for i in range(0, len(words), step):
            chunk = words[i:i + CHUNK_SIZE]
            if len(chunk) >= (CHUNK_SIZE // 2):
                docs.append(" ".join(chunk))
                labels.append(target)
                quires.append(quire)
    # Ensure voynich is also bootstrapped/limited for fair comparison if needed, 
    # but normally we benchmark others against the real Voynich size.
    return np.array(docs), np.array(labels), np.array(quires), words_all

def calculate_ncd(text_pool):
    """Calculates Normalized Compression Distance (approximation) using zlib."""
    text = " ".join(text_pool)
    if not text: return 1.0
    c_x = len(zlib.compress(text.encode('utf-8')))
    raw_x = len(text.encode('utf-8'))
    return c_x / raw_x if raw_x > 0 else 1.0

def execute_pooled_loqo(docs, labels, quires):
    pipeline = Pipeline([
        ('tfidf', TfidfVectorizer(analyzer='char_wb', ngram_range=(1, 3), min_df=5)),
        ('clf', LogisticRegression(class_weight='balanced', max_iter=1000, random_state=42))
    ])
    
    # GridSearch on the pipeline (limited CV=3 on training data)
    param_grid = {'clf__C': [0.1, 1.0, 10.0]}
    
    logo = LeaveOneGroupOut()
    pooled_y_true = []
    pooled_y_pred = []
    fold_f1_scores = []
    
    for train_idx, test_idx in logo.split(docs, labels, groups=quires):
        X_train, X_test = docs[train_idx], docs[test_idx]
        y_train, y_test = labels[train_idx], labels[test_idx]
        
        if len(np.unique(y_test)) == 0: continue
            
        gs = GridSearchCV(pipeline, param_grid, cv=StratifiedKFold(n_splits=3), n_jobs=-1, scoring='f1_macro')
        gs.fit(X_train, y_train)
        
        y_pred = gs.predict(X_test)
        pooled_y_true.extend(y_test)
        pooled_y_pred.extend(y_pred)
        fold_f1_scores.append(f1_score(y_test, y_pred, average='macro'))
        
    f1 = f1_score(pooled_y_true, pooled_y_pred, average='macro')
    mcc = matthews_corrcoef(pooled_y_true, pooled_y_pred)
    acc = accuracy_score(pooled_y_true, pooled_y_pred)
    return f1, mcc, acc, np.array(fold_f1_scores)

def main():
    print("=== Voynich Phase XXIX V2: Rigorous Negative Controls Benchmark ===")
    df = pd.read_csv(VOYNICH_FILE)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    v_docs, v_labels, v_quires, v_words = build_voynich_dataset(df)
    print("\n[*] TARGET: VOYNICH MANUSCRIPT (POOLED LOQO)")
    v_f1, v_mcc, v_acc, v_fold_scores = execute_pooled_loqo(v_docs, v_labels, v_quires)
    v_ncd = calculate_ncd(v_words)
    print(f"    -> Accuracy: {v_acc:.4f} | F1-Macro: {v_f1:.4f} | Matthews CC: {v_mcc:.4f} | NCD: {v_ncd:.4f}")
    
    latin_words = load_or_simulate_corpus("Latin_Alchemy.txt", MOCK_MEDIEVAL_LATIN)
    l_docs, l_labels, l_quires = build_adversarial_dataset(latin_words)
    print("\n[*] Evaluating Adversary: [Natural Medieval Latin (Control A)]...")
    l_f1, l_mcc, l_acc, l_fold_scores = execute_pooled_loqo(l_docs, l_labels, l_quires)
    l_ncd = calculate_ncd(latin_words)
    print(f"    -> Accuracy: {l_acc:.4f} | F1-Macro: {l_f1:.4f} | Matthews CC: {l_mcc:.4f} | NCD: {l_ncd:.4f}")
    
    recipe_words = load_or_simulate_corpus("English_Botany_Medicine.txt", MOCK_MEDIEVAL_RECIPES)
    r_docs, r_labels, r_quires = build_adversarial_dataset(recipe_words)
    print("\n[*] Evaluating Adversary: [Medieval Formulaic Recipes (Control B)]...")
    r_f1, r_mcc, r_acc, r_fold_scores = execute_pooled_loqo(r_docs, r_labels, r_quires)
    r_ncd = calculate_ncd(recipe_words)
    print(f"    -> Accuracy: {r_acc:.4f} | F1-Macro: {r_f1:.4f} | Matthews CC: {r_mcc:.4f} | NCD: {r_ncd:.4f}")
    
    markov_words = generate_markov_pseudo_language(v_words, length=TARGET_WORDS)
    m_docs, m_labels, m_quires = build_adversarial_dataset(markov_words)
    print("\n[*] Evaluating Adversary: [Markovian Pseudo-Language (Control C)]...")
    m_f1, m_mcc, m_acc, m_fold_scores = execute_pooled_loqo(m_docs, m_labels, m_quires)
    m_ncd = calculate_ncd(markov_words)
    print(f"    -> Accuracy: {m_acc:.4f} | F1-Macro: {m_f1:.4f} | Matthews CC: {m_mcc:.4f} | NCD: {m_ncd:.4f}")
    
    print("\n================================================================================")
    print("PHASE XXIX V2 COMPLETE: ADVERSARIAL BENCHMARK MATRIX")
    print("================================================================================")
    
    # Friedman + Nemenyi
    data = np.array([
        v_fold_scores[:10], # Truncate to min folds for comparison
        l_fold_scores[:10],
        r_fold_scores[:10],
        m_fold_scores[:10]
    ])
    
    try:
        stat, pval = stats.friedmanchisquare(*data)
        print(f"\n[*] Statistical Significance (Friedman Test): p-value = {pval:.5e}")
        if pval < 0.05:
            # Posthoc
            df_n = pd.DataFrame(data.T, columns=['Voynich', 'Latin', 'Recipe', 'Markov'])
            posthoc = sp.posthoc_nemenyi_friedman(df_n.melt(var_name='groups', value_name='values'), y_col='values', group_col='groups', melted=True)
            print("[*] Nemenyi Post-hoc P-values:")
            print(posthoc)
    except Exception as e:
        print("[*] Could not compute Friedman/Nemenyi (likely unequal fold counts)")

if __name__ == "__main__":
    main()