import pandas as pd
from collections import Counter
import re
import os

# -------------------------------------------------------------------------
# Phase 117: Picatrix Lunar Mansion Alignment (Astronomical Section)
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

def is_astronomical(folio_str):
    match = re.search(r'\d+', str(folio_str))
    if match:
        num = int(match.group())
        return 67 <= num <= 73
    return False

if __name__ == "__main__":
    print("--- Phase 117: Astronomical Section vs. 28 Lunar Mansions ---")
    
    file_path = 'voynich_clean_data/IT2a-n_clean.csv'
    df = pd.read_csv(file_path)
    
    # Isolate Astronomical section
    astro_df = df[df['Folio'].apply(is_astronomical)]
    
    raw_words = []
    for text in astro_df['Clean_Text'].dropna():
        raw_words.extend(str(text).split())
        
    pure_stems = []
    
    for word in raw_words:
        stem = extract_pure_stem(word)
        if len(stem) > 0:
            pure_stems.append(stem)
            
    stem_counts = Counter(pure_stems)
    total_stems = len(pure_stems)
    
    print(f"\nTotal Valid Stems in Astronomical Section: {total_stems}")
    print(f"Total Unique Stems: {len(stem_counts)}")
    
    # We are looking for the 'Core' identifiers. If there are 28 Lunar Mansions,
    # we expect the top ~28 stems to dominate the distribution.
    
    top_28_stems = stem_counts.most_common(28)
    
    # Calculate what percentage of the total text these top 28 stems make up
    top_28_total_occurrences = sum([count for stem, count in top_28_stems])
    coverage_percent = (top_28_total_occurrences / total_stems) * 100
    
    print(f"\n--- TOP 28 ASTRONOMICAL STEMS ---")
    print(f"These 28 stems account for {coverage_percent:.1f}% of all valid words in this section.")
    print("Rank | Stem | Frequency | % of Section")
    print("-" * 50)
    
    report = ["# Phase 117: Picatrix 28 Lunar Mansions Alignment\n"]
    report.append("## Hypothesis")
    report.append("The Astronomical section of the VMS (f67-f73) corresponds to the 28 Lunar Mansions detailed in the Arabic *Picatrix*. If true, the taxonomic indices (stems) in this section should cluster tightly around ~28 dominant groups.\n")
    
    report.append(f"- **Total Stems Analyzed:** {total_stems}")
    report.append(f"- **Top 28 Coverage:** {coverage_percent:.1f}% of the entire section.\n")
    
    report.append("## The 28 Dominant Astronomical Indices")
    report.append("| Rank | VMS Stem | Frequency | Potential Picatrix Mansion Match |")
    report.append("|---|---|---|---|")
    
    for i, (stem, count) in enumerate(top_28_stems):
        pct = (count / total_stems) * 100
        print(f"{i+1:4} | {stem:<10} | {count:4} | {pct:.1f}%")
        # Placeholder for Picatrix match (1 through 28)
        report.append(f"| {i+1} | **{stem}** | {count} ({pct:.1f}%) | Mansion {i+1} |")
        
    print("-" * 50)
    
    out_path = 'Protokolai ir raportai/Phase_117_Picatrix_Alignment.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"\nAlignment mapping saved to: {out_path}")
