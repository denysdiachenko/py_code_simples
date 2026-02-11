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


async def _process_invoice_file(file: UploadFile) -> dict:
    filename = file.filename or "unknown_file"
    if not filename.lower().endswith(".pdf"):
        return {
            "status": "invalid",
            "filename": filename,
            "reason": "Only PDF files are supported.",
        }

    file_content = await file.read()
    if not file_content:
        return {
            "status": "invalid",
            "filename": filename,
            "reason": "Uploaded file is empty.",
        }

    try:
        extracted_text = extract_pdf_text(file_content)
    except ValueError as exc:
        return {
            "status": "invalid",
            "filename": filename,
            "reason": str(exc),
        }

    validation = validate_invoice_document(extracted_text)
    if not validation["is_valid"]:
        return {
            "status": "invalid",
            "filename": filename,
            "reason": validation["reason"],
            "validation": validation,
        }

    try:
        ai_result = await asyncio.to_thread(analyze_invoice_with_ai, extracted_text)
    except ValueError as exc:
        return {
            "status": "invalid",
            "filename": filename,
            "reason": f"AI configuration error: {str(exc)}",
            "validation": validation,
        }
    except Exception as exc:
        return {
            "status": "invalid",
            "filename": filename,
            "reason": f"AI analysis failed: {str(exc)}",
            "validation": validation,
        }

    return {
        "status": "valid",
        "filename": filename,
        "validation": validation,
        "ai_analysis": ai_result,
    }


@app.post("/api/upload-invoices")
async def upload_invoices(files: list[UploadFile] = File(...)) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded.")

    analyzed_invoices: list[dict] = []
    invalid_files: list[dict] = []

    for file in files:
        result = await _process_invoice_file(file)
        if result["status"] == "valid":
            analyzed_invoices.append(result)
        else:
            invalid_files.append(result)

    return {
        "message": "Batch processing completed.",
        "summary": {
            "total_files": len(files),
            "valid_invoices": len(analyzed_invoices),
            "invalid_files": len(invalid_files),
        },
        "analyzed_invoices": analyzed_invoices,
        "invalid_files": invalid_files,
    }


@app.post("/api/upload-invoice")
async def upload_invoice(file: UploadFile = File(...)) -> dict:
    result = await _process_invoice_file(file)
    if result["status"] != "valid":
        raise HTTPException(status_code=422, detail=result["reason"])
    return {
        "message": "Document is valid and accepted for AI analysis.",
        "filename": result["filename"],
        "validation": result["validation"],
        "ai_analysis": result["ai_analysis"],
    }
