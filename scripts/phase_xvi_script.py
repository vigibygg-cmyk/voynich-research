# VOYNICH MANUSCRIPT: VERBOSE ENCRYPTION (NAIBBE) ANALYSIS (PHASE XVI)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import zlib
import random

# Configuration - Triangulation
VOYNICH_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
HISTORICAL_CORPUS_DIR = "historical_corpora"

# Control files for compression benchmarking
HISTORICAL_CONTROLS = [
    "Latin_Alchemy.txt",
    "German_Botany_Medicine.txt",
    "English_Theology_Religion.txt",
    "Finnish_Astronomy_Astrology.txt"
]

# Blind SVD Clusters extracted directly from Phase XIV's Unsupervised K-Means Output
# We hypothesize these highly repetitive, structurally rigid functional classes act as the "Verbose Padding"
VERBOSE_PADDING_CLASSES = {
    'daiin', 'ol', 'aiin', 'chedy', 'shedy', 'chey', 'dar', 'qokeey', 'qokeedy', 
    'al', 'qokain', 'qokedy', 'shey', 'qokaiin', 'dal', # Terminals
    'ar', 'or', 's', 'r', 'o', 'sar', 'char', 'd', 'tar', 'ches', 'sor', 'chos', 'cheos', 'lor', 'os' # Modifiers
}

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def calculate_compression_ratio(text):
    """
    Measures algorithmic entropy (Kolmogorov complexity proxy).
    Compresses text using zlib. A lower ratio means the text is highly repetitive (Verbose).
    """
    if not text:
        return 0.0
        
    encoded_text = text.encode('utf-8')
    compressed_text = zlib.compress(encoded_text, level=9)
    
    original_size = len(encoded_text)
    compressed_size = len(compressed_text)
    
    ratio = compressed_size / original_size
    return ratio

def calculate_snr(words):
    """
    Calculates the Signal-to-Noise Ratio.
    Noise = Known repetitive structural operators (Verbose Padding).
    Signal = The remaining textual "Skeleton".
    """
    total_words = len(words)
    if total_words == 0:
        return 0.0, 0.0
        
    noise_count = sum(1 for w in words if w in VERBOSE_PADDING_CLASSES)
    signal_count = total_words - noise_count
    
    noise_pct = (noise_count / total_words) * 100
    signal_pct = (signal_count / total_words) * 100
    
    return signal_pct, noise_pct

def generate_hoax_words(words):
    """Shuffles characters globally to destroy repetition syntax while keeping character count."""
    full_text = "".join(words)
    chars = list(full_text)
    random.seed(42)
    random.shuffle(chars)
    
    shuffled_text = "".join(chars)
    # Split into chunks roughly the size of average Voynich words (length ~5)
    hoax_words = [shuffled_text[i:i+5] for i in range(0, len(shuffled_text), 5)]
    return hoax_words

def process_voynich_file(filepath, is_hoax=False):
    if not os.path.exists(filepath):
        return None
        
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    full_corpus = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_corpus.split()
    
    if is_hoax:
        source_name = "RANDOM_HOAX_BASELINE"
        words = generate_hoax_words(words)
        full_corpus = " ".join(words)
    else:
        source_name = filepath.split('/')[-1]
        
    compression_ratio = calculate_compression_ratio(full_corpus)
    
    # We only measure SNR on authentic structures
    if not is_hoax:
        signal_pct, noise_pct = calculate_snr(words)
    else:
        signal_pct, noise_pct = 100.0, 0.0 # Hoax has no predefined structural padding
        
    print(f"\n[*] ANALYZING VERBOSE CIPHER MODEL: [{source_name}]")
    print(f"    -> Compression Ratio (ZLIB): {compression_ratio:.4f} (Lower = More Repetitive/Verbose)")
    if not is_hoax:
        print(f"    -> Signal (Skeleton) / Noise (Padding) Ratio:")
        print(f"       [SKELETON COMMANDS]: {signal_pct:.2f}% of text")
        print(f"       [VERBOSE PADDING]  : {noise_pct:.2f}% of text")
        
    return compression_ratio

def process_historical_control(filename):
    filepath = os.path.join(HISTORICAL_CORPUS_DIR, filename)
    if not os.path.exists(filepath):
        return
        
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        text = f.read()
        
    # Standard clean
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'_', '', text)
    clean_text = re.sub(r'\s+', ' ', text).strip().lower()
    
    # Take a sample comparable in size to the Voynich MS (~200,000 characters)
    sample_text = clean_text[:200000]
    
    compression_ratio = calculate_compression_ratio(sample_text)
    
    print(f"\n[*] HISTORICAL CONTROL: [{filename}]")
    print(f"    -> Compression Ratio (ZLIB): {compression_ratio:.4f}")

def main():
    print("=== Voynich Phase XVI: Verbose Encryption (Naibbe) Analysis ===\n")
    print("Hypothesis: If Voynich is a 'Verbose Cipher' (short skeleton wrapped in noise),")
    print("it will compress unnaturally well, and the text will be dominated by padding.\n")
    
    # 1. Voynich Triangulation
    for filepath in VOYNICH_FILES:
        process_voynich_file(filepath)
        
    # 2. Chaos Control Baseline
    if VOYNICH_FILES and os.path.exists(VOYNICH_FILES[0]):
        print("\n" + "="*70)
        print("[*] EXECUTING CHAOS CONTROL (RANDOM_HOAX_BASELINE)")
        print("="*70)
        process_voynich_file(VOYNICH_FILES[0], is_hoax=True)
        
    # 3. Historical Controls
    print("\n" + "="*70)
    print("[*] EXECUTING HISTORICAL COMPRESSION BASELINES")
    print("="*70)
    for filename in HISTORICAL_CONTROLS:
        process_historical_control(filename)
        
    print("\n=================================================================")
    print("PHASE XVI COMPLETE. Compare Voynich compressibility to natural languages.")
    print("=================================================================")

if __name__ == "__main__":
    main()
# ==============================================================================
# VOYNICH MANUSCRIPT: MICROSCOPIC f2r LINE ANALYSIS (DEEP DIVE)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os

# Configuration - Triangulation
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Ontological Key (Mathematically derived from Phases X-XIV)
# 1. Macro-Operators (The Taxonomic Skeleton / Signal)
MACRO_PROCEDURAL = ["lka", "lkc", "lky", "lk"]
MACRO_ENTITY = ["yto", "yp", "dyd", "sho", "cho", "chok", "ctho"] # Added 'cho/sho' from Phase 12 Herbal

# 2. Structural Operators (The Verbose Padding / Operational States)
STATE_MODIFIERS = ['s', 'shedy', 'or', 'ar', 'r', 'char', 'd', 'tar', 'ches', 'sor', 'chos', 'cheos', 'lor', 'os', 'chey']
BASE_STATES = ['ol', 'qol']
TERMINALS = ['aiin', 'daiin', 'am', 'chedy', 'dar', 'qokeey', 'qokeedy', 'al', 'qokain', 'qokedy', 'shey', 'qokaiin', 'dal', 'iin']

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def load_and_find_f2r(filepath):
    """Loads the dataset and extracts the first valid line from Folio f2r."""
    if not os.path.exists(filepath):
        return None, None
        
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    # Filter for folio f2r
    f2r_df = df[df['Folio'] == 'f2r'].copy()
    
    if f2r_df.empty:
        # Fallback: try matching locus string if Folio column is malformed
        f2r_df = df[df['Locus'].str.contains('f2r', na=False, case=False)].copy()
        
    if f2r_df.empty:
        return None, None
        
    # Get the first line that has actual text
    for _, row in f2r_df.iterrows():
        text = str(row['Deep_Clean_Text']).strip()
        if len(text) > 0:
            return row['Locus'], text
            
    return None, None

def naive_naibbe_parser(word):
    """
    Parses a word according to the Naibbe (Verbose Cipher) logic.
    Identifies if a word is part of the hidden "Skeleton" or just "Padding/Noise".
    """
    if any(word.startswith(root) for root in MACRO_PROCEDURAL + MACRO_ENTITY):
        return "[SIGNAL: Taxonomic Skeleton]"
    elif word in STATE_MODIFIERS or word in BASE_STATES or word in TERMINALS or any(word.endswith(t) for t in TERMINALS):
        return "[NOISE: Verbose Padding]"
    else:
        return "[UNRESOLVED / POTENTIAL SIGNAL]"

def paper_computer_parser(word):
    """
    Parses a word according to the Paper Computer (Algorithmic Logic).
    Identifies functional slots (Object -> State -> Terminal).
    """
    if any(word.startswith(root) for root in MACRO_PROCEDURAL):
        return "[COMMAND: Procedural Action]"
    elif any(word.startswith(root) for root in MACRO_ENTITY):
        return "[ENTITY: Botanical/Natural Object]"
    elif word in BASE_STATES:
        return "[BASE: Substrate / Extract]"
    elif word in STATE_MODIFIERS:
        return "[STATE: Operational Transition]"
    elif word in TERMINALS or any(word.endswith(t) for t in TERMINALS):
        return "[YIELD: Quantitative Dose / Closure]"
    else:
        return "[UNKNOWN VARIABLE]"

def analyze_line(source_name, locus, text):
    print(f"\n" + "="*80)
    print(f"[*] SOURCE: {source_name} | LOCUS: {locus}")
    print(f"    ORIGINAL TEXT: {text}")
    print("="*80)
    
    words = text.split()
    
    print("\n--- 1. NAIBBE (VERBOSE CIPHER) INTERPRETATION ---")
    print("Hypothesis: Most words are empty padding hiding a few real taxonomic roots.")
    signal_count = 0
    noise_count = 0
    
    for word in words:
        tag = naive_naibbe_parser(word)
        if "SIGNAL" in tag: signal_count += 1
        elif "NOISE" in tag: noise_count += 1
        print(f"    {word:<12} -> {tag}")
        
    total = len(words)
    print(f"    > SNR Breakdown: {signal_count} Skeleton words ({signal_count/total*100:.1f}%), {noise_count} Padding words ({noise_count/total*100:.1f}%)")

    print("\n--- 2. PAPER COMPUTER (ALGORITHMIC) INTERPRETATION ---")
    print("Hypothesis: Words are not padding, but rigid operational functions (Object->State->Dose).")
    
    for word in words:
        tag = paper_computer_parser(word)
        print(f"    {word:<12} -> {tag}")
        
    print("\n    [ALGORITHMIC SYNTAX FLOW]:")
    flow = " -> ".join([paper_computer_parser(w).split(':')[0].replace('[', '') for w in words])
    print(f"    {flow}")

def main():
    print("=== Voynich f2r Microscopic Algorithmic Parsing ===\n")
    print("Target: Extracting the first readable line from Folio f2r (Herbal Section)")
    print("and blindly applying our mathematical decoding models to it.\n")
    
    for filepath in TARGET_FILES:
        source_name = filepath.split('/')[-1]
        locus, text = load_and_find_f2r(filepath)
        
        if locus and text:
            analyze_line(source_name, locus, text)
        else:
            print(f"[-] Could not extract f2r data from {source_name}")

if __name__ == "__main__":
    main()
# ==============================================================================