import pandas as pd
import numpy as np
import collections
import string
import os

def build_profile(words):
    counts = collections.Counter()
    total_chars = 0
    for w in words:
        counts.update(w)
        total_chars += len(w)
    
    # Normalize to probabilities
    profile = {}
    if total_chars > 0:
        for char in string.ascii_lowercase:  # EVA is lowercase a-z
            profile[char] = counts.get(char, 0) / total_chars
    else:
        for char in string.ascii_lowercase:
            profile[char] = 0.0
            
    return profile

def analyze_gallows(file_path):
    df = pd.read_csv(file_path)
    
    gallows = ['k', 't', 'p', 'f']
    remainders = {g: [] for g in gallows}
    
    for _, row in df.iterrows():
        text = str(row['Clean_Text']).split()
        for w in text:
            for g in gallows:
                if w.startswith(g) and len(w) > 1:
                    remainders[g].append(w[1:]) # strip the gallows char
                    break
                    
    profiles = {}
    word_counts = {}
    for g in gallows:
        profiles[g] = build_profile(remainders[g])
        word_counts[g] = len(remainders[g])
        
    # Convert to vectors for correlation
    vectors = {}
    for g in gallows:
        vectors[g] = [profiles[g][c] for c in string.ascii_lowercase]
        
    # Correlation Matrix
    corr_matrix = np.zeros((4, 4))
    for i, g1 in enumerate(gallows):
        for j, g2 in enumerate(gallows):
            if np.sum(vectors[g1]) == 0 or np.sum(vectors[g2]) == 0:
                corr_matrix[i][j] = 0.0
            else:
                corr_matrix[i][j] = np.corrcoef(vectors[g1], vectors[g2])[0, 1]
                
    # Flatten results for DataFrame
    results = []
    for i, g1 in enumerate(gallows):
        for j, g2 in enumerate(gallows):
            if i < j:
                results.append({
                    'Transcription': os.path.basename(file_path).split('_')[0],
                    'Gallows_Pair': f"{g1} vs {g2}",
                    'Pearson_Correlation': round(corr_matrix[i][j], 4),
                    'Word_Count_1': word_counts[g1],
                    'Word_Count_2': word_counts[g2]
                })
                
    return pd.DataFrame(results)

def main():
    base_dir = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"
    files = ["IT2a-n_clean.csv", "RF1b-er_clean.csv", "ZL3b-n_clean.csv"]
    
    all_results = []
    for f in files:
        path = os.path.join(base_dir, f)
        res = analyze_gallows(path)
        all_results.append(res)
        
    final_df = pd.concat(all_results, ignore_index=True)
    out_path = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\33_Gallows_Shift_Results.csv"
    final_df.to_csv(out_path, index=False)
    print(f"\nResults saved to {out_path}\n")
    print(final_df.to_string(index=False))
    
    with open(r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\33_Gallows_Shift_Report_draft.md", 'w') as f:
        f.write("# Phase 33: Gallows Polyalphabetic Shift Test\n\n")
        f.write("## Overview\n")
        f.write("Testing the Alberti Cipher Disk shift hypothesis for gallows characters.\n\n")
        f.write("## Results\n")
        f.write("```text\n")
        f.write(final_df.to_string(index=False))
        f.write("\n```\n")

if __name__ == "__main__":
    main()
