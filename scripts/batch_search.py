"""
Semantic Search Pipeline for CPT, ICD-10 CM, and ICD-10 PCS
-----------------------------------------------------------
- Embeds descriptions with a chosen Transformer model (auto-selected per case)
- Builds/loads FAISS indexes for fast cosine similarity search
- Stores & loads metadata per case for result lookups

Cases supported:
    - "cpt"
    - "icd10_cm"
    - "icd10_pcs"

"""

import os
import pandas as pd
import numpy as np
import torch
import faiss
from transformers import AutoTokenizer, AutoModel
import configparser

# ---------------------
# GLOBAL SETTINGS
# ---------------------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 32
MAX_LENGTH = 128  # truncate to fit typical clinical descriptions

# ---------------------
# CASE CONFIGURATION
# ---------------------
# Edit the model names or paths as needed. All below work with AutoModel + mean pooling.

def load_config_map(config_file="config.ini"):
    config = configparser.ConfigParser()
    config.read(config_file)

    config_map = {}

    for section in config.sections():
        config_map[section] = {
            "model_name": config[section]["model_name"],
            "faiss_index_path": config[section]["faiss_index_path"],
            "excel_metadata": config[section]["excel_metadata"],
            "default_threshold": float(config[section].get("default_threshold", config["DEFAULT"]["default_threshold"]))
        }

    return config_map

CONFIG_MAP = load_config_map("config.ini")


# ---------------------
# UTILITIES
# ---------------------
def get_config(case_type: str):
    """Return config dict for the chosen case."""
    # case_type = case_type.lower().strip()
    if case_type not in CONFIG_MAP:
        raise ValueError(f"Invalid case type: '{case_type}'. Choose from {list(CONFIG_MAP.keys())}")
    return CONFIG_MAP[case_type]


def load_model_and_tokenizer(model_name: str):
    """Load HF tokenizer & model and move model to the selected device."""
    tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=True)
    model = AutoModel.from_pretrained(model_name)
    model.eval()
    model.to(DEVICE)
    return tokenizer, model


def mean_pooling(last_hidden_state: torch.Tensor, attention_mask: torch.Tensor) -> torch.Tensor:
    """Mean pool token embeddings using attention mask."""
    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    return (last_hidden_state * mask_expanded).sum(1) / mask_expanded.sum(1).clamp(min=1e-9)
	
def embed_texts(
    texts,
    tokenizer,
    model,
    batch_size: int = BATCH_SIZE,
    max_length: int = MAX_LENGTH
) -> np.ndarray:
    """Compute L2-normalized sentence embeddings for a list of texts."""
    all_embs = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=max_length,
                return_tensors="pt"
            ).to(DEVICE)

            out = model(**enc)
            emb = mean_pooling(out.last_hidden_state, enc["attention_mask"])
            emb = emb.cpu().numpy()
            all_embs.append(emb)

    embs = np.vstack(all_embs).astype("float32")
    # L2 normalization -> inner product equals cosine similarity
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    return embs


def build_faiss_index(embeddings: np.ndarray, index_path: str):
    """Create and persist a FAISS inner-product index."""
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    faiss.write_index(index, index_path)
    print(f"[ok] FAISS index saved at {index_path}")
    return index


def load_faiss_index(index_path: str):
    """Load an existing FAISS index from disk."""
    if not os.path.exists(index_path):
        raise FileNotFoundError(f"FAISS index not found at '{index_path}'")
    index = faiss.read_index(index_path)
    print(f"[ok] Loaded FAISS index from {index_path}")
    return index
	

def load_metadata_map(excel_metadata_path: str):
    """
    Load metadata Excel and return id -> {code, description}.
    If faiss_id column is missing, uses row order as ids.
    """
    if not os.path.exists(excel_metadata_path):
        raise FileNotFoundError(f"Metadata Excel not found at '{excel_metadata_path}'")

    df = pd.read_excel(excel_metadata_path, dtype=str).fillna("")
    required = {"Code", "Description"}
    if not required.issubset(df.columns):
        raise ValueError(f"Excel must contain columns: {required}")

    # Prefer existing faiss_id if present, else row index
    if "faiss_id" not in df.columns:
        df["faiss_id"] = range(len(df))

    metadata_map = {
        int(row["faiss_id"]): {"code": row["Code"], "description": row["Description"]}
        for _, row in df.iterrows()
    }
    print(f"[ok] Loaded metadata from {excel_metadata_path} ({len(metadata_map)} records)")
    return metadata_map


# ---------------------
# INDEXING PIPELINE (PER CASE)
# ---------------------
def index_codes(case_type: str, excel_path: str):
    """
    Build embeddings and FAISS index for the chosen case_type from excel_path.
    Excel must have columns: 'Code' and 'Description'.
    Persists index and metadata per case configuration.
    Returns (index, tokenizer, model, metadata_map).
    """
    cfg = get_config(case_type)
    model_name = cfg["model_name"]
    faiss_index_path = cfg["faiss_index_path"]
    excel_metadata_path = cfg["excel_metadata"]

    # Load Excel
    df = pd.read_excel(excel_path, dtype=str).fillna("")
    if not {"Code", "Description"}.issubset(df.columns):
        raise ValueError("Excel must contain columns: 'Code' and 'Description'")

    texts = df["Description"].tolist()

    # Load model & tokenizer
    tokenizer, model = load_model_and_tokenizer(model_name)
    print(f"[..] Generating embeddings using '{model_name}' on {DEVICE}...")
    embs = embed_texts(texts, tokenizer, model)

    # Build FAISS index
    print("[..] Building FAISS index...")
    index = build_faiss_index(embs, faiss_index_path)

    # Save metadata for lookup
    df["faiss_id"] = range(len(df))
    df.to_excel(excel_metadata_path, index=False)
    print(f"[ok] Metadata saved to {excel_metadata_path}")

    # Create mapping: id -> {code, description}
    metadata_map = {
        i: {"code": row["Code"], "description": row["Description"]}
        for i, row in df.iterrows()
    }

    return index, tokenizer, model, metadata_map


# ---------------------
# SEARCH
# ---------------------
def search_codes(
    case_type: str,
    query: str,
    index,
    tokenizer,
    model,
    metadata_map: dict,
    top_k: int,
    threshold: float | None = None
):
    """
    Search for the most similar codes in the selected index.
    Returns a list of dicts: {Code, Description, Score (cosine)} above threshold.
    """
    cfg = get_config(case_type)
    if threshold is None:
        threshold = cfg["default_threshold"]

    print(f"[..] Searching in '{case_type}' (top_k={top_k}, threshold={threshold})...")
    q_emb = embed_texts([query], tokenizer, model)
    D, I = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(D[0], I[0]):
        if score >= threshold:
            meta = metadata_map.get(int(idx))
            if meta:  # safety check
                results.append({
                    "Code": meta["code"],
                    "Description": meta["description"],
                    "Score (cosine)": round(float(score)*100, 4),
                })
    return results


# ---------------------
# CONVENIENCE: ENSURE INDEX IS READY
# ---------------------
def ensure_index_and_metadata(case_type: str):
    """
    If index/metadata exist, just load them. Otherwise, build from source Excel.
    Returns (index, tokenizer, model, metadata_map).
    """
    cfg = get_config(case_type)
    index_path = cfg["faiss_index_path"]
    metadata_path = cfg["excel_metadata"]

    # Always need tokenizer/model for query embedding
    tokenizer, model = load_model_and_tokenizer(cfg["model_name"])

    if os.path.exists(index_path) and os.path.exists(metadata_path):
        index = load_faiss_index(index_path)
        metadata_map = load_metadata_map(metadata_path)
        return index, tokenizer, model, metadata_map

    # Build fresh index if either file missing

    return "No Index Found"

def batch_search_function(case_type: str, df_queries: pd.DataFrame,top_k_num:int):
    """
    df_queries must contain a column named 'Query'
    Returns a dataframe with columns: Query, Code, Description, Score
    """

    # 1) Ensure FAISS index + metadata + model are ready
    index, tokenizer, model, metadata_map = ensure_index_and_metadata(
        case_type
    )

    # 2) Validate query column
    if "Query" not in df_queries.columns:
        raise ValueError("Input dataframe must contain a column named 'Query'")

    # 3) Collect results
    all_results = []
    top_k = top_k_num  # or expose as parameter

    for q in df_queries["Query"].astype(str):
        hits = search_codes(
            case_type=case_type,
            query=q,
            index=index,
            tokenizer=tokenizer,
            model=model,
            metadata_map=metadata_map,
            top_k=top_k,
            threshold=None
        )
        
        # Add results
        if hits:
            for h in hits:
                all_results.append({
                    "Query": q,
                    "Code": h["Code"],
                    "Description": h["Description"],
                    "Confidence": h["Score (cosine)"]
                })
        else:
            # Add empty row if no match
            all_results.append({
                "Query": q,
                "Code": "",
                "Description": "",
                "Confidence": ""
            })

    # Convert to dataframe
    df_results = pd.DataFrame(all_results)

    return df_results





