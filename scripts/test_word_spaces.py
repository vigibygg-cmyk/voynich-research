import pandas as pd
from collections import Counter
import re
import os

def get_stats(vocab):
    """Calculates pair frequencies in the current vocabulary."""
    pairs = Counter()
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i + 1]] += freq
    return pairs

def merge_vocab(pair, v_in):
    """Merges the most frequent pair in the vocabulary."""
    v_out = {}
    bigram = re.escape(' '.join(pair))
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out

def run_bpe_on_spaceless_text(file_path, num_merges=1000):
    print(f"Reading data from: {file_path}")
    df = pd.read_csv(file_path)
    
    # 1. Remove all spaces and merge into one text
    # Naudojame tik eilutes, kurios turi Clean_Text
    clean_texts = df['Clean_Text'].dropna().astype(str).tolist()
    full_text = "".join(clean_texts).replace(" ", "")
    
    print(f"Total spaceless characters: {len(full_text)}")
    
    # Since BPE standardly works with dictionaries, and we have one giant line, 
    # we artificially split this line into chunks (e.g. 50 characters), 
    # so BPE algorithm can work in memory efficiently, or we treat everything as one word.
    # For accuracy (avoiding artificial limits), we use simple n-gram frequency analysis
    # iteratively merging most frequent characters. Matches BPE logic for one long text.
    
    # Iteratyvus BPE procesas pritaikytas vienai ilgai eilutei.
    current_string = " ".join(list(full_text)) # Kiekvienas simbolis atskirtas tarpu
    
    # Convert to dictionary format for compatibility with standard BPE code template.
    # Everything is one "word" with frequency 1.
    vocab = {current_string: 1}
    
    print(f"Starting {num_merges} BPE merges...")
    
    top_tokens_history = []
    
    for i in range(num_merges):
        pairs = get_stats(vocab)
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        vocab = merge_vocab(best, vocab)
        
        # Take extracted tokens at this moment
        current_tokens = list(vocab.keys())[0].split()
        
        if (i + 1) % 100 == 0:
            token_counts = Counter(current_tokens)
            # Filtruojame tik sujungtus tokenus (ilgis > 1)
            merged_tokens = {k: v for k, v in token_counts.items() if len(k) > 1}
            top_merged = sorted(merged_tokens.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"Merge {i+1}: Best pair = {best}. Top tokens > 1 char: {top_merged}")
            top_tokens_history.append((i+1, top_merged))
            
    # Final analysis
    final_tokens = list(vocab.keys())[0].split()
    token_counts = Counter(final_tokens)
    merged_tokens = {k: v for k, v in token_counts.items() if len(k) > 1}
    
    return merged_tokens

if __name__ == "__main__":
    file_it2a = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data\IT2a-n_clean.csv"
    
    if os.path.exists(file_it2a):
        # Run with 600 merges.
        final_vocab = run_bpe_on_spaceless_text(file_it2a, num_merges=600)
        
        print("\n--- FINAL BPE TOKENS (Count > 50) ---")
        sorted_final = sorted(final_vocab.items(), key=lambda x: x[1], reverse=True)
        for token, count in sorted_final:
            if count > 50:
                print(f"{token}: {count}")
                
        # Control list for verification
        control_list = ['daiin', 'ol', 'aiin', 'chedy', 'ar', 'shedy', 'or', 'chol', 'lka', 'sho']
        print("\n--- CONTROL LIST CHECK ---")
        for word in control_list:
            found = next((count for token, count in sorted_final if token == word), 0)
            print(f"{word}: {found}")
            
    else:
        print(f"File not found: {file_it2a}")
