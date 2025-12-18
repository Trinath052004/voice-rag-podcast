
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.upload import router as upload_router
from app.api.conversation import router as conversation_router
import logging
import os
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    logging.info("Starting up the application")
    print("\nRegistered Routes:")
    for route in app.routes:
        print(f"{route.path} - {route.methods}")
    yield
    # Shutdown logic (if needed):app
    logging.info("Shutting down the application")


app = FastAPI(title="Voice RAG Podcast", lifespan=lifespan)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# CORS for frontend
if os.getenv("ENVIRONMENT") == "development":
    allow_origins = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]
else:
    # Configure allowed origins for production
    # Replace with your actual production domain(s)
    allow_origins = ["https://your-production-domain.com"]  # Update this

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])


@app.get("/")
def health():
    return {"status": "ok"}
