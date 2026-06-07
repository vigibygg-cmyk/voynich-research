import pandas as pd
import numpy as np
import re
import os
import time

def get_section(folio):
    folio_num_match = re.search(r'\d+', str(folio))
    if not folio_num_match:
        return 'Unknown'
    num = int(folio_num_match.group())
    if 1 <= num <= 57: return 'Herbal'
    if 67 <= num <= 73: return 'Astronomical'
    if 75 <= num <= 84: return 'Biological'
    if 85 <= num <= 86: return 'Cosmological'
    if 87 <= num <= 102: return 'Pharmaceutical'
    if 103 <= num <= 116: return 'Recipes'
    return 'Unknown'

def count_affixes(words, affixes):
    counts = {affix: 0 for affix in affixes}
    for w in words:
        for affix in affixes:
            if affix.endswith('-'):
                if w.startswith(affix[:-1]):
                    counts[affix] += 1
            elif affix.startswith('-'):
                if w.endswith(affix[1:]):
                    counts[affix] += 1
    return counts

def analyze_transcription(file_path, affixes, iterations=1000):
    df = pd.read_csv(file_path)
    df['Section'] = df['Folio'].apply(get_section)
    
    # Extract all words with their sections
    words_data = []
    for _, row in df.iterrows():
        text = str(row['Clean_Text']).split()
        section = row['Section']
        for w in text:
            words_data.append({'word': w, 'section': section})
            
    words_df = pd.DataFrame(words_data)
    
    # Real counts
    sections = words_df['section'].unique()
    real_counts = {sec: {affix: 0 for affix in affixes} for sec in sections}
    total_words_sec = words_df['section'].value_counts().to_dict()
    
    for sec in sections:
        sec_words = words_df[words_df['section'] == sec]['word'].tolist()
        counts = count_affixes(sec_words, affixes)
        for affix in affixes:
            real_counts[sec][affix] = counts[affix]
            
    # Baseline simulation
    np.random.seed(42)
    baseline_stats = {sec: {affix: [] for affix in affixes} for sec in sections}
    all_words = words_df['word'].values
    
    print(f"Running {iterations} chaos iterations for {os.path.basename(file_path)}...")
    start_t = time.time()
    for i in range(iterations):
        np.random.shuffle(all_words)
        idx = 0
        for sec in sections:
            sec_len = total_words_sec[sec]
            sec_words = all_words[idx:idx+sec_len]
            idx += sec_len
            
            counts = count_affixes(sec_words, affixes)
            for affix in affixes:
                baseline_stats[sec][affix].append(counts[affix])
        
        if (i+1) % 250 == 0:
            print(f"  Iteration {i+1}/{iterations} completed in {time.time()-start_t:.2f}s")
            
    # Compute Z-Scores and Relative Frequencies
    results = []
    for sec in sections:
        for affix in affixes:
            real_count = real_counts[sec][affix]
            rel_freq = (real_count / total_words_sec[sec]) * 10000 if total_words_sec[sec] > 0 else 0
            
            baseline = np.array(baseline_stats[sec][affix])
            mean_base = np.mean(baseline)
            std_base = np.std(baseline)
            z_score = (real_count - mean_base) / std_base if std_base > 0 else 0
            
            results.append({
                'Transcription': os.path.basename(file_path).split('_')[0],
                'Section': sec,
                'Affix': affix,
                'Total_Words': total_words_sec[sec],
                'Count': real_count,
                'RelFreq_10k': round(rel_freq, 2),
                'Z-Score': round(z_score, 2)
            })
            
    return pd.DataFrame(results)

def main():
    base_dir = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data"
    files = ["IT2a-n_clean.csv", "RF1b-er_clean.csv", "ZL3b-n_clean.csv"]
    
    affixes = ['qok-', 'che-', 'kch-', 'sh-', 'ok-', '-edy', '-eody', '-dy']
    
    all_results = []
    for f in files:
        path = os.path.join(base_dir, f)
        df_res = analyze_transcription(path, affixes, iterations=1000)
        all_results.append(df_res)
        
    final_df = pd.concat(all_results, ignore_index=True)
    out_path = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\31_Vigslist_Taxonomy_Results.csv"
    final_df.to_csv(out_path, index=False)
    print(f"Results saved to {out_path}")
    
    # Print summary of highly significant positive clustering
    print("\n--- HIGHLY SIGNIFICANT CLUSTERING (Z > 5.0) ---")
    sig = final_df[final_df['Z-Score'] > 5.0].sort_values(by='Z-Score', ascending=False)
    print(sig.to_string(index=False))
    
    # Format a Markdown report structure to standard out
    with open(r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Kiti_Rezultatai_per_nauja\31_Vigslist_Taxonomy_Report_draft.md", 'w') as f:
        f.write("# Phase 31: Vigslist Taxonomy Validation\n\n")
        f.write("## Overview\n")
        f.write("This report details the statistical distribution of Richard Vigslist's proposed pharmacological stems and suffixes.\n\n")
        f.write("## Significant Findings\n")
        f.write("```text\n")
        f.write(sig.to_string(index=False))
        f.write("\n```\n")

if __name__ == "__main__":
    main()
