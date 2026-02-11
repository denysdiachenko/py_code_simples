from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.services.ai_mock import analyze_with_ai_mock
from app.services.pdf_validator import extract_pdf_text, validate_invoice_document

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

    ai_result = analyze_with_ai_mock(extracted_text)

    return {
        "message": "Document is valid and accepted for AI analysis.",
        "filename": file.filename,
        "validation": validation,
        "ai_analysis": ai_result,
    }
