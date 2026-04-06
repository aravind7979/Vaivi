import os
import json
import math
import google.generativeai as genai

DB_PATH = os.path.join(os.path.dirname(__file__), "embeddings.json")

def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    magnitude1 = math.sqrt(sum(a * a for a in v1))
    magnitude2 = math.sqrt(sum(b * b for b in v2))
    if magnitude1 == 0 or magnitude2 == 0:
        return 0
    return dot_product / (magnitude1 * magnitude2)

def retrieve(query, top_k=3, threshold=0.6):
    """Retrieves top-k most relevant chunks from the embedding cache for a given query."""
    if not os.path.exists(DB_PATH):
        return []
        
    try:
        with open(DB_PATH, 'r', encoding='utf-8') as f:
            db = json.load(f)
    except Exception:
        return []
        
    if not db:
        return []

    # Embed the user query
    try:
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=query,
            task_type="retrieval_query"
        )
        query_embedding = result['embedding']
    except Exception as e:
        print(f"RAG Retrieval Error (Embedding query failed): {e}")
        return []

    # Score against all chunks
    results = []
    for doc_id, data in db.items():
        doc_embedding = data.get("embedding", [])
        if not doc_embedding:
            continue
            
        score = cosine_similarity(query_embedding, doc_embedding)
        if score >= threshold:
            results.append({
                "score": score,
                "text": data.get("text", ""),
                "metadata": data.get("metadata", {})
            })
            
    # Sort by score descending
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]
