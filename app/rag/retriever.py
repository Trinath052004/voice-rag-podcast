
import logging
from app.rag.qdrant_client import client
from sentence_transformers import SentenceTransformer
from typing import List, Tuple

# ======================
# Config
# ======================
COLLECTION = "docs"

# ======================
# Clients
# ======================

model = SentenceTransformer("all-MiniLM-L6-v2")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# ======================
# Retrieve function
# ======================
def retrieve(query: str, top_k: int = 5) -> List[Tuple[str, float]]:
    """
    Semantic search over indexed PDF chunks.
    Returns a list of tuples containing the text and score of each retrieved chunk.
    """
    try:
        # Embed query
        query_vector = model.encode(query).tolist()

        # Qdrant >= 1.16 API
        result = client.query_points(
            collection_name=COLLECTION,
            query=query_vector,
            limit=top_k,
            with_payload=True,
            with_vectors=False # We don't need the vectors in the result
        )

        return [
            (point.payload["text"], point.score)
            for point in result.points
            if point.payload and "text" in point.payload
        ]
    except Exception as e:
        logging.error(f"Error during retrieval: {e}")
        return []
