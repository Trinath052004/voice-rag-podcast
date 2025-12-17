# Voice RAG Podcast - Complete Setup to Deployment Guide

## Current State Assessment

### ✅ What's Working
- FastAPI server with `/conversation` endpoint
- PDF ingestion, chunking, and embedding pipeline
- Qdrant vector store integration
- Semantic retrieval with `all-MiniLM-L6-v2`
- Single Q&A flow via Gemini LLM

### 🚧 Needs Completion
- Multi-agent podcast system (curious + explainer agents)
- Third host agent
- Voice/audio synthesis
- PDF upload endpoint

### ⚠️ Bugs to Fix
- `requirements.txt` has `qdrant-client=1.9.0` (should be `==`)
- Missing dependencies: `sentence-transformers`, `google-generativeai`

---

## Phase 1: Fix Dependencies & Environment

### 1.1 Fix requirements.txt
```txt
fastapi
uvicorn[standard]
pypdf
qdrant-client==1.9.0
google-cloud-aiplatform
google-generativeai
sentence-transformers
python-dotenv
python-multipart
pydantic
```

### 1.2 Create .env file
```env
GEMINI_API_KEY=your_gemini_api_key_here
GCP_PROJECT_ID=your_project_id          # Optional for Vertex AI
GCP_LOCATION=us-central1                 # Optional for Vertex AI
```

### 1.3 Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install
pip install -r requirements.txt
```

---

## Phase 2: Complete RAG Pipeline

### 2.1 Verify Qdrant is Running
```bash
# Option A: Docker (recommended)
docker run -p 6333:6333 -v ./qdrant_storage:/qdrant/storage qdrant/qdrant

# Option B: Use existing qdrant_storage folder (already in repo)
```

### 2.2 Ingest PDF
Create/update `app/rag/ingest.py`:
```python
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
```

### 2.3 Run Ingestion
```bash
python -m app.rag.ingest
```

---

## Phase 3: Complete Multi-Agent System

**Three-Party Setup:**
1. **Curious Agent** — AI host that asks engaging questions
2. **Explainer Agent** — AI expert that answers and wraps up
3. **User** — Third party who can interject with their own questions

### 3.1 Update curious_agent.py
```python
def curious_prompt(context: str) -> str:
    return f"""You are the CURIOUS HOST of an educational podcast.
Your job is to ask engaging, thought-provoking questions about the topic.

Based on this context, ask ONE interesting question that a listener would want answered:

Context:
{context}

Ask a question that:
- Is specific and grounded in the context
- Would intrigue a general audience
- Leads to an educational answer

Your question:"""
```

### 3.2 Update explainer_agent.py
```python
def explainer_prompt(context: str, question: str, should_wrap_up: bool = False) -> str:
    wrap_up_instruction = """

After your answer, provide a brief wrap-up that:
- Summarizes the key takeaway in 1 sentence
- Teases what listeners might want to explore next
- Invites the user to ask follow-up questions""" if should_wrap_up else ""
    
    return f"""You are the EXPERT HOST of an educational podcast.
Your job is to give clear, engaging explanations.

Context:
{context}

Question from co-host:
{question}

Provide a conversational, informative answer that:
- Directly addresses the question
- Uses examples from the context
- Is engaging for podcast listeners
- Is 2-3 paragraphs max{wrap_up_instruction}

Your response:"""


def explainer_wrap_up_prompt(question: str, answer: str) -> str:
    """Standalone wrap-up when needed separately."""
    return f"""You are the EXPERT HOST of an educational podcast.
You just answered a question. Now wrap up this exchange.

Q: {question}
A: {answer}

Provide a 1-2 sentence wrap-up that:
- Summarizes the key takeaway
- Invites the listener to ask follow-up questions or explore related topics

Your wrap-up:"""
```

### 3.3 Update Controller
```python
from app.services.llm import call_gemini
from app.rag.retriever import retrieve
from app.agents.curious_agent import curious_prompt
from app.agents.explainer_agent import explainer_prompt, explainer_wrap_up_prompt

def run_podcast_turn(topic: str = "overview") -> dict:
    """
    Auto-generated podcast turn between Curious and Explainer.
    User can interject via run_user_question().
    """
    # Retrieve context
    contexts = retrieve(topic, top_k=5)
    context = "\n\n".join(contexts)
    
    # Curious asks
    question = call_gemini(curious_prompt(context))
    
    # Explainer answers with wrap-up
    answer = call_gemini(explainer_prompt(context, question, should_wrap_up=True))
    
    return {
        "curious": question,
        "explainer": answer
    }

def run_user_question(user_input: str) -> dict:
    """
    User (third party) interjects with their own question.
    Explainer answers and wraps up.
    """
    contexts = retrieve(user_input, top_k=5)
    context = "\n\n".join(contexts)
    
    # Explainer answers user's question with wrap-up
    answer = call_gemini(explainer_prompt(context, user_input, should_wrap_up=True))
    
    return {
        "user_question": user_input,
        "explainer": answer
    }

def run_multi_turn_podcast(topic: str = "overview", num_turns: int = 3) -> list:
    """
    Generate multiple podcast turns for a longer episode.
    """
    turns = []
    for i in range(num_turns):
        is_last = (i == num_turns - 1)
        contexts = retrieve(topic, top_k=5)
        context = "\n\n".join(contexts)
        
        question = call_gemini(curious_prompt(context))
        answer = call_gemini(explainer_prompt(context, question, should_wrap_up=is_last))
        
        turns.append({
            "turn": i + 1,
            "curious": question,
            "explainer": answer
        })
    
    return turns
```

### 3.4 Update API Endpoints
Update `app/api/conversation.py`:
```python
from fastapi import APIRouter
from pydantic import BaseModel
from app.agents.controller import run_podcast_turn, run_user_question, run_multi_turn_podcast

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
```

---

## Phase 4: Add Voice Synthesis (ElevenLabs)

### 4.1 Add TTS Dependency
Add to `requirements.txt`:
```txt
elevenlabs
```

### 4.2 Add ElevenLabs API Key
Add to `.env`:
```env
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
```

### 4.3 Get Voice IDs
1. Go to https://elevenlabs.io/voice-library
2. Pick 3 distinct voices for each host
3. Copy voice IDs from the voice settings

Popular choices:
- **Curious Host**: "Josh" (young, energetic) - `TxGEqnHWrfWFTfGW9XjX`
- **Explainer Host**: "Rachel" (clear, professional) - `21m00Tcm4TlvDq8ikWAM`
- **Moderator**: "Adam" (warm, authoritative) - `pNInz6obpgDQGcFmaJgB`

### 4.4 Create Voice Service
Create `app/services/tts.py`:
```python
import os
import base64
from elevenlabs import ElevenLabs

client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])

# Map agent roles to ElevenLabs voice IDs
# Replace with your preferred voices from https://elevenlabs.io/voice-library
VOICES = {
    "curious": "TxGEqnHWrfWFTfGW9XjX",    # Josh - energetic, curious
    "explainer": "21m00Tcm4TlvDq8ikWAM",  # Rachel - clear, professional
    "moderator": "pNInz6obpgDQGcFmaJgB",  # Adam - warm, authoritative
}

def text_to_speech(text: str, voice: str = "explainer") -> str:
    """
    Convert text to speech using ElevenLabs.
    Returns base64-encoded MP3 audio.
    """
    voice_id = VOICES.get(voice, VOICES["explainer"])
    
    audio_generator = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_multilingual_v2",  # Best quality
        output_format="mp3_44100_128",
    )
    
    # Collect audio bytes from generator
    audio_bytes = b"".join(audio_generator)
    
    return base64.b64encode(audio_bytes).decode()

def text_to_speech_stream(text: str, voice: str = "explainer"):
    """
    Stream audio for real-time playback.
    Yields audio chunks.
    """
    voice_id = VOICES.get(voice, VOICES["explainer"])
    
    return client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_turbo_v2_5",  # Faster for streaming
        output_format="mp3_44100_128",
    )

def generate_podcast_audio(conversation: dict) -> dict:
    """Generate audio for full podcast turn."""
    return {
        "curious_audio": text_to_speech(conversation["curious"], "curious"),
        "explainer_audio": text_to_speech(conversation["explainer"], "explainer"),
        "moderator_audio": text_to_speech(conversation["moderator"], "moderator"),
    }

def generate_combined_podcast(conversation: dict) -> str:
    """
    Generate a single combined audio file for the full podcast turn.
    Returns base64-encoded MP3.
    """
    # Generate individual segments
    curious_audio = b"".join(client.text_to_speech.convert(
        voice_id=VOICES["curious"],
        text=conversation["curious"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    ))
    
    explainer_audio = b"".join(client.text_to_speech.convert(
        voice_id=VOICES["explainer"],
        text=conversation["explainer"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    ))
    
    moderator_audio = b"".join(client.text_to_speech.convert(
        voice_id=VOICES["moderator"],
        text=conversation["moderator"],
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    ))
    
    # Combine (simple concatenation - works for MP3)
    combined = curious_audio + explainer_audio + moderator_audio
    
    return base64.b64encode(combined).decode()
```

### 4.5 Add Audio Endpoints
Add to `app/api/conversation.py`:
```python  
from fastapi.responses import StreamingResponse
from app.services.tts import generate_podcast_audio, generate_combined_podcast, text_to_speech_stream

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
```

### 4.6 ElevenLabs Voice Settings (Optional)
For more control, you can adjust voice settings:
```python
from elevenlabs import VoiceSettings

audio_generator = client.text_to_speech.convert(
    voice_id=voice_id,
    text=text,
    model_id="eleven_multilingual_v2",
    voice_settings=VoiceSettings(
        stability=0.5,        # 0-1: Lower = more expressive
        similarity_boost=0.8, # 0-1: Higher = closer to original voice
        style=0.5,            # 0-1: Style exaggeration
        use_speaker_boost=True
    ),
    output_format="mp3_44100_128",
)
```

### 4.7 ElevenLabs Pricing Notes
- **Free tier**: 10,000 characters/month
- **Starter**: $5/month for 30,000 characters
- **Creator**: $22/month for 100,000 characters
- Average podcast turn ≈ 500-1000 characters
- Monitor usage at https://elevenlabs.io/app/usage

---

## Phase 5: Add PDF Upload Endpoint

### 5.1 Create Upload API
Create `app/api/upload.py`:
```python
from fastapi import APIRouter, UploadFile, File
from app.rag.ingest import ingest_pdf
import tempfile
import os

router = APIRouter()

@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    # Save temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        chunks = ingest_pdf(tmp_path)
        return {"status": "success", "chunks_indexed": chunks}
    finally:
        os.unlink(tmp_path)
```

### 5.2 Enable in main.py
```python
from fastapi import FastAPI
from app.api.conversation import router as conversation_router
from app.api.upload import router as upload_router

app = FastAPI(title="Voice RAG Podcast")

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])

@app.get("/")
def health():
    return {"status": "ok"}
```

---

## Phase 6: Testing

### 6.1 Add pytest
Add to `requirements.txt`:
```txt
pytest
httpx
pytest-asyncio
```

### 6.2 Create Tests
Create `tests/test_api.py`:
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_conversation():
    response = client.post("/conversation/", json={"question": "What is this about?"})
    assert response.status_code == 200
    assert "answer" in response.json()

def test_podcast_turn():
    response = client.post("/conversation/podcast", json={})
    assert response.status_code == 200
    data = response.json()
    assert "curious" in data
    assert "explainer" in data
```

### 6.3 Run Tests
```bash
pytest tests/ -v
```

---

## Phase 7: Frontend Setup

### 7.1 Project Structure
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   ├── AudioPlayer.jsx
│   │   ├── ChatMessage.jsx
│   │   ├── PodcastPlayer.jsx
│   │   └── UploadPDF.jsx
│   ├── App.jsx
│   ├── App.css
│   ├── api.js
│   └── main.jsx
├── package.json
├── vite.config.js
└── .env
```

### 7.2 Initialize React + Vite
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install axios
```

### 7.3 Create API Service
Create `frontend/src/api.js`:
```javascript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: { 'Content-Type': 'application/json' }
});

export const uploadPDF = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/upload/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const askQuestion = async (question) => {
  const response = await api.post('/conversation/', { question });
  return response.data;
};

export const generatePodcast = async (topic = 'overview', numTurns = 1) => {
  const response = await api.post('/conversation/podcast', { topic, num_turns: numTurns });
  return response.data;
};

export const generatePodcastWithAudio = async (topic = 'overview') => {
  const response = await api.post('/conversation/podcast/audio', { topic });
  return response.data;
};

export const getPodcastStream = (topic = 'overview') => {
  return `${API_URL}/conversation/podcast/stream?topic=${encodeURIComponent(topic)}`;
};

export default api;
```

### 7.4 Create Components

#### UploadPDF.jsx
Create `frontend/src/components/UploadPDF.jsx`:
```jsx
import { useState } from 'react';
import { uploadPDF } from '../api';

export default function UploadPDF({ onUploadSuccess }) {
  const [uploading, setUploading] = useState(false);
  const [status, setStatus] = useState('');

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setUploading(true);
    setStatus('Uploading and processing...');

    try {
      const result = await uploadPDF(file);
      setStatus(`Success! Indexed ${result.chunks_indexed} chunks.`);
      onUploadSuccess?.(result);
    } catch (error) {
      setStatus(`Error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <h3>📄 Upload PDF</h3>
      <input 
        type="file" 
        accept=".pdf" 
        onChange={handleUpload} 
        disabled={uploading}
      />
      {status && <p className="status">{status}</p>}
    </div>
  );
}
```

#### ChatMessage.jsx
Create `frontend/src/components/ChatMessage.jsx`:
```jsx
export default function ChatMessage({ role, content, audioBase64 }) {
  const roleLabels = {
    curious: '🎤 Curious Host',
    explainer: '🎓 Expert Host',
    user: '👤 You'
  };

  const playAudio = () => {
    if (audioBase64) {
      const audio = new Audio(`data:audio/mp3;base64,${audioBase64}`);
      audio.play();
    }
  };

  return (
    <div className={`message ${role}`}>
      <div className="message-header">
        <span className="role">{roleLabels[role] || role}</span>
        {audioBase64 && (
          <button onClick={playAudio} className="play-btn">🔊 Play</button>
        )}
      </div>
      <div className="message-content">{content}</div>
    </div>
  );
}
```

#### PodcastPlayer.jsx
Create `frontend/src/components/PodcastPlayer.jsx`:
```jsx
import { useState } from 'react';
import { generatePodcastWithAudio } from '../api';
import ChatMessage from './ChatMessage';

export default function PodcastPlayer() {
  const [conversation, setConversation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [topic, setTopic] = useState('overview');

  const generateTurn = async () => {
    setLoading(true);
    try {
      const result = await generatePodcastWithAudio(topic);
      setConversation(result);
    } catch (error) {
      console.error('Error generating podcast:', error);
    } finally {
      setLoading(false);
    }
  };

  const playAll = () => {
    if (!conversation) return;
    
    const audios = [
      conversation.curious_audio,
      conversation.explainer_audio
    ].filter(Boolean);

    let index = 0;
    const playNext = () => {
      if (index < audios.length) {
        const audio = new Audio(`data:audio/mp3;base64,${audios[index]}`);
        audio.onended = () => {
          index++;
          playNext();
        };
        audio.play();
      }
    };
    playNext();
  };

  return (
    <div className="podcast-player">
      <h3>🎙️ AI Podcast</h3>
      
      <div className="controls">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Topic (e.g., overview, main concepts)"
        />
        <button onClick={generateTurn} disabled={loading}>
          {loading ? 'Generating...' : '▶️ Generate Turn'}
        </button>
        {conversation && (
          <button onClick={playAll}>🔊 Play All</button>
        )}
      </div>

      {conversation && (
        <div className="conversation">
          <ChatMessage 
            role="curious" 
            content={conversation.curious}
            audioBase64={conversation.curious_audio}
          />
          <ChatMessage 
            role="explainer" 
            content={conversation.explainer}
            audioBase64={conversation.explainer_audio}
          />
        </div>
      )}
    </div>
  );
}
```

#### AudioPlayer.jsx
Create `frontend/src/components/AudioPlayer.jsx`:
```jsx
import { useState, useRef } from 'react';

export default function AudioPlayer({ audioBase64, label }) {
  const [playing, setPlaying] = useState(false);
  const audioRef = useRef(null);

  const togglePlay = () => {
    if (!audioRef.current) {
      audioRef.current = new Audio(`data:audio/mp3;base64,${audioBase64}`);
      audioRef.current.onended = () => setPlaying(false);
    }

    if (playing) {
      audioRef.current.pause();
      setPlaying(false);
    } else {
      audioRef.current.play();
      setPlaying(true);
    }
  };

  return (
    <button onClick={togglePlay} className="audio-player">
      {playing ? '⏸️' : '▶️'} {label}
    </button>
  );
}
```

### 7.5 Create Main App
Create `frontend/src/App.jsx`:
```jsx
import { useState } from 'react';
import UploadPDF from './components/UploadPDF';
import PodcastPlayer from './components/PodcastPlayer';
import ChatMessage from './components/ChatMessage';
import { askQuestion } from './api';
import './App.css';

function App() {
  const [pdfUploaded, setPdfUploaded] = useState(false);
  const [question, setQuestion] = useState('');
  const [chat, setChat] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleAsk = async (e) => {
    e.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setChat(prev => [...prev, { role: 'user', content: question }]);

    try {
      const result = await askQuestion(question);
      setChat(prev => [...prev, { role: 'explainer', content: result.explainer }]);
    } catch (error) {
      setChat(prev => [...prev, { role: 'error', content: error.message }]);
    } finally {
      setLoading(false);
      setQuestion('');
    }
  };

  return (
    <div className="app">
      <header>
        <h1>🎙️ Voice RAG Podcast</h1>
        <p>Upload a PDF and let AI hosts discuss it!</p>
      </header>

      <main>
        <section className="sidebar">
          <UploadPDF onUploadSuccess={() => setPdfUploaded(true)} />
          
          {pdfUploaded && (
            <div className="status-badge">✅ PDF Ready</div>
          )}
        </section>

        <section className="content">
          <PodcastPlayer />

          <div className="user-chat">
            <h3>💬 Ask a Question</h3>
            <div className="chat-messages">
              {chat.map((msg, i) => (
                <ChatMessage key={i} role={msg.role} content={msg.content} />
              ))}
            </div>
            
            <form onSubmit={handleAsk} className="chat-input">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Ask about the document..."
                disabled={loading}
              />
              <button type="submit" disabled={loading}>
                {loading ? '...' : 'Ask'}
              </button>
            </form>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
```

### 7.6 Add Styles
Create `frontend/src/App.css`:
```css
* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #0f0f0f;
  color: #e0e0e0;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

header {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 2rem;
  text-align: center;
  border-bottom: 1px solid #333;
}

header h1 {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

header p {
  color: #888;
}

main {
  display: grid;
  grid-template-columns: 300px 1fr;
  flex: 1;
}

.sidebar {
  background: #1a1a1a;
  padding: 1.5rem;
  border-right: 1px solid #333;
}

.content {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Upload Section */
.upload-section {
  background: #252525;
  padding: 1.5rem;
  border-radius: 8px;
}

.upload-section input[type="file"] {
  margin-top: 1rem;
}

.status {
  margin-top: 0.5rem;
  font-size: 0.9rem;
  color: #4ade80;
}

.status-badge {
  background: #166534;
  color: #4ade80;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  margin-top: 1rem;
  text-align: center;
}

/* Podcast Player */
.podcast-player {
  background: #1a1a2e;
  padding: 1.5rem;
  border-radius: 8px;
}

.controls {
  display: flex;
  gap: 0.5rem;
  margin: 1rem 0;
}

.controls input {
  flex: 1;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #333;
  background: #252525;
  color: #e0e0e0;
}

button {
  padding: 0.75rem 1.5rem;
  border-radius: 4px;
  border: none;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  font-weight: 500;
}

button:hover {
  background: #2563eb;
}

button:disabled {
  background: #555;
  cursor: not-allowed;
}

/* Messages */
.conversation, .chat-messages {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.message {
  padding: 1rem;
  border-radius: 8px;
  background: #252525;
}

.message.curious {
  background: #1e3a5f;
  border-left: 3px solid #3b82f6;
}

.message.explainer {
  background: #1e3e2e;
  border-left: 3px solid #4ade80;
}

.message.user {
  background: #3d3d3d;
  border-left: 3px solid #f59e0b;
}

.message-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.role {
  font-weight: 600;
  font-size: 0.9rem;
}

.play-btn {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.message-content {
  line-height: 1.6;
  white-space: pre-wrap;
}

/* User Chat */
.user-chat {
  background: #1a1a1a;
  padding: 1.5rem;
  border-radius: 8px;
}

.chat-input {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.chat-input input {
  flex: 1;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #333;
  background: #252525;
  color: #e0e0e0;
}

/* Responsive */
@media (max-width: 768px) {
  main {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    border-right: none;
    border-bottom: 1px solid #333;
  }
}
```

### 7.7 Configure Vite
Create `frontend/vite.config.js`:
```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: true
  }
});
```

### 7.8 Environment Variables
Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

For production, create `frontend/.env.production`:
```env
VITE_API_URL=https://your-api-domain.com
```

### 7.9 Update Backend for CORS
Update `app/main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.conversation import router as conversation_router
from app.api.upload import router as upload_router

app = FastAPI(title="Voice RAG Podcast")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://your-frontend-domain.com"  # Add production URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])

@app.get("/")
def health():
    return {"status": "ok"}
```

### 7.10 Run Frontend Locally
```bash
cd frontend
npm run dev
# Opens at http://localhost:3000
```

---

## Phase 8: Local Development

### 7.1 Run the Server
```bash
# Start Qdrant (if using Docker)
docker run -p 6333:6333 -v ./qdrant_storage:/qdrant/storage qdrant/qdrant

# In another terminal, start FastAPI
uvicorn app.main:app --reload --port 8000
```

### 7.2 Test Endpoints
```bash
# Health check
curl http://localhost:8000/

# Upload PDF
curl -X POST -F "file=@sample.pdf" http://localhost:8000/upload/

# Ask question
curl -X POST http://localhost:8000/conversation/ \
  -H "Content-Type: application/json" \
  -d '{"question": "What is this document about?"}'

# Generate podcast turn
curl -X POST http://localhost:8000/conversation/podcast \
  -H "Content-Type: application/json" \
  -d '{}'
```

---

## Phase 9: Deployment

### Option A: Docker Compose (Full Stack - Recommended)

#### 9A.1 Create Backend Dockerfile
Create `Dockerfile` in root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 9A.2 Create Frontend Dockerfile
Create `frontend/Dockerfile`:
```dockerfile
# Build stage
FROM node:20-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# Production stage
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### 9A.3 Create Nginx Config
Create `frontend/nginx.conf`:
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # Handle SPA routing
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Gzip compression
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml;
}
```

#### 9A.4 Create docker-compose.yml
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage
    restart: unless-stopped

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - QDRANT_HOST=qdrant
    depends_on:
      - qdrant
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      args:
        - VITE_API_URL=http://localhost:8000
    ports:
      - "3000:80"
    depends_on:
      - api
    restart: unless-stopped

volumes:
  qdrant_data:
```

#### 9A.5 Create .env file for Docker
```env
GEMINI_API_KEY=your_gemini_api_key
ELEVENLABS_API_KEY=your_elevenlabs_api_key
```

#### 9A.6 Update Qdrant Client for Docker
Update `app/rag/qdrant_client.py`:
```python
import os
from qdrant_client import QdrantClient

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
client = QdrantClient(host=QDRANT_HOST, port=6333)
```

#### 9A.7 Deploy Locally with Docker
```bash
# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Access:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - Qdrant: http://localhost:6333
```

#### 9A.8 Production docker-compose.prod.yml
```yaml
version: '3.8'

services:
  qdrant:
    image: qdrant/qdrant:latest
    volumes:
      - qdrant_data:/qdrant/storage
    restart: always
    # No ports exposed - internal only

  api:
    build: .
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - ELEVENLABS_API_KEY=${ELEVENLABS_API_KEY}
      - QDRANT_HOST=qdrant
    depends_on:
      - qdrant
    restart: always

  frontend:
    build:
      context: ./frontend
      args:
        - VITE_API_URL=https://api.yourdomain.com
    depends_on:
      - api
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - frontend
      - api
    restart: always

volumes:
  qdrant_data:
```

---

### Option B: Google Cloud Run + Firebase Hosting

#### 9B.1 Backend: Create cloudbuild.yaml
```yaml
steps:
  # Build and push API image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/voice-rag-api', '.']
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/voice-rag-api']
  
  # Deploy API to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'run'
      - 'deploy'
      - 'voice-rag-api'
      - '--image=gcr.io/$PROJECT_ID/voice-rag-api'
      - '--region=us-central1'
      - '--platform=managed'
      - '--allow-unauthenticated'
      - '--memory=1Gi'
      - '--set-env-vars=GEMINI_API_KEY=${_GEMINI_API_KEY},ELEVENLABS_API_KEY=${_ELEVENLABS_API_KEY},QDRANT_URL=${_QDRANT_URL},QDRANT_API_KEY=${_QDRANT_API_KEY}'
```

#### 9B.2 Use Qdrant Cloud
1. Create account at https://cloud.qdrant.io
2. Create cluster, get URL and API key
3. Update `app/rag/qdrant_client.py`:
```python
import os
from qdrant_client import QdrantClient

QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)
```

#### 9B.3 Deploy Backend
```bash
gcloud builds submit --config cloudbuild.yaml \
  --substitutions=_GEMINI_API_KEY="your-key",_ELEVENLABS_API_KEY="your-key",_QDRANT_URL="your-url",_QDRANT_API_KEY="your-key"
```

#### 9B.4 Frontend: Firebase Hosting Setup
```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login and init
firebase login
firebase init hosting

# Select: Create a new project or use existing
# Public directory: dist
# Single-page app: Yes
# Automatic builds: No
```

#### 9B.5 Create firebase.json
```json
{
  "hosting": {
    "public": "dist",
    "ignore": ["firebase.json", "**/.*", "**/node_modules/**"],
    "rewrites": [
      {
        "source": "**",
        "destination": "/index.html"
      }
    ],
    "headers": [
      {
        "source": "**/*.@(js|css)",
        "headers": [
          {
            "key": "Cache-Control",
            "value": "max-age=31536000"
          }
        ]
      }
    ]
  }
}
```

#### 9B.6 Deploy Frontend to Firebase
```bash
cd frontend

# Set production API URL
echo "VITE_API_URL=https://voice-rag-api-xxxxx-uc.a.run.app" > .env.production

# Build
npm run build

# Deploy
firebase deploy --only hosting
```

---

### Option C: Vercel (Frontend) + Railway (Backend)

#### 9C.1 Backend on Railway
1. Connect GitHub repo to Railway
2. Set root directory to `/` (for backend)
3. Add environment variables:
   - `GEMINI_API_KEY`
   - `ELEVENLABS_API_KEY`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
4. Railway auto-detects Python and deploys

#### 9C.2 Frontend on Vercel

Create `frontend/vercel.json`:
```json
{
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "framework": "vite",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Deploy:
```bash
cd frontend

# Install Vercel CLI
npm i -g vercel

# Deploy
vercel

# Set environment variable in Vercel dashboard:
# VITE_API_URL = https://your-railway-api.up.railway.app
```

---

### Option D: Render (Full Stack)

#### 9D.1 Create render.yaml
```yaml
services:
  # Backend API
  - type: web
    name: voice-rag-api
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: GEMINI_API_KEY
        sync: false
      - key: ELEVENLABS_API_KEY
        sync: false
      - key: QDRANT_URL
        sync: false
      - key: QDRANT_API_KEY
        sync: false
    healthCheckPath: /

  # Frontend
  - type: web
    name: voice-rag-frontend
    env: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: frontend/dist
    envVars:
      - key: VITE_API_URL
        value: https://voice-rag-api.onrender.com
    routes:
      - type: rewrite
        source: /*
        destination: /index.html
```

#### 9D.2 Deploy on Render
1. Connect GitHub repo to Render
2. Render auto-detects `render.yaml`
3. Add secret environment variables in dashboard
4. Deploy

---

### Option E: AWS (ECS + S3/CloudFront)

#### 9E.1 Backend: ECS Task Definition
```json
{
  "family": "voice-rag-api",
  "containerDefinitions": [
    {
      "name": "api",
      "image": "your-ecr-repo/voice-rag-api:latest",
      "portMappings": [
        { "containerPort": 8000, "protocol": "tcp" }
      ],
      "environment": [
        { "name": "QDRANT_HOST", "value": "qdrant" }
      ],
      "secrets": [
        { "name": "GEMINI_API_KEY", "valueFrom": "arn:aws:secretsmanager:..." },
        { "name": "ELEVENLABS_API_KEY", "valueFrom": "arn:aws:secretsmanager:..." }
      ]
    }
  ]
}
```

#### 9E.2 Frontend: S3 + CloudFront
```bash
cd frontend
npm run build

# Create S3 bucket
aws s3 mb s3://voice-rag-frontend

# Sync build files
aws s3 sync dist/ s3://voice-rag-frontend --delete

# Create CloudFront distribution pointing to S3
aws cloudfront create-distribution --origin-domain-name voice-rag-frontend.s3.amazonaws.com
```

---

## Phase 10: Production Checklist

### Security
- [ ] Store secrets in environment variables / secret manager
- [ ] Add rate limiting
- [ ] Add authentication (API keys or OAuth)
- [ ] Enable CORS properly

### Performance
- [ ] Add Redis caching for embeddings
- [ ] Use async Qdrant client
- [ ] Add connection pooling

### Monitoring
- [ ] Add logging (structlog or loguru)
- [ ] Add health checks
- [ ] Set up error tracking (Sentry)
- [ ] Add metrics (Prometheus)

### CI/CD
- [ ] GitHub Actions for tests
- [ ] Auto-deploy on main branch
- [ ] Staging environment

---

## Quick Start Summary

### Option 1: Docker (Recommended)
```bash
# 1. Clone
git clone <repo>
cd voice-rag-podcast

# 2. Configure
cp .env.example .env
# Edit .env with your API keys

# 3. Start everything
docker-compose up --build

# 4. Access
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

### Option 2: Manual Setup
```bash
# 1. Clone and setup backend
git clone <repo>
cd voice-rag-podcast
python -m venv .venv
.venv\Scripts\activate  # Windows
pip install -r requirements.txt

# 2. Configure
echo "GEMINI_API_KEY=your_key" > .env
echo "ELEVENLABS_API_KEY=your_key" >> .env

# 3. Start Qdrant
docker run -p 6333:6333 qdrant/qdrant

# 4. Ingest PDF
python -m app.rag.ingest

# 5. Run backend
uvicorn app.main:app --reload --port 8000

# 6. Setup frontend (new terminal)
cd frontend
npm install
echo "VITE_API_URL=http://localhost:8000" > .env
npm run dev

# 7. Access
# Frontend: http://localhost:3000
# API: http://localhost:8000
```

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/upload/` | POST | Upload PDF (multipart form) |
| `/conversation/` | POST | User asks a question |
| `/conversation/ask` | POST | Explicit user question endpoint |
| `/conversation/podcast` | POST | Generate AI podcast turn |
| `/conversation/podcast/audio` | POST | Podcast with separate audio per host |
| `/conversation/podcast/audio/combined` | POST | Podcast with single combined audio |
| `/conversation/podcast/stream` | POST | Stream podcast audio |

---

## Frontend Routes

| Route | Description |
|-------|-------------|
| `/` | Main app - upload PDF, generate podcast, ask questions |

---

## Project Structure (Complete)

```
voice-rag-podcast/
├── app/
│   ├── agents/
│   │   ├── controller.py
│   │   ├── curious_agent.py
│   │   └── explainer_agent.py
│   ├── api/
│   │   ├── conversation.py
│   │   └── upload.py
│   ├── rag/
│   │   ├── chunking.py
│   │   ├── embeddings.py
│   │   ├── ingest.py
│   │   ├── qdrant_client.py
│   │   ├── retriever.py
│   │   └── vectorstore.py
│   ├── services/
│   │   ├── llm.py
│   │   └── tts.py
│   ├── config.py
│   └── main.py
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── AudioPlayer.jsx
│   │   │   ├── ChatMessage.jsx
│   │   │   ├── PodcastPlayer.jsx
│   │   │   └── UploadPDF.jsx
│   │   ├── api.js
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── vite.config.js
├── tests/
│   └── test_api.py
├── .env
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── sample.pdf
└── README.md
```