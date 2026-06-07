import pandas as pd
import re
from collections import defaultdict
import os

# -------------------------------------------------------------------------
# Phase 114: Taxonomic Stem Section Distribution
# -------------------------------------------------------------------------

PREFIXES = ['qo', 'ch', 'sh', 'o', 'y', 's', 'd']
SUFFIXES = ['dy', 'in', 'ol', 'am', 'al', 'ar', 'ey', 'hy', 'ho', 'y']
PREFIXES.sort(key=len, reverse=True)
SUFFIXES.sort(key=len, reverse=True)

def extract_pure_stem(word):
    w = str(word).lower()
    stripped = True
    while stripped and len(w) > 0:
        stripped = False
        for p in PREFIXES:
            if w.startswith(p):
                w = w[len(p):]
                stripped = True
                break
        for s in SUFFIXES:
            if w.endswith(s):
                w = w[:-len(s)]
                stripped = True
                break
    return w

def get_section(folio):
    match = re.search(r'\d+', str(folio))
    if not match: return 'Unknown'
    num = int(match.group())
    if 1 <= num <= 57: return 'Herbal'
    if 67 <= num <= 73: return 'Astronomical'
    if 75 <= num <= 84: return 'Biological'
    if 85 <= num <= 86: return 'Cosmological'
    if 87 <= num <= 102: return 'Pharmaceutical'
    if 103 <= num <= 116: return 'Recipes'
    return 'Unknown'

if __name__ == "__main__":
    file_path = 'voynich_clean_data/IT2a-n_clean.csv'
    df = pd.read_csv(file_path)
    
    section_words = defaultdict(list)
    
    # Extract stems and assign to sections
    for _, row in df.iterrows():
        folio = row['Folio']
        section = get_section(folio)
        if section == 'Unknown': continue
        
        words = str(row['Clean_Text']).split()
        for w in words:
            stem = extract_pure_stem(w)
            if len(stem) > 0:
                section_words[section].append(stem)
                
    # Get overall Top 30 stems across the whole manuscript
    all_stems = []
    for stems in section_words.values():
        all_stems.extend(stems)
        
    overall_counts = pd.Series(all_stems).value_counts()
    top_30_stems = overall_counts.head(30).index.tolist()
    
    # Calculate Relative Frequency (per 10,000 valid stems) for each section
    results = []
    for section, stems in section_words.items():
        total_in_sec = len(stems)
        sec_counts = pd.Series(stems).value_counts()
        
        for stem in top_30_stems:
            count = sec_counts.get(stem, 0)
            rel_freq = (count / total_in_sec) * 10000 if total_in_sec > 0 else 0
            results.append({
                'Section': section,
                'Stem': stem,
                'Count': count,
                'RelFreq_10k': round(rel_freq, 1)
            })
            
    results_df = pd.DataFrame(results)
    
    print("--- Phase 114: TAXONOMIC STEM BIAS BY SECTION ---\n")
    print("We calculate the Relative Frequency (per 10,000 words) of stems in each section.")
    print("If a stem is a taxonomic index, it should spike in specific sections.\n")
    
    # Find stems that have extreme bias toward one section
    for stem in top_30_stems:
        stem_data = results_df[results_df['Stem'] == stem].copy()
        if stem_data.empty: continue
        
        # Calculate the average frequency across all sections
        avg_freq = stem_data['RelFreq_10k'].mean()
        
        # Sort to find the highest frequency section
        stem_data = stem_data.sort_values(by='RelFreq_10k', ascending=False)
        top_sec = stem_data.iloc[0]
        
        # If the top section is > 1.5x the average, it's a significant bias
        if top_sec['RelFreq_10k'] > (avg_freq * 1.5) and top_sec['Count'] > 20:
            print(f"Index '{stem}' -> Strongly tied to: {top_sec['Section'].upper()}")
            print(f"   {top_sec['Section']}: {top_sec['RelFreq_10k']} per 10k")
            print(f"   (Average across all sections: {avg_freq:.1f} per 10k)")
            
            # Show the lowest section for contrast
            bottom_sec = stem_data.iloc[-1]
            print(f"   Lowest in {bottom_sec['Section']}: {bottom_sec['RelFreq_10k']} per 10k\n")

    # Export
    out_path = 'Kiti_Rezultatai_per_nauja/Phase_114_Taxonomic_Distribution.csv'
    results_df.to_csv(out_path, index=False)
    print(f"Full distribution data saved to: {out_path}")
