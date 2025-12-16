from app.rag.qdrant_client import client
from sentence_transformers import SentenceTransformer

# ======================
# Config
# ======================
COLLECTION = "docs"


# ======================
# Clients
# ======================

model = SentenceTransformer("all-MiniLM-L6-v2")


# ======================
# Retrieve function
# ======================
def retrieve(query: str, top_k: int = 5) -> list[str]:
    """
    Semantic search over indexed PDF chunks.
    """
    # Embed query
    query_vector = model.encode(query).tolist()

    # Qdrant >= 1.16 API
    result = client.query_points(
        collection_name=COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    return [
        point.payload["text"] 
        for point in result.points
        if point.payload and "text" in point.payload
        ]

