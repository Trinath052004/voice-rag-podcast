

```language app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.upload import router as upload_router
from app.api.conversation import router as conversation_router

app = FastAPI(title="Voice RAG Podcast")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router, prefix="/upload", tags=["upload"])
app.include_router(conversation_router, prefix="/conversation", tags=["conversation"])







@app.on_event("startup")
async def startup_event():
    print("\nRegistered Routes:")
    for route in app.routes:
        print(f"{route.path} - {route.methods}")

@app.get("/")
def health():
    return {"status": "ok"}
```
