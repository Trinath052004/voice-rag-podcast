from fastapi import APIRouter, UploadFile, File
from app.rag.ingest import ingest_pdf
import traceback

router = APIRouter()

@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        data = await file.read()
        ingest_pdf(data)
        return {"status": "pdf indexed"}
    except Exception as e:
        print("UPLOAD ERROR:")
        traceback.print_exc()
        raise e

