# Disease to Code Mapper (MediCode)

Semantic search engine that maps free-text clinical terms to standardised medical
codes — **ICD-10-CM**, **ICD-10-PCS** and **CPT** — served through a Streamlit UI.

Instead of keyword lookup, descriptions from each code set are embedded with
medical-domain transformer models, stored in FAISS indexes, and queried by cosine
similarity. For ICD-10-CM the results of two models are fused and then re-ranked
using the ICD hierarchy (parents, siblings, grandparents get a proximity boost),
which pulls clinically adjacent codes up the list.

---

## Table of contents

- [Features](#features)
- [How it works](#how-it-works)
- [Project layout](#project-layout)
- [Setup](#setup)
- [Running the app](#running-the-app)
- [Configuration](#configuration)
- [Rebuilding the FAISS indexes](#rebuilding-the-faiss-indexes)
- [Data assets](#data-assets)
- [Known limitations](#known-limitations)
- [Before you push to git](#before-you-push-to-git)

---

## Features

| Page | What it does | Status |
|---|---|---|
| **Dashboard** | Landing page / product overview | Working |
| **Interactive Mapping** | Single-term lookup against ICD-10-CM, ICD-10-PCS or CPT, with confidence scores and an ICD ontology tree visualisation | Working |
| **Batch Processing** | Upload a CSV/XLSX with a `Query` column and map every row in bulk | Working |
| **Clinical NLP** | Entity extraction from unstructured notes | **Mock only** — returns hard-coded results |

## How it works

```
query ──► tokenizer + transformer ──► mean pooling ──► L2 normalise
                                                          │
                                                          ▼
                                        FAISS IndexFlatIP (cosine similarity)
                                                          │
                                                          ▼
                             top-k ids ──► metadata xlsx ──► Code + Description + Score
```

**ICD-10-CM** takes an extra path (`scripts/icd_10_cm_search_bar.py`):

1. The query is searched against **two** indexes — SapBERT (`cambridgeltl/SapBERT-from-PubMedBERT-fulltext`) and MedEmbed (`abhinand/MedEmbed-large-v0.1`).
2. Scores are late-fused: `0.1 × sap + 0.9 × medembed`, plus a `+0.1` bonus for codes both models returned.
3. The top-ranked code becomes the *anchor*. Using the ICD hierarchy graph (`icd_code_hierarchy.pkl`), its parent, siblings, grandparent and cousins get an additive boost (`gamma = 0.3` scaled by relationship distance).
4. Scores are min-max normalised to 0–100 for display.

**ICD-10-PCS** uses `emilyalsentzer/Bio_ClinicalBERT`; **CPT** uses MedEmbed. Both are single-model searches with a `0.35` cosine threshold.

## Project layout

```
.
├── u10.py                      # ← CURRENT Streamlit app (entry point)
├── u9.py, U8.py, app.py,       # earlier UI iterations, kept for reference
│   U_frontend.py
├── config.ini                  # model names + index/metadata paths
├── cognitio_logo.png           # sidebar logo
├── scripts/
│   ├── icd_10_cm_search_bar.py # dual-model late fusion + graph boosting
│   ├── icd_10_pcs_search_bar.py# single-model PCS search
│   ├── cpt_search_bar.py       # single-model CPT search
│   ├── batch_search.py         # generic index/search pipeline + bulk runner
│   └── graph_visualize.py      # ICD hierarchy → networkx → matplotlib
├── index/                      # FAISS indexes + metadata (NOT in git, see below)
├── icd_code_hierarchy.pkl      # pickled ICD tree of ICDcodeNode objects (NOT in git)
├── group_to_chapter_data.xlsx  # 3-char grouper → section → chapter lookup (1,918 rows)
├── ICD_10_CM_Complete_Data.xlsx, icd10cm-order-2025.txt, ...  # source reference data
└── *.ipynb                     # exploratory notebooks (index building, NER, fusion experiments)
```

### Notebooks

These are research scratchpads, not part of the runtime path. They still contain
hard-coded absolute paths from the original author's machine
(`C:\Users\UNegi\Documents\Project\makethon\...`) and will not run as-is.
The useful ones:

- `build_icd_code_hirarchy.ipynb` — builds `icd_code_hierarchy.pkl` from `icd10cm-order-2025.txt`
- `final_v2.ipynb`, `late_fusion.ipynb` — late-fusion scoring experiments
- `medical_ner.ipynb`, `semantic_match_health.ipynb` — NER / embedding experiments
- `genai_vision.ipynb` — Groq vision document extraction (needs `GROQ_API_KEY` in the environment)

## Setup

Requires **Python 3.10–3.12** (FAISS and PyTorch have no 3.13/3.14 wheels yet) and
about **6 GB of free disk** — ~3 GB of packages plus ~2.5 GB of Hugging Face model
weights downloaded on first run.

```bash
python -m venv .venv
```

```bash
.venv\Scripts\activate
```

```bash
pip install -r requirements.txt
```

A CUDA GPU is used automatically if `torch.cuda.is_available()`; otherwise
everything runs on CPU (slower, but fine for interactive queries).

## Running the app

Run from the **project root** — `config.ini` uses paths relative to the working
directory.

```bash
streamlit run u10.py
```

First launch downloads three models (~2.5 GB) and memory-maps ~535 MB of FAISS
indexes, so expect a few minutes before the UI responds. Later launches are fast.

**Batch Processing** expects an uploaded file with a column literally named `Query`.

## Configuration

Everything tunable lives in `config.ini`:

```ini
[ICD-10-CM]
model_name = abhinand/MedEmbed-large-v0.1
faiss_index_path = index/icd10_faiss_medembed.index
excel_metadata = index/icd10_metadata_medembed.xlsx
faiss_index_path_sap = index/icd10_faiss_sapbert_from_pubmedbert.index
excel_metadata_sap = index/icd10_metadata_sapbert_from_pubmedbert.xlsx
graph_pickle = icd_code_hierarchy.pkl
group_to_chapter_data = group_to_chapter_data.xlsx
```

`default_threshold` (in `[DEFAULT]`, currently `0.35`) is the minimum cosine
similarity for a result to be returned by the PCS/CPT/batch paths.

## Rebuilding the FAISS indexes

The indexes are not in version control. To rebuild one from a source spreadsheet
with `Code` and `Description` columns:

```bash
python -c "from scripts.batch_search import index_codes; index_codes('CPT', 'ICD_10_CM_Complete_Data.xlsx')"
```

The case name must match a `config.ini` section (`CPT`, `ICD-10-CM`, `ICD-10-PCS`).
This writes both the `.index` file and the `_metadata.xlsx` sidecar to the paths in
that section. Expect this to take a while — every description is embedded.

## Data assets

| File | Rows | Size |
|---|---|---|
| `index/icd10_metadata_medembed.xlsx` | 74,719 | 2.0 MB |
| `index/icd10_metadata_sapbert_from_pubmedbert.xlsx` | 74,719 | 1.8 MB |
| `index/icd10_metadata_pcs.xlsx` | 80,029 | 1.9 MB |
| `index/cpt_metadata.xlsx` | 18,010 | 0.5 MB |
| `index/icd10_faiss_medembed.index` | — | 306 MB |
| `index/icd10_faiss_pcs.index` | — | 246 MB |
| `index/icd10_faiss_sapbert_from_pubmedbert.index` | — | 230 MB |
| `index/cpt_faiss.index` | — | 73 MB |
| `icd10_faiss.index` (root) | — | 230 MB, an older stray index; not referenced by `config.ini` |
| `index/icd10_faiss_biolord.index` + metadata | — | 230 MB, BioLORD experiment; not referenced by `config.ini` |

ICD-10-CM/PCS source data is public CMS reference data. CPT codes are AMA
copyrighted — check your licence before redistributing `cpt_metadata.xlsx`.

## Known limitations

- **Clinical NLP page is a mock.** `show_nlp()` sleeps 1.5 s and renders two
  hard-coded codes. It is not wired to any model.
- **CPT results contain duplicates.** `index/cpt_metadata.xlsx` has 2,155 exactly
  repeated `Code` + `Description` rows out of 18,010, so a CPT search happily returns
  the same code three times in a row (e.g. `71046 X-ray exam chest 2 views`). Dedupe the
  source before re-indexing, or drop duplicates on `code` in `cpt_search_bar()`.
  The ICD-10-CM and ICD-10-PCS metadata files are clean.
- **`icd_code_hierarchy.pkl` unpickles into `__main__`.** It was created in a notebook,
  so `pickle.load()` looks for `__main__.ICDcodeNode`. That is the *only* reason
  `u10.py` line 9 imports `ICDcodeNode` — do not remove that import as "unused", and any
  new entry point must import it too or the ontology tree dies with an `AttributeError`.
- **Import-time loading.** `scripts/icd_10_cm_search_bar.py` loads two models and
  two FAISS indexes at module import, so the first Streamlit run is slow and holds
  several GB of RAM. `late_fusion_with_graph_proximity()` also re-reads and rebuilds
  the 11 MB hierarchy pickle on *every* query — the obvious first optimisation.
- **`ensure_index_and_metadata()` returns the string `"No Index Found"`** when files
  are missing, which then fails with an unpacking `ValueError` in
  `batch_search_function()` rather than a clear message.
- **Unpickling `icd_code_hierarchy.pkl` executes code.** Only load the file you
  generated yourself.
- **Five UI variants** (`u10.py`, `u9.py`, `U8.py`, `app.py`, `U_frontend.py`) still
  live in the repo. `u10.py` is current; the rest are dead weight.
- `requirement.txt` (singular) is the old, incomplete dependency list — superseded by
  `requirements.txt`.

## Before you push to git

Read `MEMORY.md` for the full audit. Short version:

1. A Hugging Face token that was committed in `semantic_match_health.ipynb` has been
   **removed from the working tree — revoke it at https://huggingface.co/settings/tokens.**
2. `.gitignore` excludes `*.index`, `*.pkl`, `.venv/` and `__pycache__/`. Without it
   the push fails: GitHub rejects any file over 100 MB.
3. Nothing else in the repo contains credentials or patient data — the only clinical
   content is public code-set reference data.

## Disclaimer

Decision-support tooling for trained coders. Output is a ranked suggestion list, not
a validated coding decision, and must be reviewed by a qualified human before use in
billing or clinical documentation.
