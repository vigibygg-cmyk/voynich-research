# ==============================================================================
# VOYNICH MANUSCRIPT: DATA EXTRACTION AND STANDARDIZATION SCRIPT (PHASE I)
# Target Environment: Google Colab
# ==============================================================================

import urllib.request
import urllib.error
import pandas as pd
import re
import os

# Define the target IVTFF transcription files
# We check both standard data and beta directories as versions frequently update
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
    Cleans IVTFF text based on standard EVA rules.
    - Removes inline transcriber comments enclosed in {}
    - Replaces dots (.) and commas (,) with standard spaces (word breaks)
    - Removes dashes (-), equals (=), asterisks (*), percent signs (%), and pipes (|) 
      which mark uncertainties, line breaks, unreadable characters, or paragraph markers
    - Condenses multiple spaces
    """
    # Remove inline comments (e.g., {plant}, {image})
    text = re.sub(r'\{[^}]+\}', '', raw_text)
    
    # Replace dots and commas with spaces (EVA standard for word boundaries)
    text = re.sub(r'[\.,]', ' ', text)
    
    # Remove dashes, equals, asterisks, percent signs, and pipe symbols
    text = re.sub(r'[\-\=\*\!\%\|]', '', text)
    
    # Condense multiple spaces into a single space and strip edges
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

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
            # Group 1 matches the locus (e.g., f1r.P.1;H)
            # Group 2 matches the actual text
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