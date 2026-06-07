import json
import os
import glob

MAPPING_DIR = r"D:\Google Drive diskai\GDrive_VigiBygg\Voynich_Projektas\Tyrimu_kartojimas\Pixel MAPING"
REPORT_FILE = r"C:\Users\user\.gemini\tmp\tyrimu-kartojimas-1\Protokolai ir raportai\Phase_37_Taxon_Tracking_Model.md"

def build_reverse_model():
    json_files = glob.glob(os.path.join(MAPPING_DIR, "*_mapping.json"))
    
    # 1. Collect all [TAXON] from labels (Labels)
    taxons = {} # word -> set of folio IDs where it appears as a label
    
    # 2. Collect all paragraph texts
    paragraphs = [] # list of dicts: {'folio': id, 'locus': locus, 'text': text, 'words': list_of_words}
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            continue
            
        folio_id = data.get("folio", os.path.basename(file_path))
        text_blocks = data.get("text_blocks_mapping", [])
        
        for block in text_blocks:
            for line in block.get("lines", []):
                raw_text = line.get("raw_text", "")
                locus = line.get("locus", "")
                
                clean_text = raw_text.replace("<->", ".").replace("???", "")
                words = [w.strip() for w in clean_text.split('.') if w.strip()]
                
                # Is it a label? (@L, =L, +L, *L)
                if any(x in locus for x in ['@L', '=L', '+L', '*L']):
                    for word in words:
                        if len(word) > 2: # ignore single letters/markers
                            if word not in taxons:
                                taxons[word] = set()
                            taxons[word].add(folio_id)
                
                # Ar tai paragrafas? (@P, +P, *P)
                if any(x in locus for x in ['@P', '+P', '*P']):
                    paragraphs.append({
                        'folio': folio_id,
                        'locus': locus,
                        'raw_text': raw_text,
                        'words': words
                    })
                    
    # 3. Tracking: Search [TAXON] in paragraphs
    tracking_results = []
    
    for taxon, origin_folios in taxons.items():
        found_in_paragraphs = []
        for p in paragraphs:
            # Looking for full match or strong root match (>80%)
            for word in p['words']:
                if taxon == word or (len(taxon) > 3 and taxon in word):
                     found_in_paragraphs.append({
                         'folio': p['folio'],
                         'locus': p['locus'],
                         'matched_word': word
                     })
        
        if found_in_paragraphs:
            tracking_results.append({
                'taxon': taxon,
                'origins': list(origin_folios),
                'matches': found_in_paragraphs
            })

    # 4. Generate report
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write("# Reverse Model: [TAXON] Tracking (Ingredient Tracking)\n\n")
        f.write("This model reads visually isolated labels (e.g., nymph names on folio f75v) and tracks if these words later appear as 'ingredients' in instruction paragraphs.\n\n")
        
        f.write(f"**Identified unique [TAXON] labels (>2 letters):** {len(taxons)}\n")
        f.write(f"**Successfully tracked [TAXON] in paragraphs:** {len(tracking_results)}\n\n")
        
        f.write("## Detailed Tracking Results\n")
        for res in sorted(tracking_results, key=lambda x: len(x['matches']), reverse=True):
            f.write(f"### [TAXON]: `{res['taxon']}`\n")
            f.write(f"* **Source (Label found on pages):** {', '.join(res['origins'])}\n")
            f.write(f"* **Naudojama instrukcijose (Paragrafuose):** {len(res['matches'])} kartus\n")
            
            # Show up to 5 examples
            for m in res['matches'][:5]:
                f.write(f"    * Used in file `{m['folio']}`, locus `{m['locus']}` (as word `{m['matched_word']}`)\n")
            if len(res['matches']) > 5:
                f.write(f"    * ... (ir dar {len(res['matches']) - 5} kartus)\n")
            f.write("\n")

    print(f"Taxon sekimo ataskaita sugeneruota: {REPORT_FILE}")

if __name__ == "__main__":
    build_reverse_model()
