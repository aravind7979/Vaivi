import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_FILE = os.path.join(os.path.dirname(__file__), "index.faiss")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "metadata.json")
MODEL_NAME = 'all-MiniLM-L6-v2'

class RAGRetriever:
    def __init__(self):
        self.model = None
        self.index = None
        self.metadata = []
        self._load_index()

    def _load_index(self):
        if not os.path.exists(INDEX_FILE) or not os.path.exists(METADATA_FILE):
            print("Warning: FAISS index or metadata not found. RAG will return empty results.")
            return

        print("Loading embedding model for retrieval...")
        self.model = SentenceTransformer(MODEL_NAME)
        
        print("Loading FAISS index...")
        self.index = faiss.read_index(INDEX_FILE)
        
        with open(METADATA_FILE, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)

    def retrieve(self, query, top_k=3, threshold=1.5):
        """
        Retrieves relevant chunks for a query.
        L2 distance is used. Lower distance means higher similarity.
        Threshold filters out bad matches.
        """
        if self.index is None or not self.metadata:
            return []

        query_embedding = self.model.encode([query], convert_to_numpy=True)
        distances, indices = self.index.search(query_embedding, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx != -1 and dist < threshold:
                chunk_data = self.metadata[idx]
                results.append({
                    "text": chunk_data["text"],
                    "source": chunk_data["source"],
                    "distance": float(dist)
                })
                
        return results

# Singleton instance
retriever = RAGRetriever()

def get_retriever():
    return retriever
