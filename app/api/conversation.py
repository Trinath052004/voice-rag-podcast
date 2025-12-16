'''from fastapi import APIRouter
from app.agents.controller import run_turn

router = APIRouter()

@router.post("/")
def converse(payload: dict):
    text = payload.get("text")
    return {"response": run_turn(text)}'''


from fastapi import APIRouter
from pydantic import BaseModel

#from app.services.embeddings import embed_texts
#from app.rag.retriever import search_chunks
#from app.rag.prompt import build_conversation_prompt
from app.services.llm import generate_response

router = APIRouter()

class ConversationRequest(BaseModel):
    question: str

@router.post("/")
def converse(req: ConversationRequest):
   answer = generate_response(req.question)
   return {"conversation": answer}
   ''' query_vector = embed_texts([req.question])[0]
    chunks = search_chunks(query_vector)
    prompt = build_conversation_prompt(chunks, req.question)'''
    
