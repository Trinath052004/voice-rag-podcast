# AGENTS.md - Voice RAG Podcast

## Commands
- **Run server**: `uvicorn app.main:app --reload`
- **Install deps**: `pip install -r requirements.txt`
- **No test framework configured** - add pytest to requirements.txt if needed

## Architecture
- **FastAPI app** in `app/main.py` with conversation API at `/conversation`
- **RAG pipeline** (`app/rag/`): PDF ingestion, chunking, embeddings, Qdrant vector store, retrieval
- **LLM services** (`app/services/`): Gemini via `google-generativeai`, alternate Vertex AI support
- **Agents** (`app/agents/`): Multi-agent system with controller, curious_agent, explainer_agent
- **Vector DB**: Qdrant running locally at `http://localhost:6333`, storage in `qdrant_storage/`

## Environment Variables
- `GEMINI_API_KEY` - Required for LLM
- `GCP_PROJECT_ID`, `GCP_LOCATION` - For Vertex AI (optional)

## Code Style
- Python 3.x with type hints encouraged
- Imports: stdlib first, then third-party, then local (`from app.x import y`)
- Use absolute imports from `app` package
- Config via environment variables in `app/config.py`
