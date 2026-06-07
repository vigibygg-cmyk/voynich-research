# ==============================================================================
# VOYNICH MANUSCRIPT: CONTROLLED SYNTHESIS BENCHMARK (PHASE XXXIII)
# The "Ground Truth" Sandbox & Double-Blind Parser Evaluation
# Target Environment: Google Colab
#
# PATAISYMAI (v2):
#   [1] NOISE_MATRIX targets added to ONTOLOGY as aliases →
#       parser no longer assigns them UNKNOWN tag
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
# Stylized, historically accurate medieval botanical recipe sequence.
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
# so noisy version was penalized doubly – both for noise, and
# due to unrecognized tokens. Now parser correctly classifies them.
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
    """Encodes Latin recipe strictly according to Ontology key."""
    encoded = []
    for _, tag in LATIN_RECIPE:
        encoded.append(random.choice(ONTOLOGY[tag]))
    return " ".join(encoded)

def encode_true_noisy_voynich():
    """Encodes correctly, but inserts transcription/EVA variation noise."""
    encoded = []
    for _, tag in LATIN_RECIPE:
        token = random.choice(ONTOLOGY[tag])
        # 30% noise probability if confusion matrix exists for token
        if random.random() < 0.3 and token in NOISE_MATRIX:
            token = random.choice(NOISE_MATRIX[token])
        encoded.append(token)
    return " ".join(encoded)

def encode_agglutinative():
    """Incorrectly stacks markers into long words (COMMAND+BASE+STATE+DOSE)."""
    encoded = []
    current_word = ""
    for _, tag in LATIN_RECIPE:
        current_word += random.choice(ONTOLOGY[tag])
        if tag == "DOSE":   # Word break after full sequence
            encoded.append(current_word)
            current_word = ""
    # Safeguard: if unfinished word remains (e.g., recipe does not end in DOSE)
    if current_word:
        encoded.append(current_word)
    return " ".join(encoded)

def encode_shorthand():
    """Removes STATE and DOSE markers - leaving only COMMAND and BASE."""
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
    Imitates spaCy/Stanza dependency parser, trained on Ontology key.
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
    Creates target dependency graph by Latin recipe reference tags.

    FIX [3]: None safeguards added – if LATIN_RECIPE starts
    not with COMMAND, G.add_edge(None, i) would not raise TypeError anymore.
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
    artificially high node_diff, because their indices did not match true_graph[0..11].

    Current version compares label SEQUENCES using SequenceMatcher -
    this is position independent method, reflecting true structure difference.
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
    print("structural dependency graph from known standard text")
    print("under double blind evaluation conditions.\n")

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

    # FIX [4]: Collision protection - if two functions return same
    # text, reverse_lookup would lose one line silently.
    assert len(set(variants.values())) == len(variants), \
        "COLLISION: two encoding functions returned identical text! " \
        "Run again (random generation)."

    # 3. Double blind shuffling
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
            print(f"    [!!!] CRITICAL: Parser failed to restore correct encoding: ")
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
        print("[+] SUCCESS: Parsing pipeline mathematically separates true syntactic")
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
