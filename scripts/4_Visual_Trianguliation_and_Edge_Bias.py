# ==============================================================================
# VOYNICH MANUSCRIPT: EDGE BIAS ANALYSIS (PHASE IV)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import random

# Configuration
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]

# Edge Bias Targets (Testing physical boundary termination dynamics)
# Note: We test these specific suffixes based on their extreme frequency 
# observed in Phase II BPE valency outputs, avoiding semantic assumptions.
TERMINAL_SUFFIXES = ['iin', 'am']

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'<.*?>', '', text)
    text = re.sub(r'<>', '', text)
    text = re.sub(r'\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def analyze_edge_bias(df):
    """Calculates the concentration of specific suffixes at the end of physical lines."""
    internal_words_total = 0
    internal_words_target = 0
    
    terminal_words_total = 0
    terminal_words_target = 0
    
    for _, row in df.iterrows():
        text = row['Deep_Clean_Text']
        if not text: continue
        
        words = text.split()
        if len(words) < 2:
            continue # Need at least an internal and a terminal word to compare
            
        terminal_word = words[-1]
        internal_words = words[:-1]
        
        # Check Terminal (End of line)
        terminal_words_total += 1
        if any(terminal_word.endswith(sux) for sux in TERMINAL_SUFFIXES):
            terminal_words_target += 1
            
        # Check Internal (Middle of line)
        internal_words_total += len(internal_words)
        internal_words_target += sum(1 for w in internal_words if any(w.endswith(sux) for sux in TERMINAL_SUFFIXES))
        
    internal_rate = (internal_words_target / internal_words_total) * 100 if internal_words_total else 0
    terminal_rate = (terminal_words_target / terminal_words_total) * 100 if terminal_words_total else 0
    multiplier = (terminal_rate / internal_rate) if internal_rate else 0
    
    return {
        'Internal_Rate_%': round(internal_rate, 2),
        'Terminal_Rate_%': round(terminal_rate, 2),
        'Multiplier_X': round(multiplier, 2)
    }

def generate_hoax_dataframe(df):
    """
    Creates a Hoax baseline by extracting all words, shuffling them globally, 
    and then repopulating the dataframe rows maintaining the exact original word counts per line.
    This safely destroys line-ending structures (Edge Bias) for the control group.
    """
    hoax_df = df.copy()
    
    all_words = []
    word_counts = []
    
    # Extract
    for text in hoax_df['Deep_Clean_Text']:
        if not text:
            word_counts.append(0)
        else:
            words = text.split()
            all_words.extend(words)
            word_counts.append(len(words))
            
    # Shuffle completely
    random.shuffle(all_words)
    
    # Repopulate
    new_texts = []
    current_idx = 0
    for count in word_counts:
        if count == 0:
            new_texts.append("")
        else:
            line_words = all_words[current_idx : current_idx + count]
            new_texts.append(" ".join(line_words))
            current_idx += count
            
    hoax_df['Deep_Clean_Text'] = new_texts
    return hoax_df

def process_file(filepath):
    print(f"\n[{filepath.split('/')[-1]}] Running Phase IV Edge Bias Analysis...")
    if not os.path.exists(filepath):
        print(f"[-] Error: {filepath} not found.")
        return

    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    edge_bias_stats = analyze_edge_bias(df)
    print("    [+] EDGE BIAS RESULTS (-iin, -am suffixes):")
    print(f"        -> Internal occurrence rate: {edge_bias_stats['Internal_Rate_%']}%")
    print(f"        -> Line-Terminal occurrence rate: {edge_bias_stats['Terminal_Rate_%']}%")
    print(f"        -> Concentration Multiplier: {edge_bias_stats['Multiplier_X']}x higher at line end")

def process_hoax(filepath):
    print(f"\n[RANDOM_HOAX_BASELINE] Simulating random text layout from {filepath.split('/')[-1]}...")
    if not os.path.exists(filepath):
        return

    df = pd.read_csv(filepath)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    
    hoax_df = generate_hoax_dataframe(df)
    
    edge_bias_stats = analyze_edge_bias(hoax_df)
    print("    [+] EDGE BIAS RESULTS (-iin, -am suffixes):")
    print(f"        -> Internal occurrence rate: {edge_bias_stats['Internal_Rate_%']}%")
    print(f"        -> Line-Terminal occurrence rate: {edge_bias_stats['Terminal_Rate_%']}%")
    print(f"        -> Concentration Multiplier: {edge_bias_stats['Multiplier_X']}x higher at line end")

def main():
    print("=== Voynich Phase IV: Physical Edge Bias Analysis ===\n")
    print("[*] Enforcing Tabula Rasa: Visual clustering removed. Testing physical boundaries only.\n")
    
    for filepath in TARGET_FILES:
        process_file(filepath)
        
    if TARGET_FILES:
        print("\n" + "="*60)
        process_hoax(TARGET_FILES[0])
        
    print("\n=========================================================")
    print("PHASE IV COMPLETE.")
    print("=========================================================")

if __name__ == "__main__":
    main()