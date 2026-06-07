# ==============================================================================
# VOYNICH MANUSCRIPT: QUIRE-DOMAIN DISTRIBUTION AUDIT (DIAGNOSTIC SCRIPT)
# Target Environment: Google Colab
# ==============================================================================

import pandas as pd
import numpy as np
import re
import os

# Configuration
TARGET_FILE = "voynich_clean_data/RF1b-er_clean.csv"
CLASSES = ["Herbal", "Astronomy", "Balneology", "Recipes"]

def deeply_clean_text(text):
    text = str(text)
    text = re.sub(r'\[.*?\]|<.*?>|<>|\$\w+', '', text)
    text = re.sub(r'[^a-zA-Z\s]', '', text)
    return re.sub(r'\s+', ' ', text).strip().lower()

def get_target_class(folio_str):
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return None
    num = int(match.group(1))
    
    if (1 <= num <= 66) or num == 87: return "Herbal"
    elif (67 <= num <= 73) or (85 <= num <= 86): return "Astronomy"
    elif 75 <= num <= 84: return "Balneology"
    elif 103 <= num <= 116: return "Recipes"
    return None

def get_quire_id(folio_str):
    """
    Historical Beinecke MS 408 quire grouping approximation.
    Uses the same 8-folio boundary logic applied in Phase XXVIII.
    """
    match = re.search(r'f(\d+)', str(folio_str))
    if not match: return "Quire_Unknown"
    num = int(match.group(1))
    quire_num = ((num - 1) // 8) + 1
    return f"Quire_{quire_num}"

def run_distribution_audit():
    print("=== Voynich Diagnostic: Quire vs. Domain Distribution Audit ===\n")
    
    if not os.path.exists(TARGET_FILE):
        print(f"[-] Error: Target file {TARGET_FILE} not found. Please run Phase I parser first.")
        return
        
    df = pd.read_csv(TARGET_FILE)
    df['Deep_Clean_Text'] = df['Clean_Text'].apply(deeply_clean_text)
    df = df[df['Deep_Clean_Text'].str.strip() != '']
    
    # Map each line to its Domain and Quire
    df['Domain'] = df['Folio'].apply(get_target_class)
    df['Quire'] = df['Folio'].apply(get_quire_id)
    
    # Filter only lines that belong to our 4 target classes
    filtered_df = df[df['Domain'].isin(CLASSES)]
    
    total_lines = len(filtered_df)
    unique_quires = filtered_df['Quire'].nunique()
    
    print(f"[*] DATASET PROFILE:")
    print(f"    -> Total Analyzed Lines : {total_lines}")
    print(f"    -> Unique Active Quires  : {unique_quires}\n")
    
    # Generate Contingency Matrix (Cross-tabulation)
    contingency_matrix = pd.crosstab(filtered_df['Quire'], filtered_df['Domain'])
    
    # Ensure all target classes are present in the table columns
    for c in CLASSES:
        if c not in contingency_matrix.columns:
            contingency_matrix[c] = 0
            
    contingency_matrix = contingency_matrix[CLASSES]
    
    print("-" * 85)
    print(f"{'Quire ID':<15} | " + " | ".join([f"{c:<12}" for c in CLASSES]))
    print("-" * 85)
    for quire, row in contingency_matrix.iterrows():
        print(f"{quire:<15} | " + " | ".join([f"{row[c]:<12}" for c in CLASSES]))
    print("-" * 85)
    
    # Deep Statistical Sparsity Analysis
    print("\n[*] DIAGNOSTIC SPARSITY ANALYSIS:")
    print("    Investigating if classes are completely missing in certain quires.")
    
    for c in CLASSES:
        total_class_instances = contingency_matrix[c].sum()
        quires_present = (contingency_matrix[c] > 0).sum()
        quires_missing = unique_quires - quires_present
        concentration_pct = (contingency_matrix[c].max() / total_class_instances) * 100 if total_class_instances > 0 else 0
        
        print(f"\n    -> Domain: [{c.upper()}]")
        print(f"       Total Lines      : {total_class_instances}")
        print(f"       Sparsity Profile : Present in {quires_present}/{unique_quires} quires (Missing in {quires_missing} quires)")
        print(f"       Sparsity Rate    : {(quires_missing / unique_quires) * 100:.1f}% empty quire distribution")
        print(f"       Concentration    : Peak quire contains {concentration_pct:.1f}% of all domain lines")
        
        if quires_present <= 2:
            print("       [!] CRITICAL WARNING: This domain is extremely siloed. Splitting by Quire")
            print("           will inevitably leave folds with ZERO training examples for this class.")
            print("           This fully explains why GroupKFold Macro-F1 collapsed.")

    # Mathematical Evaluation of Fold Stability
    print("\n" + "="*85)
    print("[*] FINAL AUDIT VERDICT:")
    print("="*85)
    critical_silo_detected = False
    for c in CLASSES:
        quires_present = (contingency_matrix[c] > 0).sum()
        if quires_present < 5:  # Less than our 5-fold split
            print(f"    [-] '{c}' is present in only {quires_present} quires. It cannot survive 5-Fold GroupKFold.")
            critical_silo_detected = True
            
    if critical_silo_detected:
        print("\n    [!] REASON FOR F1 COLLAPSE CONFRIMED: 'Class-Quire Imbalance'.")
        print("        Since some classes are only present in fewer than 5 quires, the model")
        print("        mathematically cannot generalize across unseen quires using a 5-Fold split.")
        print("        To fix this, we must either:")
        print("        1) Reduce folds to match minimum quire representation (e.g., Stratified GroupKFold),")
        print("        2) Or focus the evaluation on high-density overlapping domains.")
    else:
        print("    [+] No critical quire siloing detected. The F1 degradation is purely structural.")

if __name__ == "__main__":
    run_distribution_audit()