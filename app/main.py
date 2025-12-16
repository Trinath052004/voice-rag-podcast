from fastapi import FastAPI
#from app.api.upload import router as upload_router
from app.api.conversation import router as conversation_router

app = FastAPI()

#app.include_router(upload_router)
app.include_router(conversation_router, prefix="/conversation")

@app.get("/")
def health():
    return {"status": "ok"}
