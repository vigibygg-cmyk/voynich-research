# VOYNICH MANUSCRIPT: ADVANCED DATA EXTRACTION AND STANDARDIZATION (PHASE I)
# Improved: Fixed silent bracket truncation [a:b] and brace ligature {abc} bugs.
# Target Environment: Google Colab
# ==============================================================================

import urllib.request
import urllib.error
import pandas as pd
import re
import os

# Define the target IVTFF transcription files
BASE_URLS = [
    "http://www.voynich.nu/data/",
]

TARGET_FILES = [
    "RF1b-er.txt",
    "ZL3b-n.txt",
    "IT2a-n.txt"
]

OUTPUT_DIR = "voynich_clean_data"

def download_file(filename):
    """Attempts to download the specified file from the voynich.nu servers."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    local_path = os.path.join(OUTPUT_DIR, filename)
    
    # If already downloaded, skip
    if os.path.exists(local_path):
        print(f"[*] {filename} already exists locally. Skipping download.")
        return local_path
        
    for base_url in BASE_URLS:
        url = base_url + filename
        try:
            print(f"[*] Attempting to download {filename} from {url}...")
            urllib.request.urlretrieve(url, local_path)
            print(f"[+] Successfully downloaded {filename}")
            return local_path
        except urllib.error.HTTPError:
            continue # Try next base URL
            
    print(f"[-] Failed to download {filename}. Please upload it manually to the '{OUTPUT_DIR}' directory.")
    return None

def clean_voynich_text(raw_text):
    """
    Advanced, linguistically rigorous cleaning for IVTFF/EVA text.
    - Resolves alternative readings in brackets [a:b] by taking the first alternative 'a'.
    - Preserves alphabetic characters inside curly braces {cthh} while stripping
      non-alphabetic comments like {*plant} or {!unreadable}.
    - Replaces dots (.) and commas (,) with spaces (standard EVA word boundaries).
    - Strips out formatting and metadata tags like <%> or <@254;> or any <...>.
    - Filters out any words containing unreadable markers ('?', '*') to prevent word corruption.
    - Removes residual non-alphabetic noise and standardizes spacing.
    """
    # Step 1: Remove formatting tags in angle brackets first (e.g., <@254;>, <%> or empty <>)
    text = re.sub(r'<[^>]*>', '', raw_text)
    
    # Step 2: Resolve alternative readings in square brackets [alternative1:alternative2]
    # We take the first alternative before the colon ':'.
    # Example: [cth:oto]res -> cthres
    def resolve_brackets(match):
        content = match.group(1)
        if ':' in content:
            return content.split(':')[0]
        return content
    
    while '[' in text and ']' in text:
        text = re.sub(r'\[([^\]]*)\]', resolve_brackets, text)
        
    # Step 3: Handle curly braces {abc}
    # Keep alphabetical ligatures like {cthh} but discard comments containing symbols or spaces
    def resolve_braces(match):
        content = match.group(1)
        if re.search(r'[^a-zA-Z]', content):
            return ""
        return content
    
    while '{' in text and '}' in text:
        text = re.sub(r'\{([^}]+)\}', resolve_braces, text)
        
    # Step 4: Replace dots and commas with spaces (EVA standard for word boundaries)
    text = re.sub(r'[\.,]', ' ', text)
    
    # Step 5: Remove standard IVTFF special formatting symbols
    text = re.sub(r'[\-\=\!\%\|]', '', text)
    
    # Step 6: Filter out words containing unreadable markers ('?', '*') to prevent feeding corrupted fragments
    words = text.split()
    cleaned_words = []
    for w in words:
        if '?' in w or '*' in w:
            continue
        # Remove any non-alphabetic residue from the word
        w_cleaned = re.sub(r'[^a-zA-Z]', '', w)
        if len(w_cleaned) >= 1:
            cleaned_words.append(w_cleaned.lower())
            
    return " ".join(cleaned_words).strip()

def parse_ivtff(filepath, source_name):
    """
    Parses an IVTFF format file, extracting loci and cleaning the text.
    Returns a Pandas DataFrame.
    """
    data = []
    
    with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
                
            # Regex to match IVTFF locus tags: <f1r.P.1;H> or <f1r.P.1>
            match = re.match(r'^<([^>]+)>\s+(.*)$', line)
            
            if match:
                full_locus = match.group(1)
                raw_text = match.group(2)
                
                # Split locus into Folio and specific line/paragraph
                locus_parts = full_locus.split('.')
                folio = locus_parts[0] if len(locus_parts) > 0 else "Unknown"
                
                clean_txt = clean_voynich_text(raw_text)
                
                # Only append if there is actual text left after cleaning
                if clean_txt:
                    data.append({
                        "Source": source_name,
                        "Folio": folio,
                        "Locus": full_locus,
                        "Raw_Text": raw_text,
                        "Clean_Text": clean_txt
                    })
                    
    df = pd.DataFrame(data)
    return df

def main():
    print("=== Voynich Manuscript Data Extraction Pipeline ===\n")
    
    all_dataframes = []
    
    for filename in TARGET_FILES:
        local_path = download_file(filename)
        
        if local_path:
            print(f"[*] Parsing {filename}...")
            df = parse_ivtff(local_path, filename.replace('.txt', ''))
            
            # Save individual clean CSV
            csv_filename = os.path.join(OUTPUT_DIR, filename.replace('.txt', '_clean.csv'))
            df.to_csv(csv_filename, index=False)
            
            print(f"[+] Extracted {len(df)} valid lines.")
            print(f"[+] Saved clean data to {csv_filename}\n")
            
            all_dataframes.append(df)
            
    if all_dataframes:
        # Create a combined dataset for cross-reference
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        combined_csv = os.path.join(OUTPUT_DIR, "voynich_combined_clean.csv")
        combined_df.to_csv(combined_csv, index=False)
        print("=====================================================")
        print(f"[+] SUCCESS: All files processed. Combined dataset saved to {combined_csv}")
        print(f"[i] Total lines across all sources: {len(combined_df)}")
        print("=====================================================")

if __name__ == "__main__":
    main()
# ==============================================================================