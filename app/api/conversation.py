from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.controller import run_podcast_turn, run_user_question, run_multi_turn_podcast
from fastapi.responses import StreamingResponse
from app.services.tts import generate_podcast_audio,generate_combined_podcast,text_to_speech_stream

router = APIRouter()

class QuestionRequest(BaseModel):
    question: str | None = None
    topic: str = "overview"
    num_turns: int = 1

@router.post("/")
def converse(req: QuestionRequest):
    """User asks a question (third party interjection)."""
    if req.question:
        return run_user_question(req.question)
    return run_podcast_turn(req.topic)

@router.post("/podcast")
def podcast_turn(req: QuestionRequest):
    """Generate AI-to-AI podcast turn."""
    if req.num_turns > 1:
        return {"turns": run_multi_turn_podcast(req.topic, req.num_turns)}
    return run_podcast_turn(req.topic)

@router.post("/ask")
def user_asks(req: QuestionRequest):
    """Explicit endpoint for user questions."""
    if not req.question:
        return {"error": "question is required"}
    return run_user_question(req.question)

@router.post("/podcast/audio")
def podcast_with_audio(req: QuestionRequest):
    """Returns podcast with separate audio for each host."""
    conversation = run_podcast_turn(req.topic)
    audio = generate_podcast_audio(conversation)
    return {**conversation, **audio}

@router.post("/podcast/audio/combined")
def podcast_combined_audio(req: QuestionRequest):
    """Returns podcast with single combined audio file."""
    conversation = run_podcast_turn(req.topic)
    combined = generate_combined_podcast(conversation)
    return {**conversation, "combined_audio": combined}

@router.post("/podcast/stream")
def podcast_stream(req: QuestionRequest):
    """Stream the explainer's response audio in real-time."""
    conversation = run_podcast_turn(req.topic)
    
    def audio_stream():
        for chunk in text_to_speech_stream(conversation["explainer"], "explainer"):
            yield chunk
    
    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=podcast.mp3"}
    )