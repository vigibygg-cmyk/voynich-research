import re
import os

# -------------------------------------------------------------------------
# Phase 115b: Picatrix Lunar Mansions Extractor
# -------------------------------------------------------------------------

def extract_picatrix_mansions(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return
        
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        lines = f.readlines()
        
    mansions = []
    current_mansion = None
    current_text = []
    
    # Regex to catch the mansion titles
    mansion_pattern = re.compile(r'(\d+)\.\s+THE\s+HOUSE\s+OF', re.IGNORECASE)
    
    # We know the mansions section is roughly between lines 750 and 1200
    for line in lines[700:1200]:
        if mansion_pattern.search(line):
            if current_mansion:
                mansions.append({'title': current_mansion, 'text': " ".join(current_text)})
            current_mansion = line.strip().replace('^', '').replace('*', '').replace('§', '').replace('{', '').replace('}', '').replace('•', '').replace('$', '').replace('■', '')
            current_text = []
        elif current_mansion:
            # Collect text until the next mansion
            if line.strip():
                current_text.append(line.strip())
                
    if current_mansion:
        mansions.append({'title': current_mansion, 'text': " ".join(current_text)})
        
    print("--- PICATRIX LUNAR MANSIONS ---")
    print(f"Extracted {len(mansions)} Mansions.\n")
    
    out_lines = ["# Picatrix 28 Lunar Mansions: Talisman Recipes\n"]
    for i, m in enumerate(mansions):
        out_lines.append(f"## {m['title']}")
        out_lines.append(m['text'])
        out_lines.append("\n---\n")
        if i < 3: # Print first 3 as a sample
            print(f"[{m['title']}]\n{m['text'][:200]}...\n")
            
    out_path = 'Kiti_Rezultatai_per_nauja/Phase_115b_Picatrix_Mansions.md'
    with open(out_path, 'w', encoding='utf-8') as out_f:
        out_f.write("\n".join(out_lines))
        
    print(f"\nFull extracted list saved to: {out_path}")

if __name__ == "__main__":
    file_path = 'priedai/PicatrixGhayatAlHakim_djvu.txt'
    extract_picatrix_mansions(file_path)
