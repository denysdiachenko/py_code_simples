from pathlib import Path
import asyncio

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from app.services.ai_service import analyze_invoice_with_ai
from app.services.pdf_validator import extract_pdf_text, validate_invoice_document

load_dotenv()

app = FastAPI(title="Invoice PDF Analyzer", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)) -> dict:
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        extracted_text = extract_pdf_text(file_content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    validation = validate_invoice_document(extracted_text)
    if not validation["is_valid"]:
        raise HTTPException(status_code=422, detail=validation["reason"])

    try:
        ai_result = await asyncio.to_thread(analyze_invoice_with_ai, extracted_text)
    except ValueError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"AI analysis failed: {str(exc)}",
        ) from exc

    return {
        "message": "Document is valid and accepted for AI analysis.",
        "filename": file.filename,
        "validation": validation,
        "ai_analysis": ai_result,
    }
