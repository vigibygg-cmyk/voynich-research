import pandas as pd
import numpy as np
import os
import time

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    return previous_row[-1]

def analyze_ed1(file_path, iterations=100):
    df = pd.read_csv(file_path)
    
    real_ed1_count = 0
    expansions = 0
    contractions = 0
    substitutions = 0
    total_pairs = 0
    
    lines = []
    for _, row in df.iterrows():
        words = str(row['Clean_Text']).split()
        if len(words) > 1:
            lines.append(words)
            
            for i in range(len(words)-1):
                total_pairs += 1
                w1, w2 = words[i], words[i+1]
                dist = levenshtein_distance(w1, w2)
                if dist == 1:
                    real_ed1_count += 1
                    if len(w2) > len(w1):
                        expansions += 1
                    elif len(w2) < len(w1):
                        contractions += 1
                    else:
                        substitutions += 1
                        
    # Baseline simulation
    baseline_ed1_counts = []
    print(f"Running {iterations} chaos iterations for {os.path.basename(file_path)}...")
    start_t = time.time()
    
    for i in range(iterations):
        shuffled_ed1 = 0
        for words in lines:
            shuffled_words = words.copy()
            np.random.shuffle(shuffled_words)
            for j in range(len(shuffled_words)-1):
                w1, w2 = shuffled_words[j], shuffled_words[j+1]
                if abs(len(w1) - len(w2)) > 1:
                    continue # Optimization
                dist = levenshtein_distance(w1, w2)
                if dist == 1:
                    shuffled_ed1 += 1
        baseline_ed1_counts.append(shuffled_ed1)
        
        if (i+1) % 25 == 0:
            print(f"  Iteration {i+1}/{iterations} completed in {time.time()-start_t:.2f}s")
            
    mean_base = np.mean(baseline_ed1_counts)
    std_base = np.std(baseline_ed1_counts)
    z_score = (real_ed1_count - mean_base) / std_base if std_base > 0 else 0
    
    return {
        'Transcription': os.path.basename(file_path).split('_')[0],
        'Total_Adjacent_Pairs': total_pairs,
        'Real_ED1_Count': real_ed1_count,
        'ED1_Rate_Percent': round((real_ed1_count / total_pairs) * 100, 2),
        'Expansions_Percent': round((expansions / real_ed1_count) * 100, 2) if real_ed1_count > 0 else 0,
        'Contractions_Percent': round((contractions / real_ed1_count) * 100, 2) if real_ed1_count > 0 else 0,
        'Substitutions_Percent': round((substitutions / real_ed1_count) * 100, 2) if real_ed1_count > 0 else 0,
        'Baseline_Mean_ED1': round(mean_base, 2),
        'Z_Score': round(z_score, 2)
    }

def main():
    base_dir = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"
    files = ["IT2a-n_clean.csv", "RF1b-er_clean.csv", "ZL3b-n_clean.csv"]
    
    all_results = []
    for f in files:
        path = os.path.join(base_dir, f)
        res = analyze_ed1(path, iterations=100)
        all_results.append(res)
        
    final_df = pd.DataFrame(all_results)
    out_path = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\32_ED1_Ledger_Results.csv"
    final_df.to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}\n")
    print(final_df.to_string(index=False))
    
    with open(r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\32_ED1_Ledger_Report_draft.md", 'w') as f:
        f.write("# Phase 32: ED1 Ledger Generation Testing\n\n")
        f.write("## Overview\n")
        f.write("Validation of Kinnison's One-Page Ledger ED1 mutation and Markov directionality.\n\n")
        f.write("## Results\n")
        f.write("```text\n")
        f.write(final_df.to_string(index=False))
        f.write("\n```\n")

if __name__ == "__main__":
    main()
