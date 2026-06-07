# ==============================================================================
# VOYNICH MANUSCRIPT: UNSUPERVISED GRAMMAR INDUCTION ENGINE (PHASE XXX)
# Improved: Integrated Ancient German and Old Finnish from the user corpus
# Environment: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os
import warnings
from collections import Counter, defaultdict
warnings.filterwarnings("ignore")

# Configuration
VOYNICH_FILE = "voynich_clean_data/RF1b-er_clean.csv"
HISTORICAL_DIR = "historical_corpora"
MAX_GRAMMAR_RULES = 150  # Maximum number of hierarchical rules to induce
MIN_RULE_FREQUENCY = 3  # Minimum occurrences to form a rule

# --- MULTILINGUAL MOCK CORPORA (Used if historical files are missing) ---
MOCK_LATIN = "in nomine patris et filii et spiritus sancti amen recipe de herba dicta " * 200
MOCK_GREEK = "εν αρχη ην ο λογος και ο λογος ην προς τον θεον και θεος ην ο λογος " * 200
MOCK_ARABIC = "في البدء خلق الله السماوات والأرض وكانت الأرض خربة وخالية وعلى وجه الغمر " * 200
MOCK_HEBREW = "בראשית ברא אלהים את השמים ואת הארץ והארץ היתה תהו ובהו וחשך על פני " * 200
MOCK_HINDI = "श्रीमद्भगवद्गीता उपनिषद के अनुसार अर्जुन और कृष्ण का संवाद अत्यंत पवित्र है " * 200
MOCK_GERMAN = "diz herre lere unde guote botschaft von der scone houbtman horet " * 200
MOCK_FINNISH = "mieleni minun tekevi aivoni ajattelevi lähteäni laulamahan " * 200

def deeply_clean_text(text):
    """Deep Voynich text cleaning."""
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def clean_historical_text(text, filename):
    """
    Two-tier cleaning algorithm designed to process standard Latin characters
    as well as complex non-Latin and diacritical characters (Arabic, Greek, Hebrew, Hindi, German, Finnish).
    """
    text = str(text)
    # Identify languages requiring specific/unicode character preservation (including German umlauts and Finnish characters)
    unicode_keywords = ['Greek', 'Arabic', 'Hindi', 'Hebrew', 'German', 'Finnish']
    needs_unicode = any(keyword in filename for keyword in unicode_keywords)
    
    if needs_unicode:
        # Retain specific script characters and accented letters, removing only punctuation and digits
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        text = re.sub(r'_', '', text)
    else:
        # Strict ASCII cleaning for standard Latin prose
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        
    return re.sub(r'\s+', ' ', text).strip().lower()

def load_voynich_tokens():
    """Loads and cleans Voynich manuscript tokens."""
    if not os.path.exists(VOYNICH_FILE):
        return []
    df = pd.read_csv(VOYNICH_FILE)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    return " ".join(df['Deep_Clean_Text'].dropna().tolist()).split()

def load_or_simulate_control(filename, mock_text):
    """Checks if file exists in the Colab environment; if not - falls back to mock text."""
    path = os.path.join(HISTORICAL_DIR, filename)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            raw_content = f.read()
            return clean_historical_text(raw_content, filename).split()
    return clean_historical_text(mock_text, filename).split()

def generate_markov_tokens(word_pool, length=10000):
    """Generates synthetic language using a 3-gram Markov chain from word pool."""
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

# ==============================================================================
# UNSUPERVISED GRAMMAR INDUCTION ALGORITHM (SEQUITUR-INSPIRED)
# ==============================================================================

def induce_grammar_rules(tokens):
    """
    Hierarchical pair-replacement algorithm (Sequitur analog).
    Blindly extracts the most frequent adjacent word pairs and replaces them with CFG rules.
    """
    corpus = list(tokens)
    grammar = {}
    
    for r_idx in range(MAX_GRAMMAR_RULES):
        pairs = Counter(zip(corpus[:-1], corpus[1:]))
        if not pairs:
            break
            
        best_pair, freq = pairs.most_common(1)[0]
        if freq < MIN_RULE_FREQUENCY:
            break
            
        rule_symbol = f"R{r_idx}"
        grammar[rule_symbol] = best_pair
        
        new_corpus = []
        i = 0
        while i < len(corpus):
            if i < len(corpus) - 1 and corpus[i] == best_pair[0] and corpus[i+1] == best_pair[1]:
                new_corpus.append(rule_symbol)
                i += 2
            else:
                new_corpus.append(corpus[i])
                i += 1
        corpus = new_corpus
        
    return grammar, corpus

def calculate_parse_coverage(tokens, grammar):
    """Calculates what percentage of the original text is successfully covered by the induced rules."""
    corpus = list(tokens)
    tokens_before = len(corpus)
    
    for rule_symbol, pair in grammar.items():
        new_corpus = []
        i = 0
        while i < len(corpus):
            if i < len(corpus) - 1 and corpus[i] == pair[0] and corpus[i+1] == pair[1]:
                new_corpus.append(rule_symbol)
                i += 2
            else:
                new_corpus.append(corpus[i])
                i += 1
        corpus = new_corpus
        
    tokens_after = len(corpus)
    reduced_tokens = tokens_before - tokens_after
    coverage_pct = (reduced_tokens / tokens_before) * 100 if tokens_before > 0 else 0
    return coverage_pct, tokens_after

def main():
    print("=== Voynich Phase XXX: Multi-Script Unsupervised Grammar Induction ===\n")
    print("Preregistered goal: Formally measure parsability across diverse alphabets and scripts.\n")
    
    # 1. Load data
    voynich_tokens = load_voynich_tokens()
    if not voynich_tokens:
        print("[-] Error: Voynich base files not found.")
        return
        
    voynich_tokens = voynich_tokens[:10000] # Standardize size to 10k words
    
    # Load historical corpora (falls back to mocks dynamically if missing)
    latin_tokens = load_or_simulate_control("Latin_General_Unknown.txt", MOCK_LATIN)[:10000]
    greek_tokens = load_or_simulate_control("Ancient_Greek_General_Unknown.txt", MOCK_GREEK)[:10000]
    arabic_tokens = load_or_simulate_control("Arabic_General_Unknown.txt", MOCK_ARABIC)[:10000]
    hebrew_tokens = load_or_simulate_control("Hebrew_General_Unknown.txt", MOCK_HEBREW)[:10000]
    hindi_tokens = load_or_simulate_control("Hindi_Classical_Hindi.txt", MOCK_HINDI)[:10000]
    german_tokens = load_or_simulate_control("German_General_Unknown.txt", MOCK_GERMAN)[:10000]
    finnish_tokens = load_or_simulate_control("Finnish_Astronomy_Astrology.txt", MOCK_FINNISH)[:10000]
    markov_tokens = generate_markov_tokens(voynich_tokens, length=10000)
    
    # 2. Induce rules from Voynich text
    print(f"[*] Inducing up to {MAX_GRAMMAR_RULES} CFG rules on Voynich...")
    grammar, compressed_voynich = induce_grammar_rules(voynich_tokens)
    
    print(f"    [+] Successfully induced {len(grammar)} hierarchical rules.")
    print("\n    [+] SAMPLE INDUCED PRODUCTION RULES (Top 8):")
    for rule, expansion in list(grammar.items())[:8]:
        print(f"        -> {rule} -> [ {expansion[0]} ] [ {expansion[1]} ]")
        
    # 3. Parsability Benchmark
    print("\n" + "="*80)
    print("[*] EXECUTING MULTI-SCRIPT PARSABILITY & COMPRESSION BENCHMARKS")
    print("="*80)
    
    targets = {
        "Voynich Manuscript (Self-Parse)": voynich_tokens,
        "Natural Medieval Latin (Control A)": latin_tokens,
        "Ancient Greek (Control A-2)": greek_tokens,
        "Classical Arabic (Control D)": arabic_tokens,
        "Classical Hebrew (Control E)": hebrew_tokens,
        "Classical Hindi (Control F)": hindi_tokens,
        "Medieval German (Control G)": german_tokens,
        "Old Finnish (Control H)": finnish_tokens,
        "Markovian Pseudo-Language (Control C)": markov_tokens
    }
    
    results = []
    for name, tokens in targets.items():
        coverage, final_tokens = calculate_parse_coverage(tokens, grammar)
        compression_ratio = len(tokens) / final_tokens if final_tokens > 0 else 1.0
        
        print(f"\n    -> Corpus: [{name}]")
        print(f"       Original Tokens: {len(tokens)}")
        print(f"       Parse Coverage : {coverage:.2f}% of text successfully parsed into CFG rules")
        print(f"       MDL Ratio      : {compression_ratio:.4f}x tokens-to-rules compression advantage")
        
        results.append({
            "Corpus": name,
            "Parse_Coverage": coverage,
            "MDL_Ratio": compression_ratio
        })
        
    print("\n" + "="*80)
    print("PHASE XXX COMPLETE: EXPANDED MULTI-SCRIPT COMPLEXITY MATRIX")
    print("="*80)
    print(f"{'Corpus Name':<42} | {'Parse Coverage':<23} | {'Compression Ratio':<22}")
    print("-" * 95)
    for r in results:
        print(f"{r['Corpus']:<42} | {r['Parse_Coverage']:.2f}%                 | {r['MDL_Ratio']:.4f}x")
    print("="*95)

if __name__ == "__main__":
    main()