import os
import sys

# Windows UTF-8 fix
sys.stdout.reconfigure(encoding='utf-8')

# Phase 90: Global Language Falsification Test (False Semantics Competition)
# Goal: Compare purified Voynich Zodiac roots with transliterated words from many world languages.
# We will use a simplified Levenshtein distance algorithm (or similarity coefficient).

# Cleaned Voynich roots from Zodiac pages (without ot-, ok-, o- prefixes)
voynich_roots = [
    "eos", "arar", "ldam", "eoaldy", "eolar", "eoaly", "aleky", "alsar", 
    "cheary", "eokey", "sary", "alaly", "olchdy", "oloaram", "eeol", "olchd",
    "shodady", "chdaiirdainy", "aiinarary", "kalam", "ytalshdy", "char", "alif", 
    "araldy", "aiin", "ain", "alef", "ys", "ainam", "chol", "sharam", 
    "faralar", "choshy", "chdal", "keey", "ary", "ainy"
]

# Dictionaries (Transliterated to Latin characters)

lexicons = {
    "Arabic_Lunar_Mansions": [
        "sharatain", "butain", "thurayya", "dabaran", "haqaa", "hanaa", "dhira", "nathrah", "tarf", 
        "jabhah", "zubrah", "sarfah", "awwa", "simak", "ghafar", "zubanan", "iklil", "qalb", "shaula", 
        "naam", "baldah", "dhabih", "bula", "suud", "akhbiya", "muqaddam", "muakkhar", "risha"
    ],
    "Old_High_German_Months": [
        "lenz", "ostar", "wunne", "brach", "heuw", "arn", "herb", "wein", "winter", "wolf", "horn", "hornung"
    ],
    "Latin_Months_Zodiac": [
        "martius", "aprilis", "maius", "iunius", "iulius", "augustus", "september", "october", "november", "december", "ianuarius", "februarius",
        "aries", "taurus", "gemini", "cancer", "leo", "virgo", "libra", "scorpius", "sagittarius", "capricornus", "aquarius", "pisces"
    ],
    "Baltic_Samogitian_Mythology_Nature": [
        # Baltic deities and nature terms, old months
        "ragutis", "zemepatis", "gegutis", "saule", "menulis", "zvaigzde", "ugnis", "vanduo", "vejas", "zeme",
        "sausis", "vasaris", "kovas", "balandis", "geguzis", "birzelis", "liepa", "rugpjutis", "rugsejis", "spalis", "lapkritis", "gruodis",
        "siekis", "ragas", "ziedas", "laukas", "sula", "paukstis", "medis"
    ],
    "Hittite_Nature": [
        # Hittite nature/world terms
        "šuppi", "watar", "pahhur", "tekan", "nepis", "haster", "harki", "danku", "misri", "kard", "ais", "pata"
    ],
    "Chinese_Pinyin_Zodiac_Lunar": [
        # Chinese zodiac, lunar terms (pinyin)
        "shu", "niu", "hu", "tu", "long", "she", "ma", "yang", "hou", "ji", "gou", "zhu",
        "zi", "chou", "yin", "mao", "chen", "si", "wu", "wei", "shen", "you", "xu", "hai",
        "yue", "ri", "xing", "tian", "di", "shui", "huo", "mu", "jin", "tu"
    ],
    "Japanese_Romaji_Nature_Calendar": [
        # Japanese calendar, nature
        "mutsuki", "kisaragi", "yayoi", "uzuki", "satsuki", "minazuki", "fumizuki", "hazuki", "nagatsuki", "kannazuki", "shimotsuki", "shiwasu",
        "tsuki", "hi", "hoshi", "mizu", "hi", "ki", "kane", "tsuchi", "sora"
    ],
    "Sanskrit_Hindi_Nakshatra": [
        # Indian Lunar Mansions (Nakshatras)
        "ashvini", "bharani", "krittika", "rohini", "mrigashirsha", "ardra", "punarvasu", "pushya", "ashlesha", 
        "magha", "purva_phalguni", "uttara_phalguni", "hasta", "chitra", "svati", "vishakha", "anuradha", "jyeshtha", 
        "mula", "purva_ashadha", "uttara_ashadha", "shravana", "dhanishta", "shatabhisha", "purva_bhadrapada", "uttara_bhadrapada", "revati"
    ],
    "Egyptian_Hieroglyph_Transliteration": [
        # Egyptian months / sky terms
        "thoth", "phaophi", "athyr", "choiak", "tybi", "mechir", "phamenoth", "pharmuthi", "pachons", "payni", "epiphi", "mesore",
        "ra", "yah", "seba", "pet", "ta", "mu", "khet"
    ]
}

def string_similarity(s1, s2):
    """
    Simple similarity coefficient (Sørensen–Dice coefficient on bigrams for morphological similarity).
    Suitable for comparing distorted roots with historical words.
    """
    if len(s1) < 2 or len(s2) < 2:
        return 1.0 if s1 == s2 else 0.0
        
    b1 = set([s1[i:i+2] for i in range(len(s1)-1)])
    b2 = set([s2[i:i+2] for i in range(len(s2)-1)])
    
    if not b1 or not b2: return 0.0
    return 2.0 * len(b1.intersection(b2)) / (len(b1) + len(b2))

print("# Phase 90: Global Language Falsification Test")
print("Cycle through all Voynich Zodiac roots list (37 roots) compared to 9 different world languages / systems dictionaries.\n")

results_summary = {name: {"total_score": 0, "matches_over_40": 0, "matches_over_60": 0, "best_matches": []} for name in lexicons.keys()}

for v_root in voynich_roots:
    if len(v_root) < 3: continue # Ignore roots too short
    
    for lang_name, lexicon in lexicons.items():
        best_score = 0
        best_word = ""
        
        for l_word in lexicon:
            score = string_similarity(v_root, l_word)
            if score > best_score:
                best_score = score
                best_word = l_word
                
        results_summary[lang_name]["total_score"] += best_score
        
        if best_score >= 0.4:
            results_summary[lang_name]["matches_over_40"] += 1
        if best_score >= 0.6:
            results_summary[lang_name]["matches_over_60"] += 1
            # Saving only very strong matches to avoid cluttering the report
            results_summary[lang_name]["best_matches"].append((v_root, best_word, best_score))

print("## Rating by Strong Matches (Similarity >= 40% and >= 60%)")
print("| Vieta | Kalba / Sistema | Atitikmenys (>40%) | Atitikmenys (>60%) | Vidutinis Score |")
print("|---|---|---|---|---|")

# Rikiuojame pagal "matches_over_40"
ranked = sorted(results_summary.items(), key=lambda item: (item[1]["matches_over_40"], item[1]["total_score"]), reverse=True)

rank = 1
for lang_name, data in ranked:
    avg_score = data["total_score"] / len([r for r in voynich_roots if len(r)>=3])
    print(f"| {rank} | **{lang_name.replace('_', ' ')}** | {data['matches_over_40']} | {data['matches_over_60']} | {avg_score:.3f} |")
    rank += 1

print("\n## Overview of Strongest Matches (>60%) in Top 3 Languages")
for lang_name, data in ranked[:3]:
    print(f"\n### {lang_name.replace('_', ' ')}")
    if not data["best_matches"]:
        print("- *No matches exceeding 60% threshold.*")
    for v_root, l_word, score in sorted(data["best_matches"], key=lambda x: x[2], reverse=True):
        print(f"- Voynich `(ot-){v_root}` ~ **{l_word}** ({score*100:.1f}%)")

print("\n## CONCLUSIONS (Falsification)")
print("1. The more languages and systems we include, the clearer we see 'Noise Floor' - what percentage of matches can be obtained randomly because Latin letters and bigrams repeat in all languages.")
print("2. Looking at leaders: did Arabic Lunar Mansions withstand Baltic, Indian, Chinese and Egyptian languages pressure, or were they pushed to end of list?")
print("3. Attention to strong matches (>60%). If any language generates many >60% matches without overfitting, it becomes main linguistic candidate.")
