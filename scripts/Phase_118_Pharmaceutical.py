import pandas as pd
from collections import Counter
import re
import os

# -------------------------------------------------------------------------
# Phase 118: Objective Pharmaceutical Stem Extraction
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

def is_pharmaceutical(folio_str):
    match = re.search(r'\d+', str(folio_str))
    if match:
        num = int(match.group())
        return 87 <= num <= 102
    return False

def analyze_pharma(file_path):
    if not os.path.exists(file_path): return None
    df = pd.read_csv(file_path)
    
    col_name = 'Clean_Text' if 'Clean_Text' in df.columns else 'text'
    pharma_df = df[df['Folio'].apply(is_pharmaceutical)]
    
    words = []
    for text in pharma_df[col_name].dropna():
        words.extend(str(text).split())
        
    stems = []
    for w in words:
        s = extract_pure_stem(w)
        if len(s) > 0: stems.append(s)
        
    return Counter(stems), len(stems)

if __name__ == "__main__":
    files = [
        'voynich_clean_data/IT2a-n_clean.csv',
        'voynich_clean_data/RF1b-er_clean.csv',
        'voynich_clean_data/ZL3b-n_clean.csv'
    ]
    
    all_results = {}
    for f in files:
        name = os.path.basename(f).split('_')[0]
        res = analyze_pharma(f)
        if res: all_results[name] = res
        
    if not all_results:
        exit()
        
    # Get consensus (stems that appear in top 40 across all 3 transcriptions)
    top_n = 40
    stem_sets = []
    for name, (counts, total) in all_results.items():
        top = [s for s, c in counts.most_common(top_n)]
        stem_sets.append(set(top))
        
    consensus = set.intersection(*stem_sets)
    
    # Sort consensus by IT frequency
    it_counts = all_results['IT2a-n'][0]
    total_it = all_results['IT2a-n'][1]
    sorted_consensus = sorted(list(consensus), key=lambda x: it_counts[x], reverse=True)
    
    report = ["# Phase 118: Objective Pharmaceutical Stem Extraction\n"]
    report.append("## Methodology")
    report.append("We isolated the Pharmaceutical section (f87-f102), which visually depicts alchemy jars and isolated plant parts (roots, leaves). We performed pure stem extraction across all 3 transcriptions (IT, RF, ZL) to eliminate transcriber bias. No phonetic or linguistic forcing was applied.\n")
    
    report.append(f"- **Total Valid Stems (IT Trans):** {total_it}\n")
    
    report.append("## Consensus Top Stems (Pharmaceutical Section)")
    report.append("These stems appear in the Top 40 most frequent stems across ALL THREE independent transcriptions. They are mathematically robust targets for visual mapping against the jars and roots.\n")
    
    report.append("| Rank | Pure Stem | IT Freq | RF Freq | ZL Freq | % of Section (IT) |")
    report.append("|---|---|---|---|---|---|")
    
    for i, stem in enumerate(sorted_consensus):
        it_f = it_counts[stem]
        rf_f = all_results['RF1b-er'][0][stem]
        zl_f = all_results['ZL3b-n'][0][stem]
        pct = (it_f / total_it) * 100
        report.append(f"| {i+1} | **{stem}** | {it_f} | {rf_f} | {zl_f} | {pct:.1f}% |")
        
    out_path = 'Protokolai ir raportai/Phase_118_Pharmaceutical_Stems.md'
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(report))
        
    print(f"--- Phase 118 Complete ---")
    print(f"Report saved to: {out_path}")
    print("\nTop 10 Consensus Pharmaceutical Stems:")
    for i, stem in enumerate(sorted_consensus[:10]):
        print(f"{i+1}. {stem} ({it_counts[stem]} times)")
