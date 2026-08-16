# MEMORY.md — project context & working notes

Durable context for anyone (human or AI assistant) picking this repo up. Facts that
are *not* obvious from reading the code.

Last updated: 2026-08-16

---

## 1. What this project is

A makethon/hackathon build of a **Disease to Code Mapper**: free-text clinical terms →
ICD-10-CM / ICD-10-PCS / CPT codes, via transformer embeddings + FAISS cosine search,
wrapped in Streamlit. Branded for Cognitio Analytics ("MediCode").

## 2. Which file is the app

`app.py` at the root — this was `u10.py` until the 2026-08-16 restructure. Everything
else with a UI was a superseded iteration and now lives in `archive/ui_versions/`:

| File | Date | Note |
|---|---|---|
| `app.py` (was `u10.py`) | 15 Dec 2025 | **current** — session-state routing + `@st.cache_resource` on the pickle/xlsx loads |
| `archive/ui_versions/u9.py` | 5 Dec 2025 | same UI, no caching, loads pickle at import |
| `archive/ui_versions/U8.py` | 4 Dec 2025 | no ontology tree, no config.ini |
| `archive/ui_versions/app.py` | 30 Nov 2025 | older gradient/magenta design — *not* the current app.py |
| `archive/ui_versions/U_frontend.py` | 26 Nov 2025 | first UI sketch, fully mocked |

Do not "fix" bugs in the archived four. Note the name collision: `archive/ui_versions/app.py`
is the *old* UI, unrelated to the root `app.py`.

### Notebook lineage

`notebooks/final_v2.ipynb` (MedEmbed + SapBERT) is the direct ancestor of
`scripts/icd_10_cm_search_bar.py`. The earlier **BioLORD** line —
`archive/notebooks/final.ipynb`, `late_fusion.ipynb`, `new.ipynb`, all using
`FremyCompany/BioLORD-2023` — was abandoned and is referenced nowhere in `config.ini`.
If you are wondering why a stray `index/icd10_faiss_biolord.index` exists, that is why.

## 3. Non-obvious design decisions

- **Two models for ICD-10-CM, weighted 0.1 / 0.9.** SapBERT contributes little
  directly; it mostly acts as an agreement signal — codes returned by both models get
  a `+0.1` overlap bonus. MedEmbed (`abhinand/MedEmbed-large-v0.1`) does the heavy lifting.
- **Graph proximity boosting** was added because pure embedding search returned
  semantically similar but clinically unrelated codes. The top-1 hit becomes an anchor
  and its hierarchy neighbours are boosted (`gamma = 0.3`, scaled 1.0 / 0.8 / 0.7 / 0.6 / 0.5
  for anchor / parent / grandparent / siblings+cousins / their children).
- **Scores are min-max normalised to 0–100**, so "100%" means *best in this result set*,
  not "certain". The raw value is cosine similarity. Don't present it to clinicians as
  a probability.
- **PCS uses Bio_ClinicalBERT, not MedEmbed** — procedure descriptions are structurally
  different from diagnosis text, and MedEmbed scored worse on them in the notebooks.
- Indexes are `faiss.IndexFlatIP` over L2-normalised vectors, i.e. exact (not
  approximate) cosine search. Fine at 75–80k vectors; would need IVF/HNSW to scale.

## 4. Environment reality check (verified 2026-08-16)

- System Python is **3.14**, which has **no wheels for `torch` or `faiss-cpu`**. The app
  cannot run on it.
- A working venv was created at `.venv/` using the **Python 3.12.14** interpreter at
  `C:\Users\acer\AppData\Roaming\uv\python\cpython-3.12.14-windows-x86_64-none\python.exe`.
  `.venv/` is gitignored; recreate with `python -m venv .venv` from any 3.10–3.12.
- Also available on this machine: Anaconda 3.9, Windows Store 3.9.
- Hugging Face weights (~2.5 GB) land in `%USERPROFILE%\.cache\huggingface`, not in the repo.
- C: drive was at ~92% full — watch disk before installing.

## 4b. Repository restructure — 2026-08-16

The root held 13 notebooks, 5 UI variants and 8 loose data files. Reorganised into
`data/`, `notebooks/`, `assets/`, `archive/{ui_versions,notebooks}/`, with `scripts/`
and `index/` unchanged. All moves used `git mv`, so history follows the files.

Only three code paths needed updating: `graph_pickle` and `group_to_chapter_data` in
`config.ini` (now `data/…`), and the sidebar logo in `app.py` (now `assets/…`). The
full 8-check suite was re-run afterwards and still passes.

`archive/` is inert — nothing in `scripts/` or `app.py` imports from it.

## 5. Path handling — fixed 2026-08-16

`config.ini` originally hard-coded `C:\Users\UNegi\Documents\Project\makethon\...`, the
original author's machine. Every path is now **relative to the project root**, so the app
must be launched from the root (`streamlit run u10.py`), not from `scripts/`.

Two other hard-coded absolute paths were fixed at the same time:

- `scripts/icd_10_cm_search_bar.py` — `ICD_GRAPH_PICKLE` now reads from `config.ini`
  instead of a literal path (it was shadowing the config value it had just loaded).
- `U8.py:19` — `ICD_10_CM_Complete_Data.xlsx` now relative.

The `.ipynb` files still contain `C:\Users\UNegi\...` paths. They are exploratory and
were deliberately left alone; fix them if you ever need to re-run one.

## 6. Git safety audit (2026-08-16)

Done before any push. Findings and their status:

| # | Finding | Status |
|---|---|---|
| 1 | A Hugging Face access token, in plain text in a commented cell of `semantic_match_health.ipynb` | **Removed from working tree. The token itself must still be revoked** at https://huggingface.co/settings/tokens — it was in plain text on disk and may exist in a backup or an earlier copy. |
| 2 | Five FAISS indexes, 73 MB – 306 MB (~1.1 GB). GitHub hard-rejects files > 100 MB | `.gitignore` excludes `*.index` |
| 3 | `icd_code_hierarchy.pkl` (11 MB) — a pickle, which executes arbitrary code on load | `.gitignore` excludes `*.pkl` |
| 4 | `scripts/__pycache__/` with stale `.pyc.<pid>` variants | `.gitignore` excludes them |
| 5 | Scan for API keys / private keys / AWS-Slack-GitHub tokens across all `.py`, `.ipynb`, `.txt`, `.ini`, `.csv`, `.json` | Clean apart from #1 |
| 6 | Patient data / PHI | None. All clinical content is public code-set reference data. `genai_vision.ipynb` mentions "Jane Doe / ACME Corp" — invented prompt examples. |
| 7 | Author's Windows username (`UNegi`) visible in notebook paths | Cosmetic; left in place |
| 8 | CPT code descriptions in `index/cpt_metadata.xlsx` are **AMA copyrighted** | Not a leak, but check licensing before making the repo public. Also gitignored as a `.xlsx`? **No** — it is tracked. Decide deliberately. |

**Consequence of the `.gitignore`:** a fresh clone will not run. Either rebuild the
indexes (`scripts/batch_search.py:index_codes`) or distribute them out-of-band
(Git LFS, a release asset, shared drive).

## 7. Traps discovered while testing (2026-08-16)

- **The pickle unpickles into `__main__`.** `icd_code_hierarchy.pkl` was written from a
  notebook, so `pickle.load()` resolves `__main__.ICDcodeNode`. `u10.py:9` imports
  `ICDcodeNode` purely to satisfy this — it looks like an unused import and it is not.
  Any script that loads the pickle must do the same, or it dies with
  `AttributeError: Can't get attribute 'ICDcodeNode' on <module '__main__'>`.
- **Emoji in `print()` crashed Batch Processing on Windows.** `scripts/batch_search.py`
  printed `✅ / 📦 / 📚 / 🔍` to stdout; a Windows console at cp1252 raises
  `UnicodeEncodeError` and takes the whole batch job down. Replaced with `[ok]` / `[..]`
  markers on 2026-08-16. Don't reintroduce emoji into stdout on this platform.
- **`index/cpt_metadata.xlsx` has 2,155 duplicate rows** (identical `Code` +
  `Description`) out of 18,010, so CPT search returns the same code repeatedly. The ICD
  metadata files are clean. Left unfixed — dedupe the source and re-index, or drop
  duplicates in `cpt_search_bar()`.
- Model load is the dominant cost: ~130 s for the first CPT query (cold weights),
  ~60 s for PCS, on CPU. Subsequent queries are fast. HF weights cache to
  `%USERPROFILE%\.cache\huggingface`, and Windows without Developer Mode can't symlink
  them, so the cache uses more disk than the nominal download size.

## 8. Known rough edges worth fixing next

1. `late_fusion_with_graph_proximity()` re-opens and re-parses the 11 MB pickle **and
   rebuilds the full networkx graph on every single query**. Hoist it to module scope
   or `@st.cache_resource`. This is the single biggest latency win available.
2. `scripts/icd_10_cm_search_bar.py` loads both models + both indexes at *import* time,
   so importing it is unavoidably slow and memory-hungry even for a CPT-only session.
3. `ensure_index_and_metadata()` returns the string `"No Index Found"` on a missing file;
   the caller unpacks it into 4 values and dies with an opaque `ValueError`.
4. The Clinical NLP page is entirely mocked — hard-coded R07.9 / I10 output behind a
   `time.sleep(1.5)`. Anyone demoing this should know.
5. Two ~230 MB indexes are dead weight: `icd10_faiss.index` in the repo root (same size
   as the SapBERT index but a *different* file — md5 `2ae429bd…` vs `141ca2ea…`, so an
   older build) and `index/icd10_faiss_biolord.index` (a BioLORD experiment). Neither is
   referenced by `config.ini` or any script.
6. Two dependency files exist: `requirement.txt` (old, 5 lines) and `requirements.txt`
   (current). Delete the former once nothing references it.
