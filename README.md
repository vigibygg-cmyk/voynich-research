# Voynich Manuscript Ontological Cipher Replication Study

**Principal Investigator:** Vytautas Giedraitis.  
**Research Period:** 2025–2026.

## About the Project
This repository contains the data, computational scripts, and research protocols for an exhaustive replication study of the Voynich Manuscript (Beinecke MS 408). By statistically analysing over 38,000 words across multiple independent transcriptions, this research mathematically proves that the manuscript is neither a natural language nor a random hoax. 

Instead, the manuscript functions as a **Pasigraphic Instruction Engine**—a constructed, ontological coding system used to document Renaissance-era spagyric (alchemical and botanical) laboratory procedures.

## Key Findings

* **The Pasigraphic Instruction Engine:** The text operates as a deterministic algorithm or "Paper Computer". Sentences are built using a rigid, Lego-like morphology: `[PREFIX / OPERATION] + <ROOT / INGREDIENT> + {SUFFIX / STATE OR DOSE}`. For example, the frequent chain `ol -> s -> aiin` represents `[BASE EXTRACT] -> [STATE MODIFIER] -> [DOSE/QUANTITY]`.
* **Extreme Entropy & Morphological Valency:** The text has an unusually low bigram perplexity (~4.44, similar to Latin) but a massive morphological valency averaging ~84–86. Natural human languages typically exhibit a valency of 6–10, mathematically proving this is a highly combinatorial, artificial taxonomic code.
* **Cross-Cultural Synthesis:** The cipher integrates Arabic astromedicine (e.g., 28 Lunar Mansions mapping to specific roots like *sharatain* and *baldah*), Northern Italian hydraulic engineering (visually and topologically inspired by Francesco di Giorgio Martini), and European botany.
* **Spatial Polymorphism & Edge Bias:** The text layout dynamically interacts with the illustrations. Specific "Gallows" characters (`p`, `t`) appear almost exclusively at the start of lines (functioning as valve indices or structural markers), while dosage terminations (`-am`, `-iin`) show extreme "Edge Bias" at line endings.
* **Currier A and B are Code Versions, Not Dialects:** The shift from Currier A to Currier B represents a technical code update. Version B introduces new procedural operators (e.g., `lk-`, `lc-`) and a new dosage/state suffix (`-dy` replacing `-in`) needed for more complex pharmaceutical processing.
* **The Rosettes Foldout (Macro-Reactor):** The famous 6-page Rosettes foldout (f85/f86) is decoded as a Directed Acyclic Graph representing a continuous spagyric distillation laboratory (an *Athanor*), with text directions matching fluid and vapour flow.

## Data Sources & Acknowledgements
The raw data, manuscript images, and transcriptions used to conduct this research were obtained from the following original sources:

* **Yale University Library (Beinecke Rare Book and Manuscript Library):** High-resolution scans and official catalog metadata of the Cipher manuscript (Beinecke MS 408).
  * Image Archive: [https://collections.library.yale.edu/catalog/2002046?child_oid=1006094](https://collections.library.yale.edu/catalog/2002046?child_oid=1006094)
* **Voynich.nu:** IVTFF transcription files, folio reference layouts, and extensive transliteration work compiled by René Zandbergen, Gabriel Landini, Takeshi Takahashi, Jorge Stolfi, and other contributors.
  * Folios & Transcriptions: [https://www.voynich.nu/folios.html](https://www.voynich.nu/)

## Data & Methodology
To prevent confirmation bias and overfitting ("Tabula Rasa" methodology), all analyses are triangulated across three independent IVTFF transcription baselines:
1. **RF1b-er** (Consensus transcription).
2. **ZL3b-n** (Comprehensive transcription).
3. **IT2a-n** (Basic transcription).

**Methods:** The pipeline utilises Pointwise Mutual Information (PMI) for syntactic chain auto-discovery, Truncated SVD for topological clustering, TF-IDF for blind semantic extraction, and Orthogonal Procrustes vector alignment to cross-reference topologies with 35 historical corpora.

## Repository Structure
* `/voynich_clean_data/` - Cleaned and standardised CSV transcription files (RF1b, ZL3b, IT2a).
* `/historical_corpora/` - 35 historical control texts (Latin Alchemy, German Botany, Old Finnish, etc.) used for baseline comparisons and orthogonal alignment.
* `/Pixel_MAPING/` - JSON mapping files containing exact coordinates and bounding boxes for manuscript illustrations and text bisections.
* `/scripts/` - Python scripts for executing Byte-Pair Encoding (BPE), SVD clustering, entropy calculations, and cross-domain semantic alignment.
* `/reports/` - Detailed research protocols, empirical tests, and scientific findings (Phases I–XXXV+).

## Usage & License
This project is conducted under the principles of open, citizen-science. All data, code, and findings are provided under the **MIT License**. Researchers, cryptographers, and data scientists are encouraged to freely verify, reproduce, challenge, and build upon this ontological framework.
```
