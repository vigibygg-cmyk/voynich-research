import pandas as pd
import random
from collections import defaultdict, Counter

def generate_timm_schinner_text(vocab_seed, length=10000, memory_size=5, mutation_rate=0.2):
    """
    Generates text using a simplified Timm & Schinner self-citation model.
    - Chooses words mostly from recent memory.
    - Occasionally mutates a word (changes/adds/removes a character).
    """
    if not vocab_seed:
        return []

    # Valid chars from basic EVA
    chars = "abcdefghijklmnopqrstuvwxyz"
    
    text = [random.choice(vocab_seed)]
    
    for _ in range(length - 1):
        # Determine source word: high chance from recent memory, low chance from global
        if len(text) > 0 and random.random() < 0.8:
            # Self-citation: Pick from recent memory
            lookback = min(len(text), memory_size)
            source_word = random.choice(text[-lookback:])
        else:
            # Random novel seed
            source_word = random.choice(vocab_seed)
            
        # Apply mutation (simulate scribe changing a prefix/suffix slightly)
        if random.random() < mutation_rate and len(source_word) > 1:
            mutation_type = random.choice(['sub', 'add', 'del'])
            pos = random.randint(0, len(source_word) - 1)
            if mutation_type == 'sub':
                source_word = source_word[:pos] + random.choice(chars) + source_word[pos+1:]
            elif mutation_type == 'add':
                source_word = source_word[:pos] + random.choice(chars) + source_word[pos:]
            elif mutation_type == 'del' and len(source_word) > 2:
                source_word = source_word[:pos] + source_word[pos+1:]
                
        text.append(source_word)
        
    return text

def calculate_markov_directionality(text_words):
    """
    Calculates 1st order transitions to measure Directional Flow vs Cyclic loops.
    Forward Flow: A -> B
    Backward/Cyclic Flow: A -> B -> A or A -> A
    """
    transitions = defaultdict(Counter)
    
    for i in range(len(text_words) - 1):
        w1 = text_words[i]
        w2 = text_words[i+1]
        transitions[w1][w2] += 1
        
    forward_count = 0
    backward_count = 0
    
    # Analyze topology
    for w1, targets in transitions.items():
        for w2, count in targets.items():
            if w1 == w2:
                # Self-loop (A -> A)
                backward_count += count
            elif w1 in transitions.get(w2, {}):
                # Bidirectional / Cyclic (A -> B and B -> A exist)
                backward_count += count
            else:
                # Strictly Forward / Transitive (A -> B only)
                forward_count += count
                
    total = forward_count + backward_count
    if total == 0:
        return 0, 0
        
    forward_pct = (forward_count / total) * 100
    backward_pct = (backward_count / total) * 100
    
    return forward_pct, backward_pct

if __name__ == "__main__":
    file_it2a = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data\IT2a-n_clean.csv"
    
    print("Reading Authentic Voynich Text...")
    df = pd.read_csv(file_it2a)
    authentic_words = " ".join(df['Clean_Text'].dropna().astype(str).tolist()).split()
    
    # Extract seed vocabulary
    vocab_seed = list(set(authentic_words[:5000]))
    
    print("Generating Timm & Schinner Baseline (15,000 words)...")
    timm_text = generate_timm_schinner_text(vocab_seed, length=15000, memory_size=5, mutation_rate=0.15)
    
    print("\n--- Markov Directionality Test ---")
    
    auth_fw, auth_bw = calculate_markov_directionality(authentic_words[:15000])
    print(f"Authentic Voynich (IT2a-n):")
    print(f"  Forward Flow: {auth_fw:.2f}%")
    print(f"  Cyclic/Backward Flow: {auth_bw:.2f}%")
    
    timm_fw, timm_bw = calculate_markov_directionality(timm_text)
    print(f"\nTimm & Schinner Baseline:")
    print(f"  Forward Flow: {timm_fw:.2f}%")
    print(f"  Cyclic/Backward Flow: {timm_bw:.2f}%")
