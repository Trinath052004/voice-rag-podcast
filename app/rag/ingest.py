from pathlib import Path
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

    return len(chunks)