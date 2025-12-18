# Voice RAG Podcast

A voice-based Retrieval-Augmented Generation (RAG) podcast application that creates interactive AI-powered conversations about user-uploaded PDF documents.

## Features

- Upload PDF documents for processing
- AI agents (Curious and Explainer) engage in podcast-style dialogue
- Text-to-speech integration for audio playback
- Web-based interface for easy interaction

## Quick Start

1. Install dependencies: `pip install -r requirements.txt` and `npm install`
2. Start backend: `uvicorn app.main:app --reload`
3. Start frontend: `npm run dev`
4. Visit `http://localhost:3000` to upload PDFs and start conversations

## Requirements

- Python 3.9+
- Node.js 14+
- Google Cloud credentials for Vertex AI
