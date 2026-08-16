
import pandas as pd
import faiss
from transformers import AutoTokenizer, AutoModel
import torch
import numpy as np
import pickle
import networkx as nx
import matplotlib.pyplot as plt
import configparser
config = configparser.ConfigParser()
config.read("config.ini")

# Access values
MODEL_NAME = config["ICD-10-CM"]["model_name"]
FAISS_INDEX_PATH = config["ICD-10-CM"]["faiss_index_path"]
EXCEL_METADATA = config["ICD-10-CM"]["excel_metadata"]
MODEL_NAME_SAP = config["ICD-10-CM"]["model_name"]
FAISS_INDEX_PATH_SAP = config["ICD-10-CM"]["faiss_index_path_sap"]
EXCEL_METADATA_SAP = config["ICD-10-CM"]["excel_metadata_sap"]
GRAPH_DATA = config["ICD-10-CM"]["graph_pickle"]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
BATCH_SIZE = 32
# class for icd code hierarchial tree
class ICDcodeNode:
    def __init__(self, icd_code, description, children, parent):
        self.icd_code = icd_code
        self.description = description
        self.children  =  children
        self.parent = parent

    def get_children(self):
        return self.children
    
    def add_child(self, child):
        if child not in self.children:
            self.children.append(child)

    def get_parent(self):
        return self.parent
    
    def set_parent(self,parent):
        self.parent = parent

    def __repr__(self):
        return f'{self.icd_code} - {self.description} -  Children: {[x.icd_code for x in self.children]}'

# ===========================
# CONFIG
# ===========================
SAPBERT_MODEL = "cambridgeltl/SapBERT-from-PubMedBERT-fulltext"
MEDEMBED_MODEL = "abhinand/MedEmbed-large-v0.1"

SAPBERT_INDEX = FAISS_INDEX_PATH_SAP
SAPBERT_META = EXCEL_METADATA_SAP
MEDEMBED_INDEX = FAISS_INDEX_PATH
MEDEMBED_META = EXCEL_METADATA
ICD_GRAPH_PICKLE = GRAPH_DATA

# ===========================
# LOAD MODELS & INDEXES
# ===========================
sap_tokenizer = AutoTokenizer.from_pretrained(SAPBERT_MODEL)
sap_model = AutoModel.from_pretrained(SAPBERT_MODEL).to(DEVICE).eval()

medembed_tokenizer = AutoTokenizer.from_pretrained(MEDEMBED_MODEL)
medembed_model = AutoModel.from_pretrained(MEDEMBED_MODEL).to(DEVICE).eval()

sap_index = faiss.read_index(SAPBERT_INDEX)
medembed_index = faiss.read_index(MEDEMBED_INDEX)

sap_meta_df = pd.read_excel(SAPBERT_META)
medembed_meta_df = pd.read_excel(MEDEMBED_META)

sap_metadata = {i: {"code": row["Code"], "description": row["Description"]} for i, row in sap_meta_df.iterrows()}
medembed_metadata = {i: {"code": row["Code"], "description": row["Description"]} for i, row in medembed_meta_df.iterrows()}

# ===========================
# EMBEDDING FUNCTIONS
# ===========================
def mean_pooling(last_hidden_state, attention_mask):
    mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
    return (last_hidden_state * mask_expanded).sum(1) / mask_expanded.sum(1).clamp(min=1e-9)

def embed_texts(texts, tokenizer, model):
    all_embs = []
    with torch.no_grad():
        for i in range(0, len(texts), BATCH_SIZE):
            batch = texts[i:i+BATCH_SIZE]
            enc = tokenizer(batch, padding=True, truncation=True, max_length=128, return_tensors="pt").to(DEVICE)
            out = model(**enc)
            emb = mean_pooling(out.last_hidden_state, enc["attention_mask"])
            emb = emb.cpu().numpy()
            all_embs.append(emb)
    embs = np.vstack(all_embs).astype("float32")
    embs /= np.linalg.norm(embs, axis=1, keepdims=True)  # L2 normalization
    return embs

# ===========================
# SEARCH FUNCTION
# ===========================
def search_model(query, index, tokenizer, model, metadata, top_k=200):
    q_emb = embed_texts([query], tokenizer, model)
    D, I = index.search(q_emb, top_k)
    results = []
    for score, idx in zip(D[0], I[0]):
        meta = metadata[idx]
        results.append({"code": meta["code"], "description": meta["description"], "score": float(score), "id": idx})
    return results

def build_networkx_graph(root_node):
    graph = nx.DiGraph()  # Use directed graph for parent-child

    def add_nodes_edges(node):
        graph.add_node(node.icd_code, description=node.description)
        for child in node.get_children():
            graph.add_edge(node.icd_code, child.icd_code)  # parent -> child
            add_nodes_edges(child)

    add_nodes_edges(root_node)
    return graph


# ===========================
# LATE FUSION WITH BOOSTING
# ===========================
def late_fusion_with_graph_proximity(query, alpha=0.1, beta=0.9, gamma=0.3, overlap_bonus=0.1, top_k=200):
    sap_results = search_model(query, sap_index, sap_tokenizer, sap_model, sap_metadata, top_k)
    medembed_results = search_model(query, medembed_index, medembed_tokenizer, medembed_model, medembed_metadata, top_k)

    combined = {}
    for r in sap_results:
        combined[r["code"]] = alpha * r["score"]

    for r in medembed_results:
        if r["code"] in combined:
            combined[r["code"]] += beta * r["score"] + overlap_bonus  # extra boost for overlap
        else:
            combined[r["code"]] = beta * r["score"]

    ranked_initial = sorted(combined.items(), key=lambda x: x[1], reverse=True)
    anchor_code = ranked_initial[0][0].strip()
    boosted_nodes = {}
    with open(ICD_GRAPH_PICKLE, "rb") as f:
        node_dict = pickle.load(f)
    root_node = node_dict['root']
    graph = build_networkx_graph(root_node)
    print(f"Graph loaded: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges")

    if anchor_code in graph:
        # Boost anchor
        boosted_nodes[anchor_code] = gamma * 1.0

        # Get parent
        parents = list(graph.predecessors(anchor_code))
        if parents:
            parent = parents[0]
            boosted_nodes[parent] = gamma * 0.8

            # Boost siblings (children of parent except anchor)
            siblings = [child for child in graph.successors(parent) if child != anchor_code]
            for sib in siblings:
                boosted_nodes[sib] = gamma * 0.6

            # Get grandparent
            grandparents = list(graph.predecessors(parent))
            if grandparents:
                grandparent = grandparents[0]
                boosted_nodes[grandparent] = gamma * 0.7

                # Boost children of grandparent (categories like I21, I22)
                category_nodes = list(graph.successors(grandparent))
                for cat in category_nodes:
                    if cat != parent:
                        boosted_nodes[cat] = gamma * 0.6

                    # Boost children of these categories
                    for cat_child in graph.successors(cat):
                        boosted_nodes[cat_child] = gamma * 0.5

    for code, boost in boosted_nodes.items():
        if code in combined:
            combined[code] += boost

    # Normalize to 0–100 for display
    scores = list(combined.values())
    min_score, max_score = min(scores), max(scores)
    normalized_combined = {code: 100 * (score - min_score) / (max_score - min_score) for code, score in combined.items()}

    ranked_final = sorted(normalized_combined.items(), key=lambda x: x[1], reverse=True)

    formatted_results = []
    for code, score in ranked_final:
        description = sap_meta_df.loc[sap_meta_df["Code"] == code, "Description"].values
        if len(description) == 0:
            description = medembed_meta_df.loc[medembed_meta_df["Code"] == code, "Description"].values
        description = description[0] if len(description) > 0 else "Description not found"
        formatted_results.append({
            "ICD_Code": code.strip(),
            "Description": description,
            "Score (0-100)": round(score, 2)
        })

    return formatted_results, anchor_code, boosted_nodes

def icd_10_cm_search_bar(query):
    final_results, anchor_code, boosted_nodes = late_fusion_with_graph_proximity(query)
    df_result =pd.DataFrame(final_results)

    return df_result
