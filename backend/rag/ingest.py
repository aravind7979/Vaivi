import os
import json
import glob
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
DB_PATH = os.path.join(os.path.dirname(__file__), "embeddings.json")

def ingest_knowledge():
    """Reads all JSON files in the knowledge directory, generates embeddings, and saves to a local JSON DB."""
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set. Cannot run ingestion.")
        return

    documents = []
    
    # Load all json files
    for filepath in glob.glob(os.path.join(KNOWLEDGE_DIR, "*.json")):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    for item in data:
                        documents.append(item)
                else:
                    documents.append(data)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")

    print(f"Loaded {len(documents)} knowledge items.")

    # Load existing embeddings to avoid re-embedding
    db = {}
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, 'r', encoding='utf-8') as f:
                db = json.load(f)
        except Exception:
            db = {}

    updated = False
    for doc in documents:
        doc_id = doc.get("document_id")
        if not doc_id:
            continue
            
        if doc_id in db:
            continue # already embedded
        
        # Build a text block for embedding
        title = doc.get("title", "")
        summary = doc.get("summary", "")
        content = doc.get("content", "")
        domain = doc.get("domain", "")
        
        text_to_embed = f"Title: {title}\nDomain: {domain}\nSummary: {summary}\nContent: {content}"
        
        print(f"Generating embedding for {doc_id}...")
        try:
            result = genai.embed_content(
                model="models/text-embedding-004",
                content=text_to_embed,
                task_type="retrieval_document"
            )
            embedding = result['embedding']
            
            db[doc_id] = {
                "text": text_to_embed,
                "metadata": {
                    "title": title,
                    "domain": domain,
                    "document_id": doc_id,
                    "source": "knowledge_file"
                },
                "embedding": embedding
            }
            updated = True
        except Exception as e:
            print(f"Failed to embed {doc_id}: {e}")

    if updated:
        with open(DB_PATH, 'w', encoding='utf-8') as f:
            json.dump(db, f)
        print(f"Successfully saved {len(db)} embedded chunks to {DB_PATH}.")
    else:
        print("No new documents to embed. Cache is up to date.")

if __name__ == "__main__":
    ingest_knowledge()
