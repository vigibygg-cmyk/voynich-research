# ==============================================================================
# VOYNICH MANUSCRIPT: OUT-OF-SAMPLE VALIDATION & BLIND PREDICTION (PHASE XXIV)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import math
import random
from collections import defaultdict, Counter
from sklearn.model_selection import train_test_split

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
MIN_PREFIX_FREQ = 5     # Reduced slightly because Training Set is only 50% of the corpus
TOP_N_ANCHORS = 10      # Number of top predictive anchors to learn per visual category
PREFIX_LENGTHS = [2, 3] # Analyzing 2-3 char prefixes to avoid single-char noise

def deeply_clean_text(text):
    """Deeply cleans text of residual IVTFF transcriber marks."""
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_visual_category(folio_str):
    """Maps a folio string to its accepted visual illustration category."""
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Unknown"
    num = int(match.group(1))
    
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    else: return "Unknown" # Exclude Pharma (f88-102) for this pure distinct 4-class test

def extract_prefixes(words):
    """Extracts prefixes of specified lengths from a list of words."""
    prefixes = []
    for word in words:
        for length in PREFIX_LENGTHS:
            if len(word) > length:
                prefixes.append(word[:length])
    return prefixes

def train_macro_operators(train_df):
    """
    TRAINING PHASE: Uses TF-IDF on the 50% training set to blindly isolate
    the top predicting prefix anchors for each thematic domain.
    """
    section_prefixes = defaultdict(list)
    for _, row in train_df.iterrows():
        cat = get_visual_category(row['Folio'])
        if cat != "Unknown":
            words = str(row['Deep_Clean_Text']).split()
            section_prefixes[cat].extend(extract_prefixes(words))

    # 1. Global counts
    global_counts = Counter()
    for prefixes in section_prefixes.values():
        global_counts.update(prefixes)
        
    valid_prefixes = {p for p, c in global_counts.items() if c >= MIN_PREFIX_FREQ}
    
    # 2. Document Frequency
    doc_freq = defaultdict(int)
    for section, prefixes in section_prefixes.items():
        unique_prefixes = set(prefixes).intersection(valid_prefixes)
        for p in unique_prefixes:
            doc_freq[p] += 1
            
    total_docs = len(section_prefixes)
    
    # 3. TF-IDF Calculation
    prediction_dictionary = defaultdict(set)
    
    for section, prefixes in section_prefixes.items():
        total_section_prefixes = len(prefixes)
        if total_section_prefixes == 0: continue
            
        section_counts = Counter(p for p in prefixes if p in valid_prefixes)
        tfidf_scores = {}
        
        for prefix, count in section_counts.items():
            tf = count / total_section_prefixes
            idf = math.log10(total_docs / doc_freq[prefix])
            score = tf * idf
            if score > 0:
                tfidf_results = score
                tfidf_scores[prefix] = score
                
        # Select the top N anchors for this section
        sorted_anchors = sorted(tfidf_scores.items(), key=lambda x: x[1], reverse=True)
        for prefix, _ in sorted_anchors[:TOP_N_ANCHORS]:
            prediction_dictionary[section].add(prefix)
            
    return prediction_dictionary

def test_blind_prediction(test_df, prediction_dictionary):
    """
    TESTING PHASE: Scans the 50% unseen testing set. Predicts the folio's
    visual category based ONLY on the anchors learned during training.
    """
    total_predictions = 0
    correct_predictions = 0
    
    # Track domain-specific accuracy
    domain_correct = defaultdict(int)
    domain_total = defaultdict(int)

    for _, row in test_df.iterrows():
        actual_cat = get_visual_category(row['Folio'])
        if actual_cat == "Unknown": continue
            
        words = str(row['Deep_Clean_Text']).split()
        if not words: continue
            
        line_prefixes = extract_prefixes(words)
        
        # Score the line for each visual category
        scores = defaultdict(int)
        for cat, anchors in prediction_dictionary.items():
            scores[cat] = sum(1 for p in line_prefixes if p in anchors)
            
        # If no known anchors are present, we cannot make a confident prediction
        if sum(scores.values()) == 0:
            continue
            
        predicted_cat = max(scores, key=scores.get)
        
        total_predictions += 1
        domain_total[actual_cat] += 1
        
        if predicted_cat == actual_cat:
            correct_predictions += 1
            domain_correct[actual_cat] += 1

    accuracy = (correct_predictions / total_predictions) * 100 if total_predictions > 0 else 0
    return accuracy, total_predictions, domain_correct, domain_total

def generate_hoax_dataframe(df):
    """Simulates a hoax by globally shuffling characters."""
    hoax_df = df.copy()
    full_text = " ".join(hoax_df['Deep_Clean_Text'].dropna().tolist())
    chars = list(full_text.replace(" ", ""))
    random.seed(42)
    random.shuffle(chars)
    
    shuffled_text_blocks = []
    char_idx = 0
    for text in hoax_df['Deep_Clean_Text']:
        if not text or pd.isna(text):
            shuffled_text_blocks.append("")
            continue
        words = text.split()
        new_words = []
        for w in words:
            new_w = "".join(chars[char_idx : char_idx + len(w)])
            new_words.append(new_w)
            char_idx += len(w)
        shuffled_text_blocks.append(" ".join(new_words))
        
    hoax_df['Deep_Clean_Text'] = shuffled_text_blocks
    return hoax_df

def execute_validation_pipeline(filepath, is_hoax=False):
    if not os.path.exists(filepath): return
    
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    if is_hoax:
        source_name = "RANDOM_HOAX_BASELINE"
        df = generate_hoax_dataframe(df)
    else:
        source_name = filepath.split('/')[-1]
        
    print(f"\n" + "="*70)
    print(f"[*] EXECUTING OUT-OF-SAMPLE VALIDATION: [{source_name}]")
    print("="*70)
    
    # Filter out empty rows before splitting
    df = df[df['Deep_Clean_Text'].str.strip() != ""]
    
    # 1. Train/Test Split (50% / 50%)
    # Using random_state ensures reproducibility
    train_df, test_df = train_test_split(df, test_size=0.5, random_state=101)
    
    print(f"    [i] Data Split: {len(train_df)} Training lines | {len(test_df)} Unseen Testing lines")
    
    # 2. Train the model (Extract Rules)
    prediction_dict = train_macro_operators(train_df)
    
    if not prediction_dict and is_hoax:
        print("    [-] Training failed to find significant anchors (Expected for Hoax).")
        return
        
    print("\n    [+] Learned Rules from 50% Training Set:")
    for section, anchors in prediction_dict.items():
        print(f"        -> {section:<12} Anchors: {', '.join(list(anchors)[:5])}...")
        
    # 3. Test the model (Predict Unseen Data)
    print("\n    [*] Running True Blind Predictions on 50% Unseen Data...")
    accuracy, total_preds, dom_correct, dom_total = test_blind_prediction(test_df, prediction_dict)
    
    print(f"    -> Total Blind Predictions Made: {total_preds}")
    for dom in dom_total.keys():
        dom_acc = (dom_correct[dom] / dom_total[dom]) * 100
        print(f"       [{dom:<10}]: {dom_correct[dom]}/{dom_total[dom]} correct ({dom_acc:.1f}%)")
        
    print(f"    -> GLOBAL PREDICTIVE ACCURACY: {accuracy:.2f}%")
    
    if accuracy >= 80.0 and not is_hoax:
        print("    [!] KPI MET: Model successfully generalized to unseen data (>80% accuracy).")
        print("        Sectoral Polymorphism is a robust, predictive structural reality.")
    elif not is_hoax:
        print("    [-] KPI FAILED: Accuracy dropped below 80% on unseen data (Possible overfitting).")
    else:
        print("    [i] BASELINE CONTROL: Note the expected collapse in predictive accuracy.")

def main():
    print("=== Voynich Phase XXIV: Out-of-Sample Predictive Validation ===\n")
    print("Objective: Mitigate confirmation bias by strictly separating the discovery")
    print("of rules (50% Training Data) from their validation (50% Unseen Test Data).\n")
    
    # Authentic Validation
    for filepath in TARGET_FILES:
        execute_validation_pipeline(filepath)
        
    # Hoax Baseline Validation
    if TARGET_FILES and os.path.exists(TARGET_FILES[0]):
        execute_validation_pipeline(TARGET_FILES[0], is_hoax=True)
        
    print("\n=================================================================")
    print("PHASE XXIV (Parts 2.1 & 2.3) COMPLETE. Review Out-of-Sample KPI.")
    print("=================================================================")

if __name__ == "__main__":
    main()