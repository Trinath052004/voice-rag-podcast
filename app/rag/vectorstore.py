
from qdrant_client.models import VectorParams, Distance, PointStruct
from app.rag.qdrant_client import client
import uuid

COLLECTION = "docs"

def init_collection(vector_size: int):
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

def store_embeddings(chunks, vectors):
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vectors[i],
            payload={"text": chunks[i]}
        )
        for i in range(len(chunks))
    ]

    client.upsert(
        collection_name=COLLECTION,
        points=points
    )

