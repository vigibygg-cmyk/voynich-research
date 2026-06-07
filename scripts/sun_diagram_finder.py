import os

DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\voynich_clean_data - OLD neliesti"
FILE_ZL = os.path.join(DIR, "ZL3b-n_clean.csv")

# Searching for folios around the foldout
TARGET_FOLIOS = ["f68r1", "f68r2", "f68r3", "f68v1", "f68v2", "f68v3", "f69r", "f69v", "f70r1", "f70r2", "f70v1", "f70v2"]

with open(FILE_ZL, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

output_path = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Skriptai\sun_diagram_search.txt"
with open(output_path, "w", encoding='utf-8') as out:
    for folio in TARGET_FOLIOS:
        folio_lines = [l for l in lines if len(l.split(',')) > 2 and l.split(',')[1] == folio]
        if not folio_lines: continue
        
        # Pabandome analizuoti eilutes. 
        # If we find 4 very long lines (rings) and ~8 short ones (rays), it is likely our target.
        long_lines = 0
        short_lines = 0
        
        out.write(f"\n========== {folio} ==========\n")
        out.write(f"Total lines: {len(folio_lines)}\n")
        
        for l in folio_lines:
            parts = l.strip().split(',')
            locus = parts[2].strip('"')
            text = parts[-1]
            words = text.split(' ')
            if len(words) > 15:
                long_lines += 1
                out.write(f"LONG ({len(words)} words) | {locus} | {text[:50]}...\n")
            elif len(words) <= 4 and len(words) > 0:
                short_lines += 1
                out.write(f"SHORT ({len(words)} words) | {locus} | {text}\n")
            else:
                out.write(f"MED ({len(words)} words) | {locus} | {text[:50]}...\n")
                
        out.write(f"Summary for {folio}: {long_lines} long, {short_lines} short.\n")

print(f"Searching for structures. Saved to: {output_path}")
