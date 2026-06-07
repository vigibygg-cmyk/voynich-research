import pandas as pd
from collections import Counter
import re
import os
import random

def get_stats(vocab):
    pairs = Counter()
    for word, freq in vocab.items():
        symbols = word.split()
        for i in range(len(symbols) - 1):
            pairs[symbols[i], symbols[i + 1]] += freq
    return pairs

def merge_vocab(pair, v_in):
    v_out = {}
    bigram = re.escape(' '.join(pair))
    p = re.compile(r'(?<!\S)' + bigram + r'(?!\S)')
    for word in v_in:
        w_out = p.sub(''.join(pair), word)
        v_out[w_out] = v_in[word]
    return v_out

def run_bpe_on_spaceless_text(clean_texts, num_merges=600):
    full_text = "".join(clean_texts).replace(" ", "")
    print(f"Total spaceless characters: {len(full_text)}")
    
    current_string = " ".join(list(full_text))
    vocab = {current_string: 1}
    
    for i in range(num_merges):
        pairs = get_stats(vocab)
        if not pairs:
            break
        best = max(pairs, key=pairs.get)
        vocab = merge_vocab(best, vocab)
            
    final_tokens = list(vocab.keys())[0].split()
    token_counts = Counter(final_tokens)
    merged_tokens = {k: v for k, v in token_counts.items() if len(k) > 1}
    
    return merged_tokens

def generate_random_baseline(clean_texts):
    """Generates a random baseline text preserving character frequencies."""
    full_text = "".join(clean_texts).replace(" ", "")
    char_list = list(full_text)
    random.seed(42) # For reproducibility
    random.shuffle(char_list)
    return ["".join(char_list)]

if __name__ == "__main__":
    base_dir = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"
    files = {
        "IT2a-n": os.path.join(base_dir, "IT2a-n_clean.csv"),
        "RF1b-er": os.path.join(base_dir, "RF1b-er_clean.csv"),
        "ZL3b-n": os.path.join(base_dir, "ZL3b-n_clean.csv")
    }
    
    control_list = ['daiin', 'ol', 'aiin', 'chedy', 'ar', 'shedy', 'or', 'chol', 'lka', 'sho']
    results = {}
    
    for name, filepath in files.items():
        if os.path.exists(filepath):
            print(f"\n================ Processing {name} ================")
            df = pd.read_csv(filepath)
            clean_texts = df['Clean_Text'].dropna().astype(str).tolist()
            
            # Process Authentic Text
            print(f"--- Running BPE on Authentic {name} ---")
            final_vocab_auth = run_bpe_on_spaceless_text(clean_texts, num_merges=600)
            
            # Process Random Baseline
            print(f"--- Running BPE on Random Baseline ({name}) ---")
            random_texts = generate_random_baseline(clean_texts)
            final_vocab_rand = run_bpe_on_spaceless_text(random_texts, num_merges=600)
            
            results[name] = {
                "auth": final_vocab_auth,
                "rand": final_vocab_rand
            }
        else:
            print(f"File missing: {filepath}")

    print("\n\n================ CROSS-VALIDATION SUMMARY ================")
    print(f"{'Token':<10} | {'IT2a-n':<8} | {'RF1b-er':<8} | {'ZL3b-n':<8} | {'Random (Avg)':<12}")
    print("-" * 55)
    
    for word in control_list:
        counts = []
        rand_counts = []
        for name in files.keys():
            if name in results:
                # Authentic
                auth_count = results[name]["auth"].get(word, 0)
                counts.append(str(auth_count))
                # Random
                rand_count = results[name]["rand"].get(word, 0)
                rand_counts.append(rand_count)
        
        avg_rand = sum(rand_counts) / len(rand_counts) if rand_counts else 0
        print(f"{word:<10} | {counts[0]:<8} | {counts[1]:<8} | {counts[2]:<8} | {avg_rand:.1f}")
