import pandas as pd
from collections import defaultdict

# -------------------------------------------------------------------------
# Phase 113: The Ironclad Rule (Finite State Machine of Stems)
# -------------------------------------------------------------------------

def extract_ironclad_rules(file_path):
    df = pd.read_csv(file_path)
    
    # We only care about multi-letter stems to see transitions
    # Format of data: Stem, Frequency, Length
    stems = []
    for _, row in df.iterrows():
        stem = str(row['Stem'])
        freq = int(row['Frequency'])
        if len(stem) > 0 and stem != 'nan':
            # Add boundary markers
            stems.extend([f"^{stem}$"] * freq)
            
    # Calculate transitions: Character A -> Character B
    transitions = defaultdict(lambda: defaultdict(int))
    char_counts = defaultdict(int)
    
    for stem in stems:
        for i in range(len(stem) - 1):
            char_a = stem[i]
            char_b = stem[i+1]
            transitions[char_a][char_b] += 1
            char_counts[char_a] += 1
            
    print(f"--- THE IRONCLAD RULES OF VMS STEMS ---")
    print(f"Total Stems Analyzed: {len(stems)}")
    print("Rule: If you see [Char A], what MUST follow it?\n")
    
    # Identify ironclad rules (>90% probability)
    ironclad_found = False
    for char_a, count_a in sorted(char_counts.items(), key=lambda x: x[1], reverse=True):
        if count_a < 100:  # Ignore rare characters
            continue
            
        print(f"When stem has '{char_a}' (Total occurrences: {count_a}):")
        
        # Sort targets by frequency
        targets = sorted(transitions[char_a].items(), key=lambda x: x[1], reverse=True)
        for char_b, count_b in targets:
            prob = (count_b / count_a) * 100
            
            # Print if it's a major pathway
            if prob > 15:
                direction = "END OF STEM" if char_b == '$' else f"'{char_b}'"
                marker = "*** IRONCLAD ***" if prob > 85 else ""
                print(f"  -> Goes to {direction}: {prob:.1f}% ({count_b} times) {marker}")
        print()

if __name__ == "__main__":
    file_path = 'Kiti_Rezultatai_per_nauja/Phase_112b_IT2a-n_Stems.csv'
    extract_ironclad_rules(file_path)
