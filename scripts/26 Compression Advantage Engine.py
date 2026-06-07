# ==============================================================================
# VOYNICH MANUSCRIPT: COMPRESSION ADVANTAGE ENGINE (PHASE XXVI)
# Information theory Minimum Description Length (MDL) test
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import zlib
import math
from collections import Counter

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Morphological dictionary (derived from VII, XIV and XIX phase results)
# Used for systematic splitting of words into semantic tokens.
KNOWN_PREFIXES = {'q', 'y', 'd', 'o', 's', 't', 'k', 'p', 'l', 'r', 'ch', 'sh', 'al', 'ar'}
KNOWN_SUFFIXES = {'aiin', 'iin', 'in', 'dy', 'ey', 'am', 'al', 'ol', 'or', 'ar', 'ed', 'edy', 'cg', 'eg'}

def deeply_clean_text(text):
    """Cleans text of remaining IVTFF transcription marks."""
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def ontological_parse_and_encode(words):
    """
    Splits words into morphological tokens (prefix + root + suffix)
    and calculates optimized size in bytes.
    Each successfully recognized morphological dictionary token is encoded 12 bits (1.5 bytes).
    Unrecognized words encoded in standard 8 bit UTF-8 format.
    """
    total_bits = 0
    parsed_words = 0
    
    for word in words:
        if len(word) < 2:
            total_bits += len(word) * 8 + 8  # letter + space
            continue
            
        # Greedy Match: try to find longest prefix and suffix
        prefix_match = None
        suffix_match = None
        root = word
        
        # Check longest matching prefix
        for p in sorted(KNOWN_PREFIXES, key=len, reverse=True):
            if root.startswith(p):
                prefix_match = p
                root = root[len(p):]
                break
                
        # Check longest matching suffix
        for s in sorted(KNOWN_SUFFIXES, key=len, reverse=True):
            if root.endswith(s):
                suffix_match = s
                root = root[:-len(s)]
                break
                
        # FIX (LOGIC TRAP): Word is encoded via dictionary method only if,
        # if prefix OR suffix was successfully detected in it.
        # Otherwise, word is considered unrecognized and encoded in UTF-8 format.
        if prefix_match is not None or suffix_match is not None:
            parsed_words += 1
            # Optimized size calculation
            # 12 bits for each recognized dictionary component (prefix, suffix)
            if prefix_match: total_bits += 12
            if suffix_match: total_bits += 12
            
            # Remaining root (if it exists after splitting) is encoded as 12-bit index
            if len(root) > 0:
                total_bits += 12 
                
            total_bits += 8 # Tarpo separatorius (1 baitas)
        else:
            # Standard fallback for completely indecipherable words
            total_bits += len(word) * 8 + 8
            
    encoded_bytes = math.ceil(total_bits / 8)
    return encoded_bytes, parsed_words

def execute_compression_benchmark(filepath):
    if not os.path.exists(filepath): return
    
    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    full_text = " ".join(df['Deep_Clean_Text'].dropna().tolist())
    words = full_text.split()
    source_name = filepath.split('/')[-1]
    
    if not words: return
    
    # 1. Baseline 1: Pradinis teksto dydis (Raw UTF-8)
    raw_bytes = len(full_text.encode('utf-8'))
    
    # 2. Baseline 2: Standartinis Zlib suspaudimo dydis
    zlib_bytes = len(zlib.compress(full_text.encode('utf-8')))
    
    # 3. Testas: Ontologinio parserio suspaustas dydis
    parsed_bytes, parsed_count = ontological_parse_and_encode(words)
    
    # Metrikos
    zlib_savings = (1 - (zlib_bytes / raw_bytes)) * 100
    parsed_savings = (1 - (parsed_bytes / raw_bytes)) * 100
    
    parse_rate = (parsed_count / len(words)) * 100
    
    print(f"\n[*] VYKDOMAS KOMPRESIJOS BENCHMARKAS: [{source_name}]")
    print("-" * 70)
    print(f"    -> Pradinis teksto dydis   : {raw_bytes:,} baitai")
    print(f"    -> Standartinis Zlib dydis : {zlib_bytes:,} baitai (Sutaupyta: {zlib_savings:.1f}%)")
    print(f"    -> Ontologinis parseris    : {parsed_bytes:,} baitai (Sutaupyta: {parsed_savings:.1f}%)")
    print("-" * 70)
    print(f"    -> Parserio kodavimo daznis: {parse_rate:.1f}% zodziu sekmingai atitiko morfologines taisykles.")
    
    if parsed_bytes < zlib_bytes:
        advantage = ((zlib_bytes - parsed_bytes) / zlib_bytes) * 100
        print(f"    [!] KOMPRESIJOS PRANASUMAS PATVIRTINTAS: Ontologinis parseris yra {advantage:.1f}% efektyvesnis uz Zlib.")
        print("        Tai palaiko hipoteze, kad tekstas is esmes veikia pagal sias morfologines taisykles.")
    else:
        print("    [-] HIPOTEZE ATMESTA: Standartinis Zlib suspaude efektyviau uz ontologini parseri.")

def main():
    print("=== Voynich Phase XXVI: Information-Theoretic Compression Benchmark ===\n")
    print("Objective: Test the Minimum Description Length (MDL) principle. If our")
    print("structural rules are accurate, a parser built on them must compress")
    print("the text better than a blind statistical algorithm like Zlib.\n")
    
    for filepath in TARGET_FILES:
        execute_compression_benchmark(filepath)
        
    print("\n======================================================================")
    print("PHASE XXVI COMPLETE. Review the algorithmic entropy metrics.")
    print("======================================================================")

if __name__ == "__main__":
    main()