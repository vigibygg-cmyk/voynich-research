import pandas as pd
import numpy as np
import os
import time

def extract_triplets(text):
    words = str(text).split()
    triplets = []
    # Using sliding window of 3, non-overlapping to simulate instruction blocks
    # e.g., words[0:3], words[3:6]
    for i in range(0, len(words) - 2, 3):
        triplets.append((words[i], words[i+1], words[i+2]))
    return triplets

def count_positional_affixes(triplets, affixes):
    counts = {affix: {1: 0, 2: 0, 3: 0} for affix in affixes}
    
    for t in triplets:
        for idx, w in enumerate(t):
            pos = idx + 1
            for affix in affixes:
                if affix.endswith('-'):
                    if w.startswith(affix[:-1]):
                        counts[affix][pos] += 1
                elif affix.startswith('-'):
                    if w.endswith(affix[1:]):
                        counts[affix][pos] += 1
    return counts

def analyze_mechanical_key(file_path, affixes, iterations=100):
    df = pd.read_csv(file_path)
    
    all_triplets = []
    for _, row in df.iterrows():
        all_triplets.extend(extract_triplets(row['Clean_Text']))
        
    total_triplets = len(all_triplets)
    if total_triplets == 0:
        return pd.DataFrame()
        
    real_counts = count_positional_affixes(all_triplets, affixes)
    
    # Baseline simulation
    baseline_stats = {affix: {1: [], 2: [], 3: []} for affix in affixes}
    
    # Extract all words from triplets to shuffle
    all_words = []
    for t in all_triplets:
        all_words.extend(t)
    all_words = np.array(all_words)
    
    print(f"Running {iterations} chaos iterations for {os.path.basename(file_path)}...")
    start_t = time.time()
    
    for i in range(iterations):
        np.random.shuffle(all_words)
        
        shuffled_triplets = []
        for j in range(0, len(all_words) - 2, 3):
            shuffled_triplets.append((all_words[j], all_words[j+1], all_words[j+2]))
            
        shuffled_counts = count_positional_affixes(shuffled_triplets, affixes)
        
        for affix in affixes:
            for pos in [1, 2, 3]:
                baseline_stats[affix][pos].append(shuffled_counts[affix][pos])
                
        if (i+1) % 25 == 0:
            print(f"  Iteration {i+1}/{iterations} completed in {time.time()-start_t:.2f}s")

    results = []
    for affix in affixes:
        for pos in [1, 2, 3]:
            real_count = real_counts[affix][pos]
            baseline = np.array(baseline_stats[affix][pos])
            mean_base = np.mean(baseline)
            std_base = np.std(baseline)
            z_score = (real_count - mean_base) / std_base if std_base > 0 else 0
            
            # Calculate percentage within the triplet for this affix
            total_affix_count = sum(real_counts[affix].values())
            percent = (real_count / total_affix_count * 100) if total_affix_count > 0 else 0
            
            results.append({
                'Transcription': os.path.basename(file_path).split('_')[0],
                'Affix': affix,
                'Position': pos,
                'Real_Count': real_count,
                'Distribution_%': round(percent, 2),
                'Baseline_Mean': round(mean_base, 2),
                'Z_Score': round(z_score, 2)
            })
            
    return pd.DataFrame(results)

def main():
    base_dir = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"
    files = ["IT2a-n_clean.csv", "RF1b-er_clean.csv", "ZL3b-n_clean.csv"]
    
    affixes = ['qok-', 'che-', 'sh-', 'ok-', '-edy', '-dy', 'daiin-', '-daiin', 'chol-']
    
    all_results = []
    for f in files:
        path = os.path.join(base_dir, f)
        res = analyze_mechanical_key(path, affixes, iterations=100)
        all_results.append(res)
        
    final_df = pd.concat(all_results, ignore_index=True)
    out_path = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\34_Mechanical_Key_Results.csv"
    final_df.to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}\n")
    
    sig = final_df[abs(final_df['Z_Score']) > 3.0].sort_values(by=['Transcription', 'Affix', 'Position'])
    print("\n--- SIGNIFICANT POSITIONAL BIAS (Z > |3.0|) ---")
    print(sig.to_string(index=False))
    
    with open(r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\34_Mechanical_Key_Report_draft.md", 'w') as f:
        f.write("# Phase 34: Mechanical Key (3-Position Grammar) Testing\n\n")
        f.write("## Overview\n")
        f.write("Validation of the 3-position triplet instruction grammar.\n\n")
        f.write("## Significant Findings\n")
        f.write("```text\n")
        f.write(sig.to_string(index=False))
        f.write("\n```\n")

if __name__ == "__main__":
    main()
