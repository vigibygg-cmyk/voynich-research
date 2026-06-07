# ==============================================================================
# VOYNICH MANUSCRIPT: DIFFERENTIAL MORPHOLOGICAL FRAMING (PHASE X)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import re
import os
import random
import numpy as np
from collections import defaultdict, Counter

# Configuration - Triangulation
TARGET_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv"
]
PREFIX_LENGTHS = [2, 3] # We test 2-char and 3-char prefixes blindly

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]', ' ', text)
    text = re.sub(r'<.*?>', ' ', text)
    text = re.sub(r'<>', ' ', text)
    text = re.sub(r'\$\w+', ' ', text)
    text = re.sub(r'[^a-zA-Z\s]', ' ', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_visual_category(folio_str):
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Unknown"
    num = int(match.group(1))
    
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 88 <= num <= 102: return "Pharmaceutical"
    elif 103 <= num <= 116: return "Recipes"
    else: return "Unknown"

def generate_hoax_dataframe(df):
    """Simulates a hoax by globally shuffling characters, destroying morphology."""
    hoax_df = df.copy()
    full_text = " ".join(hoax_df['Deep_Clean_Text'].dropna().tolist())
    chars = list(full_text.replace(" ", ""))
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
            l = len(w)
            new_w = "".join(chars[char_idx : char_idx + l])
            new_words.append(new_w)
            char_idx += l
        shuffled_text_blocks.append(" ".join(new_words))
        
    hoax_df['Deep_Clean_Text'] = shuffled_text_blocks
    return hoax_df

def blind_overlap_discovery(df):
    prefix_section_counts = defaultdict(lambda: defaultdict(int))
    all_counts = []
    
    for _, row in df.iterrows():
        text = str(row['Deep_Clean_Text'])
        if not text: continue
        
        cat = get_visual_category(row['Folio'])
        if cat == "Unknown": continue
            
        words = text.split()
        for word in words:
            for length in PREFIX_LENGTHS:
                if len(word) > length:
                    prefix = word[:length]
                    prefix_section_counts[prefix][cat] += 1
                    
    for counts in prefix_section_counts.values():
        all_counts.extend(counts.values())
        
    if not all_counts: return {}
    
    # Dynamic threshold: 95th percentile of all valid prefix-section combinations
    threshold = max(5, np.percentile(all_counts, 95))
                    
    overlapping_anchors = {}
    for prefix, section_counts in prefix_section_counts.items():
        valid_sections = [sec for sec, count in section_counts.items() if count >= threshold]
        if len(valid_sections) >= 2:
            overlapping_anchors[prefix] = valid_sections
            
    return overlapping_anchors

def extract_morphological_frames(df, anchor, valid_sections):
    frames_by_section = {sec: Counter() for sec in valid_sections}
    
    for _, row in df.iterrows():
        text = str(row['Deep_Clean_Text'])
        if not text: continue
        
        cat = get_visual_category(row['Folio'])
        if cat not in valid_sections: continue
            
        words = text.split()
        for word in words:
            if word.startswith(anchor) and len(word) > len(anchor):
                frame = word[len(anchor):]
                frames_by_section[cat][frame] += 1
                
    return frames_by_section

def analyze_polymorphism(df, source_name):
    print(f"\n[*] ANALYZING DIFFERENTIAL GRAMMAR FOR: [{source_name}]")
    
    overlapping_anchors = blind_overlap_discovery(df)
    
    if not overlapping_anchors:
        print("    [-] No statistically significant overlapping anchors discovered.")
        return

    sorted_anchors = sorted(overlapping_anchors.items(), key=lambda x: (len(x[1]), x[0]), reverse=True)
    
    print(f"    [+] Blindly discovered {len(sorted_anchors)} valid overlapping anchors.")
    
    for anchor, sections in sorted_anchors[:3]:
        print(f"\n    >> TARGET ANCHOR: '{anchor}-' (Overlaps in: {', '.join(sections)})")
        frames_data = extract_morphological_frames(df, anchor, sections)
        
        for section in sections:
            frames_counter = frames_data[section]
            total_frames = sum(frames_counter.values())
            
            top_frames = frames_counter.most_common(3)
            frames_str = " | ".join([f"-{f} ({c})" for f, c in top_frames])
            
            print(f"       [{section:<14}] Total: {total_frames:<4} | Top Suffixes: {frames_str}")

def main():
    print("=== Voynich Phase X: Blind Micro-Polymorphism Analysis ===\n")
    print("Objective: Mathematically verify if grammatical suffixes change")
    print("dynamically based on visual section, without a priori targets.")
    
    for filepath in TARGET_FILES:
        if not os.path.exists(filepath):
            print(f"[-] Error: File {filepath} not found.")
            continue
            
        source_name = filepath.split('/')[-1]
        df = pd.read_csv(filepath)
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        analyze_polymorphism(df, source_name)
        
    if TARGET_FILES and os.path.exists(TARGET_FILES[0]):
        print("\n" + "="*70)
        print("[*] RUNNING CHAOS CONTROL (RANDOM_HOAX_BASELINE)")
        print("    Hypothesis: Randomized morphology will fail to produce structured overlap.")
        print("="*70)
        df = pd.read_csv(TARGET_FILES[0])
        df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
        hoax_df = generate_hoax_dataframe(df)
        analyze_polymorphism(hoax_df, "RANDOM_HOAX_BASELINE")
        
    print("\n=================================================================")
    print("PHASE X COMPLETE. Evaluate suffix frame divergence between sections.")
    print("=================================================================")

if __name__ == "__main__":
    main()