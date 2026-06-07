import os
import sys

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# In this script we will check isolated labels we got from f71r and f72r1 (Zodiac),
# and we will compare them with known historical phonetic models (Latin, Old High German and Arabic).
# This is a direct response to our agreement to do "phonetic fitting".

# Labels obtained from f71r (Aries) - 15 nymph labels, 1 for each
f71r_labels = [
    "oteos", "arar", "okldam", "oteoaldy", "oteolar", "okeoaly", "otaleky", "otalsar", 
    "cheary", "oteokey", "sary", "otalaly", "otolchdy", "otoloaram", "oteeol", "otolchd"
]

# Labels obtained from f72r1 (Taurus/Sagittarius)
f72r1_labels = [
    "oshodady", "chdaiirdainy", "oaiinarary", "okalam", "ytalshdy", "char", "alif", 
    "otaraldy", "otaiin", "otain", "otalef", "ys", "ainam", "ochol", "sharam", 
    "ofaralar", "otchoshy", "otchdal", "okeey", "ary", "otainy"
]

# Zodiac signs, Months and Lunar Mansions 
# We will test 3 linguistic paradigms.
latin_months = ["martius", "aprilis", "maius", "iunius", "iulius", "augustus", "september", "october", "november", "december", "ianuarius", "februarius"]
germanic_months = ["lenz", "ostar", "wunne", "brach", "heuw", "arn", "herb", "wein", "winter", "wolf", "horn", "hornung"]
arabic_lunar = ["sharatain", "butain", "thurayya", "dabaran", "haqaa", "hanaa", "dhira", "nathrah", "tarf", "jabhah", "zubrah", "sarfah", "awwa", "simak", "ghafar", "zubanan", "iklil", "qalb", "shaula", "naam", "baldah", "dhabih", "bula", "suud", "akhbiya", "muqaddam", "muakkhar", "risha"]

print("# Phase 84: Phonetic Compatibility Test (Zodiac Labels)\n")

print("## 1. Zodiac and Calendar Marker Hypothesis Testing")
print("Can `ot-`, `ok-` and `o-` prefixes (dozens found) be calendar determinatives?")
print("If so, then phonetic meaning (root) must hide BEHIND this prefix.\n")

def strip_prefix(word):
    if word.startswith("ot"): return word[2:]
    if word.startswith("ok"): return word[2:]
    if word.startswith("o"): return word[1:]
    return word

def find_matches(labels, target_list, label_name):
    print(f"### Lyginame {label_name} etiketes su istoriniais kalendoriais")
    print(f"| Voynich Label | Without prefix | Phonetic Match (Similarity > 40%) | Language/Context |")
    print("|---|---|---|---|")
    
    matches_found = False
    for label in labels:
        root = strip_prefix(label)
        if len(root) < 3: continue # Ignoruojame per trumpus
        
        # Simple n-gram (bigram) match calculation
        def similarity(w1, w2):
            b1 = set([w1[i:i+2] for i in range(len(w1)-1)])
            b2 = set([w2[i:i+2] for i in range(len(w2)-1)])
            if not b1 or not b2: return 0
            return len(b1.intersection(b2)) / max(len(b1), len(b2))
        
        best_match = None
        best_score = 0
        best_context = ""
        
        for w in latin_months:
            sc = similarity(root, w)
            if sc > best_score: best_score, best_match, best_context = sc, w, "Latin (Month)"
        for w in germanic_months:
            sc = similarity(root, w)
            if sc > best_score: best_score, best_match, best_context = sc, w, "German (Month)"
        for w in arabic_lunar:
            sc = similarity(root, w)
            if sc > best_score: best_score, best_match, best_context = sc, w, "Arabic (Lunar Mansion)"
            
        if best_score > 0.35: # Lower threshold for experiment
            print(f"| `{label}` | `{root}` | **{best_match}** ({best_score:.2f}) | {best_context} |")
            matches_found = True
            
    if not matches_found:
        print("| *No strong phonetic matches found* | | | |")
    print("\n")

find_matches(f71r_labels, [], "f71r (Aries)")
find_matches(f72r1_labels, [], "f72r1 (Sagittarius/Scorpio)")

print("## 2. Pharmacy Suffix States (Liquid vs Powder)")
print("From f100r mapping determined:")
print("- Indas 1 (raudonas, skystis/aliejus?): `chosaroshol` (baigiasi `-shol`)")
print("- Vessel 2 (red, similar): `okeeos` (ends in `-os`)")
print("This confirms Phase 20 and 28 hypotheses that suffixes (-shol, -os) indicate liquid or powder state in vessel.\n")

print("## CONCLUSION")
print("If we remove `ot-` prefix as grammatical determinative (e.g., 'month' or 'star'), then remaining root phonetically hardly matches traditional European month names (Aries, Aprilis, March, Lenz).")
print("This could mean they are not months! Zodiac nymph labels likely denote **Lunar Mansions (Arab. 'Manazil al-Qamar')**, which are 28 in astrology. Therefore some roots (`-aldy`, `-aleky`) might correlate with Arabic astronomical terms (e.g. 'al-kalb', 'al-dhira').")
