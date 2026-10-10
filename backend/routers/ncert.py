from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.routers.ncert_data import NCERT_CURRICULUM, GRADE_OPTIONS, AGE_GROUPS
from backend.services.pdf_service import pdf_service

router = APIRouter(prefix="/api/ncert", tags=["ncert"])

class FetchUrlRequest(BaseModel):
    url: str

@router.get("/lessons")
def get_curated_lessons():
    return {"lessons": NCERT_CURRICULUM}

@router.get("/options")
def get_grade_options():
    return {
        "grades": GRADE_OPTIONS,
        "age_groups": AGE_GROUPS
    }

@router.post("/upload-pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    try:
        content = await file.read()
        extracted_text = pdf_service.extract_text_from_bytes(content)
        return {
            "filename": file.filename,
            "text_length": len(extracted_text),
            "text": extracted_text[:20000] # Cap text extract for initial outline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process PDF: {str(e)}")

@router.post("/fetch-url")
async def fetch_pdf_url(req: FetchUrlRequest):
    try:
        extracted_text = await pdf_service.extract_text_from_url(req.url)
        return {
            "url": req.url,
            "text_length": len(extracted_text),
            "text": extracted_text[:20000]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch PDF from URL: {str(e)}")
