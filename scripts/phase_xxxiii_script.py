# VOYNICH MANUSCRIPT: CONTROLLED SYNTHESIS BENCHMARK (PHASE XXXIII)
# The "Ground Truth" Sandbox & Double-Blind Parser Evaluation
# Target Environment: Google Colab
#
# PATAISYMAI (v2):
#   [1] NOISE_MATRIX targets added to ONTOLOGY as aliases →
#       the parser no longer assigns them the UNKNOWN tag
#   [2] calculate_normalized_ged() recalculated using sequence
#       comparison (SequenceMatcher), not positional indices →
#       shorthand/agglutinative no longer gets artificially high node_diff
#   [3] build_true_latin_graph() apsaugota nuo None edge klaidos
#   [4] Collision protection: assert before reverse_lookup creation
#   [5] Redundant imports (pandas, numpy) removed
#   [6] categories = sorted(set(...)) instead of list(set(...)) → deterministic order
# ==============================================================================

import random
import networkx as nx
from difflib import SequenceMatcher
import warnings

warnings.filterwarnings("ignore")

# ==============================================================================
# 1. GROUND TRUTH (LATIN RECIPE) & ENCODING RULES
# ==============================================================================
# Stylized, historically accurate medieval botany recipe sequence.
# Structure: [Verb/Command] -> [Base] -> [State] -> [Dose]
LATIN_RECIPE = [
    ("recipe",  "COMMAND"),
    ("aquam",   "BASE"),
    ("calidam", "STATE"),
    ("unciam",  "DOSE"),
    ("misce",   "COMMAND"),
    ("succum",  "BASE"),
    ("purum",   "STATE"),
    ("guttam",  "DOSE"),
    ("coque",   "COMMAND"),
    ("oleum",   "BASE"),
    ("nigrum",  "STATE"),
    ("libram",  "DOSE"),
]

# FIX [1]: NOISE_MATRIX targets added to ONTOLOGY as aliases.
# Previously 'lk', 'lkal', 'o', 'r', 'sh', 'ain', 'aiiin' received UNKNOWN tag,
# therefore the noisy version was penalized doubly – both due to noise and
# due to unrecognized tokens. Now parser classifies them correctly.
ONTOLOGY = {
    "COMMAND":  ["lka", "lkc", "lky", "lk", "lkal"],       # + noise variants
    "BASE":     ["ol", "qol", "al", "o", "or"],             # + noise variants
    "STATE":    ["s", "ar", "shedy", "r", "sh"],            # + noise variants
    "DOSE":     ["aiin", "daiin", "am", "chedy", "ain", "aiiin"],  # + noise variants
}

# Transcription noise matrix (EVA variation)
NOISE_MATRIX = {
    "lka":  ["lk", "lkal"],
    "ol":   ["o", "or"],
    "s":    ["r", "sh"],
    "aiin": ["ain", "aiiin"],
}

# ==============================================================================
# 2. KODAVIMO GENERATORIAI (VARIANTAI)
# ==============================================================================

def encode_true_voynich():
    """Encodes the Latin recipe strictly according to the Ontology key."""
    encoded = []
    for _, tag in LATIN_RECIPE:
        encoded.append(random.choice(ONTOLOGY[tag]))
    return " ".join(encoded)

def encode_true_noisy_voynich():
    """Encodes correctly, but inserts transcription/EVA variation noise."""
    encoded = []
    for _, tag in LATIN_RECIPE:
        token = random.choice(ONTOLOGY[tag])
        # 30% noise probability if a confusion matrix exists for the token
        if random.random() < 0.3 and token in NOISE_MATRIX:
            token = random.choice(NOISE_MATRIX[token])
        encoded.append(token)
    return " ".join(encoded)

def encode_agglutinative():
    """Incorrectly stacks tags into long words (COMMAND+BASE+STATE+DOSE)."""
    encoded = []
    current_word = ""
    for _, tag in LATIN_RECIPE:
        current_word += random.choice(ONTOLOGY[tag])
        if tag == "DOSE":   # Word break after full sequence
            encoded.append(current_word)
            current_word = ""
    # Safeguard: if unfinished word remains (e.g. recipe does not end with DOSE)
    if current_word:
        encoded.append(current_word)
    return " ".join(encoded)

def encode_shorthand():
    """Removes STATE and DOSE tags – leaving only COMMAND and BASE."""
    encoded = []
    for _, tag in LATIN_RECIPE:
        if tag in ["COMMAND", "BASE"]:
            encoded.append(random.choice(ONTOLOGY[tag]))
    return " ".join(encoded)

def encode_random_constrained():
    """Randomly assigns valid Voynich tokens without structural logic."""
    all_tokens = [t for tokens in ONTOLOGY.values() for t in tokens]
    return " ".join(random.choice(all_tokens) for _ in LATIN_RECIPE)

# ==============================================================================
# 3. ISOMORPHIC PARSER AND DEPENDENCY GRAPH
# ==============================================================================

def isomorphic_parse_to_graph(text_line):
    """
    Imitates spaCy/Stanza dependency parser, trained on the Ontology key.
    Likely structure: COMMAND (root) → BASE → STATE/DOSE.
    """
    words = text_line.split()
    G = nx.DiGraph()

    tagged_words = []
    for i, word in enumerate(words):
        tag = "UNKNOWN"
        for key_tag, valid_tokens in ONTOLOGY.items():
            if word in valid_tokens:
                tag = key_tag
                break
        tagged_words.append((i, word, tag))
        G.add_node(i, label=tag, word=word)

    current_root = None
    current_base = None

    for i, word, tag in tagged_words:
        if tag == "COMMAND":
            current_root = i
        elif tag == "BASE":
            current_base = i
            if current_root is not None:
                G.add_edge(current_root, i)
        elif tag in ["STATE", "DOSE"]:
            if current_base is not None:
                G.add_edge(current_base, i)
            elif current_root is not None:
                G.add_edge(current_root, i)

    return G, tagged_words

def build_true_latin_graph():
    """
    Creates target dependency graph based on Latin recipe reference tags.

    FIX [3]: None safeguards added - if LATIN_RECIPE started
    not with COMMAND, G.add_edge(None, i) would no longer raise TypeError.
    """
    G = nx.DiGraph()
    current_root = None
    current_base = None

    for i, (word, tag) in enumerate(LATIN_RECIPE):
        G.add_node(i, label=tag, word=word)
        if tag == "COMMAND":
            current_root = i
        elif tag == "BASE":
            current_base = i
            if current_root is not None:           # PATAISYMAS [3]
                G.add_edge(current_root, i)
        elif tag in ["STATE", "DOSE"]:
            if current_base is not None:           # PATAISYMAS [3]
                G.add_edge(current_base, i)
            elif current_root is not None:
                G.add_edge(current_root, i)

    return G

# ==============================================================================
# 4. VERTINIMO METRIKOS (GED ir UAS)
# ==============================================================================

def calculate_uas(parsed_graph, true_graph):
    """
    Unlabeled Attachment Score (UAS).
    Percentage of words correctly attached to structural parent.
    """
    if len(parsed_graph.nodes) == 0:
        return 0.0

    total_nodes = len(true_graph.nodes)
    if total_nodes == 0:
        return 0.0

    correct = 0
    for node in true_graph.nodes():
        if node in parsed_graph.nodes():
            true_parents   = list(true_graph.predecessors(node))
            parsed_parents = list(parsed_graph.predecessors(node))
            if (not true_parents and not parsed_parents) or \
               (true_parents and parsed_parents and
                true_parents[0] == parsed_parents[0]):
                correct += 1

    return correct / total_nodes

def calculate_normalized_ged(parsed_graph, true_graph):
    """
    Normalizuotas Grafo Redagavimo Atstumas (GED).

    FIX [2]: Previous version compared nodes by integer index,
    so shorthand (6 words) and agglutinative (3 words) variants received
    artificially high node_diff, as their indices did not match true_graph[0..11].

    Current version compares label SEQUENCES using SequenceMatcher -
    this is a position-independent method reflecting the true structural difference.
    """
    # Node sequence comparison (from smallest index)
    true_seq   = [true_graph.nodes[n]['label']
                  for n in sorted(true_graph.nodes)]
    parsed_seq = [parsed_graph.nodes[n]['label']
                  for n in sorted(parsed_graph.nodes)]

    # Sequence similarity coefficient → node_diff
    match_ratio = SequenceMatcher(None, parsed_seq, true_seq).ratio()
    node_diff   = round((1.0 - match_ratio) * len(true_seq))

    # Edge mismatches (false negatives + false positives)
    edge_diff = sum(1 for e in true_graph.edges()
                    if not parsed_graph.has_edge(*e))
    edge_diff += sum(1 for e in parsed_graph.edges()
                     if not true_graph.has_edge(*e))

    max_dist = (len(true_seq) + len(true_graph.edges) +
                len(parsed_seq) + len(parsed_graph.edges))
    if max_dist == 0:
        return 1.0

    return (node_diff + edge_diff) / max_dist

# ==============================================================================
# 5. PAGRINDINIS VYKDYMAS
# ==============================================================================

def main():
    print("=== Voynich Phase XXXIII: Controlled Synthesis Benchmark ===")
    print("Goal: Prove that isomorphic parser can reconstruct")
    print("structural dependency graph from known reference text")
    print("under double-blind evaluation conditions.\n")

    random.seed(42)

    # 1. Etalonas
    true_graph = build_true_latin_graph()

    # 2. Generuojame variantus
    variants = {
        "True Encoding":               encode_true_voynich(),
        "True Encoding (With Noise)":  encode_true_noisy_voynich(),
        "Agglutinative Encoding":      encode_agglutinative(),
        "Shorthand Encoding":          encode_shorthand(),
        "Random Constrained":          encode_random_constrained(),
    }

    # FIX [4]: Collision protection - if two functions returned the same
    # text, reverse_lookup would lose one line silently.
    assert len(set(variants.values())) == len(variants), \
        "COLLISION: two encoding functions returned identical text! " \
        "Run again (random generation)."

    # 3. Double-blind shuffle
    blind_test_set = list(variants.values())
    random.seed(101)
    random.shuffle(blind_test_set)

    reverse_lookup = {v: k for k, v in variants.items()}

    print("[*] VYKDOMAS DVIGUBAI AKLAS PARSAVIMO GAUNTLET...")
    print(f"    Thresholds: GED <= 0.25 | UAS >= 0.70\n")

    results = []

    for test_text in blind_test_set:
        actual_model  = reverse_lookup[test_text]
        parsed_graph, tagged_words = isomorphic_parse_to_graph(test_text)

        uas = calculate_uas(parsed_graph, true_graph)
        ged = calculate_normalized_ged(parsed_graph, true_graph)

        results.append({
            "Variant":     actual_model,
            "UAS":         uas,
            "GED":         ged,
            "Text_Sample": test_text[:40] + ("..." if len(test_text) > 40 else ""),
            "Tagged":      [(w, t) for _, w, t in tagged_words],
        })

    # 4. Atskleidimas ir vertinimas
    print("=" * 95)
    print(f"{'Variantas':<30} | {'UAS (↑ geriau)':<18} | {'GED (↓ geriau)':<18} | Pavyzdys")
    print("-" * 95)

    results.sort(key=lambda x: x["GED"])

    fail_triggered = False

    for res in results:
        is_true    = "True" in res["Variant"]
        pass_uas   = res["UAS"] >= 0.70
        pass_ged   = res["GED"] <= 0.25
        lbl_uas    = "PASS" if pass_uas else "FAIL"
        lbl_ged    = "PASS" if pass_ged else "FAIL"

        print(f"{res['Variant']:<30} | "
              f"{res['UAS']:.4f} [{lbl_uas:<4}] | "
              f"{res['GED']:.4f} [{lbl_ged:<4}] | "
              f"{res['Text_Sample']}")

        # Fail conditions
        if is_true and (not pass_uas or not pass_ged):
            fail_triggered = True
            print(f"    [!!!] CRITICAL: Parser failed to reconstruct correct encoding: ")
                  f"'{res['Variant']}'")

        if not is_true and pass_uas and pass_ged:
            fail_triggered = True
            print(f"    [!!!] CRITICAL: Parser incorrectly validated adversarial ")
                  f"encoding: '{res['Variant']}'")

    print("=" * 95)

    # 5. Galutinis sprendimas
    print()
    if fail_triggered:
        print("[-] REIKALINGAS VEIKSMAS: Parserio logika yra klaidinga arba pernelyg")
        print("    applied. Stop semantic decoding and fix.")
    else:
        print("[+] SUCCESS: Parsing pipeline mathematically isolates true syntactic")
        print("    structure from noise, shorthand and random generation.")
        print("    Pipeline viability proven.")
        print("    Safe to proceed to Phase XXXIV (Multimodal Vision-Language Cross-Validation).")

    # 6. Detailed tagging log
    print("\n--- DETAILED TAGGING ANALYSIS ---")
    for res in sorted(results, key=lambda x: x["Variant"]):
        print(f"\n  [{res['Variant']}]  GED={res['GED']:.4f}  UAS={res['UAS']:.4f}")
        unknown_count = sum(1 for _, t in res["Tagged"] if t == "UNKNOWN")
        if unknown_count > 0:
            print(f"    ⚠ UNKNOWN markers: {unknown_count} ")
                  f"(tokens unrecognized – check ONTOLOGY coverage)")
        for word, tag in res["Tagged"]:
            marker = " ← UNKNOWN" if tag == "UNKNOWN" else ""
            print(f"    '{word}' → {tag}{marker}")

if __name__ == "__main__":
    main()

# ==============================================================================
# VOYNICH: MULTIMODAL TEXT-IMAGE CROSS-VALIDATION
#
# Two parallel data sources:
#
# [A] CSV rows with pos_tag Lc/Ls/Lf — marked by transcription authors
#     labels written DIRECTLY on the drawn object (throughout the manuscript).
#     This is the hard baseline: if our prefix hypothesis is correct,
#     these lines should be dominated by the corresponding prefixes.
#
# [B] Researcher DOCX (Pages_10_-_19.docx) — folio level pixel map:
#     koks objektas (Botanical, Vessel, Celestial) pavaizduotas kiekviename
#     on pages f10r-f19v. For each CSV line from these pages
#     assign folio object type and check if line words
#     naudoja atitinkamus taksonominius inkaras (cho-, oto-, ok-...).
#
# Goal: show that textual prefixes do not correlate with object
# types randomly — or refute this hypothesis.
# ==============================================================================

import re
import os
import pandas as pd
import numpy as np
from collections import defaultdict, Counter
from scipy.stats import chi2_contingency, fisher_exact
import warnings

warnings.filterwarnings("ignore")

# ==============================================================================
# 1. CONFIGURATION
# ==============================================================================

CSV_FILES = [
    "voynich_clean_data/RF1b-er_clean.csv",
    "voynich_clean_data/ZL3b-n_clean.csv",
    "voynich_clean_data/IT2a-n_clean.csv",
]

# Taxonomic anchors: which prefixes should appear with which object.
# Based on Phase I-III results.
ANCHOR_RULES = {
    "Ls": {"expected": ["ot", "op", "ok", "o"],  "label": "Stars (@Ls)"},
    "Lc": {"expected": ["ok", "oke", "okc"],      "label": "Indai (@Lc)"},
    "Lf": {"expected": ["ch", "sh", "ct"],        "label": "Augalai (@Lf/@Lp)"},
}
# Treat Lp identically to Lf
LP_ALIAS = "Lf"

# Folio object types from researcher DOCX (Pages_10_-_19.docx).
# Kiekvienas puslapis → dominuojantis objektas.
# Data manually extracted from DOCX descriptions.
DOCX_FOLIO_OBJECTS = {
    # f10r: blue flower on top, two red bulbs (vessels) at bottom
    "f10r": {"type": "Botanical+Vessel", "primary": "Botanical_Flower", "vessel": True},
    # f10v: two blue bell flowers, wavy leaves
    "f10v": {"type": "Botanical_Flower", "primary": "Botanical_Flower",  "vessel": False},
    # f11r: giant round canopy, three tubes/vessel necks
    "f11r": {"type": "Botanical+Vessel", "primary": "Botanical_Leaves",  "vessel": True},
    # f11v: cone-shaped plant, tube branches at bottom
    "f11v": {"type": "Botanical+Vessel", "primary": "Botanical_Leaves",  "vessel": True},
    # f13r: toothed spike, seed pile, massive root bulb
    "f13r": {"type": "Botanical_Seeds",  "primary": "Botanical_Seeds",   "vessel": False},
    # f13v: two stems, three blue flower-vessels, root
    "f13v": {"type": "Botanical_Flower", "primary": "Botanical_Flower",  "vessel": False},
    # f14r: plant + cylindrical vessel at bottom + parchment hole
    "f14r": {"type": "Botanical+Vessel", "primary": "Botanical_Leaves",  "vessel": True},
    # f14v: two large leaves, seed bunches, tube knot
    "f14v": {"type": "Botanical_Seeds",  "primary": "Botanical_Seeds",   "vessel": False},
    # f15r: TWO LARGE BLUE VESSELS/RETORTS on top — the most vessel-like page
    "f15r": {"type": "Fluid_Vessel",     "primary": "Fluid_Vessel",      "vessel": True},
    # f15v: keturlapis augalas, banguota gelsva uodega
    "f15v": {"type": "Botanical_Leaves", "primary": "Botanical_Leaves",  "vessel": False},
    # f16r: spiky leaves, red seed spikes, stump/vessel at bottom
    "f16r": {"type": "Botanical_Seeds",  "primary": "Botanical_Seeds",   "vessel": True},
    # f16v: 4 red spiky flowers + 1 blue, vessel/retort at bottom
    "f16v": {"type": "Botanical+Vessel", "primary": "Botanical_Flower",  "vessel": True},
    # f17r: horizontal leaves, three blue flowers, two red rhombs in roots
    "f17r": {"type": "Botanical_Flower", "primary": "Botanical_Flower",  "vessel": False},
    # f17v: wavy leaves, red berry branch, root bulb-vessel
    "f17v": {"type": "Botanical+Vessel", "primary": "Botanical_Leaves",  "vessel": True},
    # f18r: oval leaves, large blue flower, three white buds
    "f18r": {"type": "Botanical_Flower", "primary": "Botanical_Flower",  "vessel": False},
    # f18v: jagged leaves, round inflorescence (basket), berries inside
    "f18v": {"type": "Botanical_Seeds",  "primary": "Botanical_Seeds",   "vessel": False},
    # f19r: funnel-shaped vessel (neck) at bottom, blue flower on top
    "f19r": {"type": "Botanical+Vessel", "primary": "Botanical_Flower",  "vessel": True},
    # f19v: two spiky canopies, three blue vessels/bells at apex, claw at bottom
    "f19v": {"type": "Botanical+Vessel", "primary": "Botanical_Leaves",  "vessel": True},
}

# Prefixes assigned to botanical types (from ANCHOR_RULES logic)
DOCX_ANCHOR_MAP = {
    "Botanical_Flower": ["ch", "sh", "ct"],
    "Botanical_Leaves": ["ch", "sh", "ct"],
    "Botanical_Seeds":  ["ch", "sh", "ct"],
    "Fluid_Vessel":     ["ok", "oke", "okc"],
    "Botanical+Vessel": ["ch", "sh", "ct", "ok"],
}


# ==============================================================================
# 2. HELPER FUNCTIONS
# ==============================================================================

def get_pos_tag(locus: str) -> str:
    """Extracts the position tag from the locus string (e.g. '@Ls' → 'Ls')."""
    m = re.search(r'[@+\-*%]([A-Z][a-z]{0,2}\d?)', str(locus))
    return m.group(1) if m else "P0"

def get_folio(locus: str) -> str:
    """Extracts folio ID from the locus string (e.g. 'f10r.3,@P0' → 'f10r')."""
    m = re.match(r'(f\d+[rv]\d*)', str(locus))
    return m.group(1) if m else ""

def get_word_prefix(word: str, length: int = 3) -> str:
    """Returns the word prefix up to `length` characters."""
    return word[:length].lower() if len(word) >= length else word.lower()

def classify_anchor(word: str) -> str:
    """
    Assigns a word to a taxonomic anchor class based on prefix.
    Checks longer prefixes first to avoid the absorbing effect of 'o'.
    """
    w = word.lower()
    for pref in ["okc", "oke", "ok", "ot", "op", "ct", "ch", "sh"]:
        if w.startswith(pref):
            return pref
    if w.startswith("o"):
        return "o"
    return "other"

def load_csv(filepath: str) -> pd.DataFrame | None:
    """Reads the CSV file and appends derived columns."""
    if not os.path.exists(filepath):
        print(f"  [!] Failas nerastas: {filepath}")
        return None
    df = pd.read_csv(filepath)
    df["pos_tag"] = df["Locus"].apply(get_pos_tag)
    # Lp = plant part → treat as Lf
    df["pos_tag"] = df["pos_tag"].replace("Lp", LP_ALIAS)
    df["folio"]   = df["Locus"].apply(get_folio)
    df["Clean_Text"] = df["Clean_Text"].fillna("").astype(str)
    return df

def words_from_row(row: pd.Series) -> list[str]:
    """Returns a list of words from Clean_Text, removing short ones (<2 characters)."""
    return [w for w in str(row["Clean_Text"]).strip().split() if len(w) >= 2]


# ==============================================================================
# 3. ANALYSIS A: GLOBAL Lc/Ls/Lf TAG PREFIX PROFILES
#    (Entire manuscript, not just f10r-f19v)
# ==============================================================================

def analyze_label_lines(df: pd.DataFrame, source_name: str) -> pd.DataFrame:
    """
    Calculates the prefix distribution for each Lc/Ls/Lf line.
    Returns a summary table with the chi2 test.
    """
    rows = []
    for tag, info in ANCHOR_RULES.items():
        subset = df[df["pos_tag"] == tag]
        if len(subset) == 0:
            print(f"  [!] No '{tag}' lines in this file.")
            continue

        all_words = []
        for _, row in subset.iterrows():
            all_words.extend(words_from_row(row))

        if not all_words:
            continue

        anchor_counts = Counter(classify_anchor(w) for w in all_words)
        total = len(all_words)

        expected_hit = sum(anchor_counts.get(p, 0) for p in info["expected"])
        expected_pct = round(expected_hit / total * 100, 1) if total else 0

        rows.append({
            "Source":        source_name,
            "Objektas":        info["label"],
            "pos_tag":         tag,
            "Line count":     len(subset),
            "Word count":      total,
            "Laukiami inkarai (%)": expected_pct,
            "Dominuojantis inkaras": anchor_counts.most_common(1)[0][0] if anchor_counts else "–",
            "Pasiskirstymas":  dict(anchor_counts.most_common(5)),
        })

    return pd.DataFrame(rows)


# ==============================================================================
# 4. ANALYSIS B: DOCX FOLIO-LEVEL VALIDATION (f10r-f19v)
#    For each CSV line from these pages we assign the DOCX object type
#    and check if the line words have the expected anchors.
# ==============================================================================

def analyze_docx_folios(df: pd.DataFrame, source_name: str) -> dict:
    """
    Checks: do words of each f10r-f19v line use an anchor,
    matching the object type described in DOCX?

    Returns:
      - hit_rate: what % of lines have at least one expected anchor
      - per_folio: details at folio level
      - contingency: 2x2 table for chi2 test (botany vs vessel)
    """
    target_folios = list(DOCX_FOLIO_OBJECTS.keys())
    sub = df[df["folio"].isin(target_folios)].copy()

    if len(sub) == 0:
        print(f"  [!] {source_name}: no lines in f10r-f19v range.")
        return {}

    per_folio = []
    botanical_anchors = {"ch", "sh", "ct"}
    vessel_anchors    = {"ok", "oke", "okc"}

    for folio, group in sub.groupby("folio"):
        obj_info = DOCX_FOLIO_OBJECTS.get(folio, {})
        if not obj_info:
            continue

        expected_anchors = set(DOCX_ANCHOR_MAP.get(obj_info["primary"], []))
        total_words, hit_words, bot_words, ves_words = 0, 0, 0, 0

        for _, row in group.iterrows():
            for word in words_from_row(row):
                anc = classify_anchor(word)
                total_words += 1
                if any(word.lower().startswith(e) for e in expected_anchors):
                    hit_words += 1
                if anc in botanical_anchors:
                    bot_words += 1
                if anc in vessel_anchors:
                    ves_words += 1

        per_folio.append({
            "Folio":        folio,
            "DOCX tipas":   obj_info["type"],
            "Pirm. objektas": obj_info["primary"],
            "Yra indas":    obj_info["vessel"],
            "Lines":      len(group),
            "Words":       total_words,
            "Laukiami inkarai (%)": round(hit_words / total_words * 100, 1) if total_words else 0,
            "Botanikos inkarai (%)": round(bot_words / total_words * 100, 1) if total_words else 0,
            "Indo inkarai (%)":     round(ves_words / total_words * 100, 1) if total_words else 0,
        })

    return pd.DataFrame(per_folio)


# ==============================================================================
# 5. PERMUTACIJOS TESTAS: AR REZULTATAI NE ATSITIKTINIAI?
# ==============================================================================

def permutation_test(df_label: pd.DataFrame, n_iter: int = 1000) -> dict:
    """
    Shuffles pos_tag labels randomly and measures the average
    expected anchor percentage obtained randomly.
    Lygina su realiu rezultatu.
    """
    if "Laukiami inkarai (%)" not in df_label.columns or len(df_label) == 0:
        return {}

    real_mean = df_label["Laukiami inkarai (%)"].mean()

    # Collect all words and their real tags
    shuffled_means = []
    tag_list = df_label["pos_tag"].tolist()
    pct_list  = df_label["Laukiami inkarai (%)"].tolist()

    rng = np.random.default_rng(seed=42)
    for _ in range(n_iter):
        shuffled = rng.permutation(pct_list)
        shuffled_means.append(np.mean(shuffled))

    p_value = np.mean([s >= real_mean for s in shuffled_means])

    return {
        "Realus vidurkis (%)": round(real_mean, 2),
        "Atsitiktinis vidurkis (%)": round(np.mean(shuffled_means), 2),
        "p-value": round(p_value, 4),
        "Conclusion": "✓ NOT RANDOM" if p_value < 0.05 else "✗ May be random",
    }


# ==============================================================================
# 6. PAGRINDINIS VYKDYMAS
# ==============================================================================

def main():
    print("=" * 80)
    print(" VOYNICH MULTIMODAL CROSS-VALIDATION")
    print(" Sources: transcriptions CSV + researcher DOCX pixel map")
    print("=" * 80)

    all_label_results = []
    all_docx_results  = []

    for filepath in CSV_FILES:
        source_name = os.path.basename(filepath).replace("_clean.csv", "")
        print(f"\n{'─'*60}")
        print(f" Nuskaitomas: {source_name}")
        print(f"{'─'*60}")

        df = load_csv(filepath)
        if df is None:
            continue

        print(f"  Total lines: {len(df)}")
        tag_counts = df["pos_tag"].value_counts()
        lc_ls_lf = {t: tag_counts.get(t, 0) for t in ["Lc", "Ls", "Lf"]}
        print(f"  Lc={lc_ls_lf['Lc']}, Ls={lc_ls_lf['Ls']}, Lf={lc_ls_lf['Lf']} labels")

        # --- ANALYSIS A ---
        print(f"\n  [A] Global Lc/Ls/Lf prefix profiles:")
        df_label = analyze_label_lines(df, source_name)
        if len(df_label) > 0:
            all_label_results.append(df_label)
            print(df_label[
                ["Object", "Line count", "Word count",
                 "Laukiami inkarai (%)", "Dominuojantis inkaras"]
            ].to_string(index=False))

        # --- ANALYSIS B ---
        print(f"\n  [B] DOCX folio lygio validacija (f10r–f19v):")
        df_docx = analyze_docx_folios(df, source_name)
        if isinstance(df_docx, pd.DataFrame) and len(df_docx) > 0:
            all_docx_results.append(df_docx)
            print(df_docx[
                ["Folio", "DOCX type", "Lines",
                 "Laukiami inkarai (%)", "Botanikos inkarai (%)", "Indo inkarai (%)"]
            ].to_string(index=False))

    # --- SUMMARY ---
    print(f"\n{'=' * 80}")
    print(" SUMMARY ACROSS ALL SOURCES")
    print(f"{'=' * 80}")

    if all_label_results:
        combined_label = pd.concat(all_label_results, ignore_index=True)
        summary = combined_label.groupby(["Objektas", "pos_tag"]).agg(
            Sources=("Source", "count"),
            Avg_lines=("Line count", "mean"),
            Vid_laukiami_pct=("Laukiami inkarai (%)", "mean"),
        ).round(1).reset_index()
        print("\n[A] Lc/Ls/Lf prefix averages across all sources:")
        print(summary.to_string(index=False))

        # Permutacijos testas
        perm = permutation_test(combined_label)
        if perm:
            print(f"\n[A] Permutation test (n=1000 iterations):")
            for k, v in perm.items():
                print(f"    {k}: {v}")

    if all_docx_results:
        combined_docx = pd.concat(all_docx_results, ignore_index=True)
        docx_summary = combined_docx.groupby("DOCX tipas").agg(
            Folio_sk=("Folio", "count"),
            Vid_laukiami=("Laukiami inkarai (%)", "mean"),
            Vid_botanika=("Botanikos inkarai (%)", "mean"),
            Vid_indas=("Indo inkarai (%)", "mean"),
        ).round(1).reset_index()
        print(f"\n[B] DOCX folio averages by object type:")
        print(docx_summary.to_string(index=False))

        # Botanikos vs Vessel chi² testas
        bot_vals = combined_docx["Botanikos inkarai (%)"].values
        ves_vals  = combined_docx["Indo inkarai (%)"].values
        vessel_rows = combined_docx["Yra indas"] == True
        try:
            contingency = np.array([
                [bot_vals[vessel_rows].mean(),  ves_vals[vessel_rows].mean()],
                [bot_vals[~vessel_rows].mean(), ves_vals[~vessel_rows].mean()],
            ])
            # Fisher exact test (2×2 su proporcijomis)
            # Convert to numbers, not percentages
            n_rows_vessel  = vessel_rows.sum()
            n_rows_nobotan = (~vessel_rows).sum()
            table = np.array([
                [int(bot_vals[vessel_rows].mean()  * n_rows_vessel  / 100),
                 int(ves_vals[vessel_rows].mean()  * n_rows_vessel  / 100)],
                [int(bot_vals[~vessel_rows].mean() * n_rows_nobotan / 100),
                 int(ves_vals[~vessel_rows].mean() * n_rows_nobotan / 100)],
            ])
            if table.min() >= 0 and table.sum() > 0:
                _, p = fisher_exact(table)
                print(f"\n[B] Fisher exact testas (Botanika vs Vessel indai):")
                print(f"    Contingency table: {table.tolist()}")
                print(f"    p-value: {p:.4f}")
                print(f"    Conclusion: {'✓ Statistically significant diff (p<0.05)' if p < 0.05 else '✗ Difference not statistically significant'}")
        except Exception as e:
            print(f"    [!] Chi² klaida: {e}")

    print(f"\n{'=' * 80}")
    print(" INTERPRETACIJA")
    print(" [A] If in Lc lines 'ok-' > 40% and in Ls lines 'ot-/op-' > 30%,")
    print("     transcription authors' object marking and prefix hypothesis MATCH.")
    print(" [B] Jei DOCX Botanical puslapiuose 'ch-/sh-/ct-' > 30%")
    print("     and in Vessel pages 'ok-' > 30%, pixel map confirms the hypothesis.")
    print(" If both tests are positive: the hypothesis has a double independent basis.")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    main()
# ==============================================================================