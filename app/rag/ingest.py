'''from pathlib import Path
from pypdf import PdfReader

from app.rag.chunking import chunk_text
from app.rag.embeddings import embed_texts
from app.rag.vectorstore import init_collection, store_embeddings


def ingest_pdf(pdf_path: str | Path) -> str:
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    reader = PdfReader(str(pdf_path))

    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text
def ingest_and_index(pdf_path: str | Path) -> int:
    # 1. Extract text
    text = ingest_pdf(pdf_path)

    # 2. Chunk text
    chunks = chunk_text(text)

    # 3. Embed chunks
    embeddings = embed_texts(chunks)

    # 4. Initialize vector DB collection
    init_collection(len(embeddings[0]))

    # 5. Store embeddings
    store_embeddings(chunks, embeddings)

    return len(chunks)'''




from pypdf import PdfReader
from app.rag.chunking import chunk_text
from app.rag.qdrant_client import client
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct, VectorParams, Distance
import uuid

COLLECTION = "docs"
model = SentenceTransformer("all-MiniLM-L6-v2")

def ingest_pdf(pdf_path: str):
    # Extract text
    reader = PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    
    # Chunk
    chunks = chunk_text(text)
    
    # Create collection if not exists
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    
    # Embed and upsert
    embeddings = model.encode(chunks).tolist()
    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=emb,
            payload={"text": chunk}
        )
        for chunk, emb in zip(chunks, embeddings)
    ]
    
    client.upsert(collection_name=COLLECTION, points=points)
    return len(chunks)

if __name__ == "__main__":
    count = ingest_pdf("sample.pdf")
    print(f"Ingested {count} chunks")