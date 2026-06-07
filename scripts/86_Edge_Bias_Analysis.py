import os
import sys
import csv
import collections

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

CLEAN_DATA_FILE = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data\RF1b-er_clean.csv"

print("# Phase 86: \"Nulls\" and Steganography Analysis at Microscopic Level (Edge Bias)")
print("Hypothesis E from Phase 82 plan: Check if certain symbols/prefixes perform steganographic function or denote hidden variables (time/temperature), based on their placement at line start, middle or end (Edge Bias).\n")

if not os.path.exists(CLEAN_DATA_FILE):
    print(f"Klaida: Nerastas failas {CLEAN_DATA_FILE}")
    sys.exit(1)

# Skaitikliai
start_chars = collections.Counter()
end_chars = collections.Counter()
middle_chars = collections.Counter()

start_prefixes = collections.Counter()
middle_prefixes = collections.Counter()

end_suffixes = collections.Counter()
middle_suffixes = collections.Counter()

total_lines = 0
total_middle_words = 0

with open(CLEAN_DATA_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        text = row['Clean_Text'].strip()
        if not text: continue
        
        words = [w for w in text.split() if w.isalpha() and len(w) > 1]
        if len(words) < 3: continue # Need at least start, middle and end
        
        total_lines += 1
        
        w_start = words[0]
        w_end = words[-1]
        w_middle = words[1:-1]
        
        total_middle_words += len(w_middle)
        
        # First letters
        start_chars[w_start[0]] += 1
        end_chars[w_end[-1]] += 1
        
        for wm in w_middle:
            middle_chars[wm[0]] += 1
            middle_chars[wm[-1]] += 1 # middle words ending chars
            
            if len(wm) >= 2:
                middle_prefixes[wm[:2]] += 1
                middle_suffixes[wm[-2:]] += 1
                
        if len(w_start) >= 2:
            start_prefixes[w_start[:2]] += 1
        if len(w_end) >= 2:
            end_suffixes[w_end[-2:]] += 1

print(f"Analyzed lines: {total_lines}")
print(f"Analyzed middle words: {total_middle_words}\n")

# Function to find "Edge Bias" (E.g. appears at the beginning of a line much more often than in the middle)
def calculate_bias(edge_counter, middle_counter, edge_total, middle_total, label):
    print(f"## {label} (Top 10 by Disproportion)")
    print("| Symbol / Morpheme | Percentage at Edge | Percentage in Middle | Conclusion (Edge Bias) |")
    print("|---|---|---|---|")
    
    # Checking only those appearing at least 50 times at the edge
    candidates = [item for item, count in edge_counter.items() if count > 50]
    results = []
    
    for item in candidates:
        edge_pct = (edge_counter[item] / edge_total) * 100
        mid_pct = (middle_counter.get(item, 0) / middle_total) * 100
        
        if mid_pct == 0:
            ratio = float('inf')
        else:
            ratio = edge_pct / mid_pct
            
        results.append((item, edge_pct, mid_pct, ratio))
        
    results.sort(key=lambda x: x[3], reverse=True) # Sorting by disproportion
    
    for item, e_pct, m_pct, ratio in results[:10]:
        conclusion = "Strict edge fixation" if ratio > 3 else "Weak bias"
        print(f"| **`{item}`** | {e_pct:.2f}% | {m_pct:.2f}% | {conclusion} ({ratio:.1f}x more frequent) |")

# Calculations
calculate_bias(start_chars, middle_chars, total_lines, total_middle_words, "Line Start Letters (First Character of Line)")

# End letter bias (using total_lines for end words and total_middle_words for middle ones)
end_chars_middle = collections.Counter()
with open(CLEAN_DATA_FILE, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        words = [w for w in row['Clean_Text'].strip().split() if w.isalpha() and len(w) > 1]
        if len(words) >= 3:
            for wm in words[1:-1]:
                end_chars_middle[wm[-1]] += 1

calculate_bias(end_chars, end_chars_middle, total_lines, total_middle_words, "Line End Letters (Last Character of Line)")

calculate_bias(start_prefixes, middle_prefixes, total_lines, total_middle_words, "Line Start Prefixes (Line-Start Prefixes)")
calculate_bias(end_suffixes, middle_suffixes, total_lines, total_middle_words, "Line End Suffixes (Line-End Suffixes)")

print("\n## CONCLUSIONS")
print("1. **Strict Positional Encoding:** If algorithm shows >3x disproportion, it means manuscript author PURPOSELY placed certain symbols only at the beginning or end of line.")
print("2. **Steganography / 'Nulls':** Symbols having no statistical meaning in middle of line, but massively dominating at start (e.g. specific gallows), are likely not phonetic sounds. They are **structural variables** (e.g. paragraph numbering, alchemical operation duration or temperature/fire level indicator).")
