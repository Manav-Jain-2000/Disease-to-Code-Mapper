# ✅ Load FAISS index and metadata
import pandas as pd
import faiss
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import configparser




# Load config.ini
config = configparser.ConfigParser()
config.read("config.ini")

# Access values
MODEL_NAME = config["ICD-10-PCS"]["model_name"]
FAISS_INDEX_PATH = config["ICD-10-PCS"]["faiss_index_path"]
EXCEL_METADATA = config["ICD-10-PCS"]["excel_metadata"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 32

# Load model & tokenizer
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModel.from_pretrained(MODEL_NAME).to(DEVICE).eval()

# Load FAISS index
index = faiss.read_index(FAISS_INDEX_PATH)

# Load metadata
df = pd.read_excel(EXCEL_METADATA)
metadata_map = {i: {"code": row["Code"], "description": row["Description"]} for i, row in df.iterrows()}

# Embed query
def mean_pooling(last_hidden_state, attention_mask):
    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    return (last_hidden_state * mask_expanded).sum(1) / mask_expanded.sum(1).clamp(min=1e-9)


def embed_texts(texts, tokenizer, model, batch_size=BATCH_SIZE):
    all_embs = []
    with torch.no_grad():
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            enc = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt").to(DEVICE)
            out = model(**enc)
            emb = mean_pooling(out.last_hidden_state, enc["attention_mask"])
            emb = emb.cpu().numpy()
            all_embs.append(emb)
    embs = np.vstack(all_embs).astype("float32")
    # L2 normalization for cosine similarity
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)
    return embs

def search_icd10_pcs_search_bar(query):
    top_k=100
    threshold=0.35
    q_emb = embed_texts([query], tokenizer, model)
    D, I = index.search(q_emb, top_k)

    results = []
    for score, idx in zip(D[0], I[0]):
        if score >= threshold:
            meta = metadata_map[idx]
            results.append(
                {
                    "code": meta["code"],
                    "description": meta["description"],
                    "confidence": round(float(score)*100, 4),
                }
            )
    return pd.DataFrame(results)
