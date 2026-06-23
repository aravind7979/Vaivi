import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "memories"
MODEL_NAME = 'all-MiniLM-L6-v2'

class RAGRetriever:
    def __init__(self):
        self.model = None
        self.client = None
        self._init_qdrant()

    def _init_qdrant(self):
        if not QDRANT_URL:
            print("Warning: QDRANT_URL is not set. Qdrant retriever will not function.")
            return

        print("Loading embedding model for Qdrant...")
        self.model = SentenceTransformer(MODEL_NAME)
        
        print("Connecting to Qdrant Cloud...")
        self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
        
        # Check and create collection
        try:
            # We use a try-except block here because checking if collection exists 
            # might throw an exception if the API key/URL is invalid or connection fails.
            if not self.client.collection_exists(COLLECTION_NAME):
                embedding_dim = self.model.get_sentence_embedding_dimension()
                self.client.create_collection(
                    collection_name=COLLECTION_NAME,
                    vectors_config=qmodels.VectorParams(
                        size=embedding_dim,
                        distance=qmodels.Distance.EUCLID  # Matches original FAISS L2 distance
                    )
                )
                print(f"Created Qdrant collection: {COLLECTION_NAME}")
            else:
                print(f"Connected to existing Qdrant collection: {COLLECTION_NAME}")
        except Exception as e:
            print(f"Failed to initialize Qdrant collection: {e}")

    def add_to_index(self, text, metadata_dict):
        """
        Dynamically adds a new document or memory to the Qdrant collection.
        """
        if self.client is None:
            self._init_qdrant()
            if self.client is None:
                print("Error: Qdrant client not initialized. Cannot add to index.")
                return

        try:
            embedding = self.model.encode([text], convert_to_numpy=True)
            point_id = str(uuid.uuid4())
            payload = {"text": text, **metadata_dict}
            
            self.client.upsert(
                collection_name=COLLECTION_NAME,
                points=[
                    qmodels.PointStruct(
                        id=point_id,
                        vector=embedding[0].tolist(),
                        payload=payload
                    )
                ]
            )
            print(f"Successfully added point {point_id} to Qdrant Cloud.")
        except Exception as e:
            print(f"Qdrant add failed: {e}")

    def retrieve(self, query, top_k=3, threshold=1.5, filter_type=None, user_id=None):
        """
        Retrieves relevant chunks for a query from Qdrant Cloud.
        Using EUCLID distance: lower score means higher similarity.
        """
        if self.client is None or self.model is None:
            self._init_qdrant()
            if self.client is None:
                return []

        try:
            query_embedding = self.model.encode([query], convert_to_numpy=True)
            
            # Construct multi-tenant filtering conditions
            must_conditions = []
            if filter_type:
                must_conditions.append(
                    qmodels.FieldCondition(
                        key="type",
                        match=qmodels.MatchValue(value=filter_type)
                    )
                )
            if user_id is not None:
                must_conditions.append(
                    qmodels.FieldCondition(
                        key="user_id",
                        match=qmodels.MatchValue(value=user_id)
                    )
                )

            query_filter = qmodels.Filter(must=must_conditions) if must_conditions else None

            search_results = self.client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_embedding[0].tolist(),
                limit=top_k,
                query_filter=query_filter,
                with_payload=True
            )
            
            results = []
            for hit in search_results:
                # Euclidean distance: smaller scores represent closer vectors
                if hit.score < threshold:
                    payload = hit.payload
                    results.append({
                        "text": payload.get("text", ""),
                        "source": payload.get("source", "unknown"),
                        "distance": float(hit.score)
                    })
            return results
        except Exception as e:
            print(f"Qdrant search failed: {e}")
            return []

# Singleton instance
retriever = RAGRetriever()

def get_retriever():
    return retriever
