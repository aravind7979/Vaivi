import os
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
INDEX_FILE = os.path.join(os.path.dirname(__file__), "index.faiss")
METADATA_FILE = os.path.join(os.path.dirname(__file__), "metadata.json")
MODEL_NAME = 'all-MiniLM-L6-v2'

def chunk_text(text, chunk_size=300, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def ingest():
    print("Loading embedding model...")
    model = SentenceTransformer(MODEL_NAME)
    
    docs = []
    metadata = []
    
    print(f"Reading from {KNOWLEDGE_DIR}...")
    if not os.path.exists(KNOWLEDGE_DIR):
        os.makedirs(KNOWLEDGE_DIR)
        
    for filename in os.listdir(KNOWLEDGE_DIR):
        if filename.endswith(".json"):
            filepath = os.path.join(KNOWLEDGE_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    # Support different JSON structures
                    text_content = ""
                    if isinstance(data, dict):
                        # Flatten dict to string or extract a specific field like "content"
                        for k, v in data.items():
                            if isinstance(v, str):
                                text_content += f"{k}: {v}\n"
                            elif isinstance(v, list):
                                text_content += f"{k}:\n" + "\n".join(str(item) for item in v) + "\n"
                    elif isinstance(data, list):
                        for item in data:
                            text_content += json.dumps(item) + "\n"
                    else:
                        text_content = str(data)
                        
                    chunks = chunk_text(text_content)
                    
                    for i, chunk in enumerate(chunks):
                        docs.append(chunk)
                        metadata.append({
                            "source": filename,
                            "chunk_index": i,
                            "text": chunk
                        })
                        
                except Exception as e:
                    print(f"Error parsing {filename}: {e}")

    if not docs:
        print("No documents found to ingest.")
        return

    print(f"Computing embeddings for {len(docs)} chunks...")
    embeddings = model.encode(docs, show_progress_bar=True, convert_to_numpy=True)
    
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    
    print("Building FAISS index...")
    index.add(embeddings)
    
    faiss.write_index(index, INDEX_FILE)
    
    with open(METADATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(metadata, f)
        
    print(f"Successfully ingested and cached to {INDEX_FILE}")

if __name__ == "__main__":
    ingest()
