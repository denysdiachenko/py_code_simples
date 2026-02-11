import re
from io import BytesIO

from pypdf import PdfReader

INVOICE_KEYWORDS = (
    "invoice",
    "bill",
    "receipt",
    "payment",
    "amount due",
    "total",
)

AMOUNT_PATTERNS = (
    r"\btotal\b\s*[:\-]?\s*[\d\s,.]+",
    r"\bamount\b\s*[:\-]?\s*[\d\s,.]+",
    r"\bamount due\b\s*[:\-]?\s*[\d\s,.]+",
)

DOC_NUMBER_PATTERNS = (
    r"\binvoice\s*(no|number|#)?\s*[:\-]?\s*[a-z0-9\-/]+",
    r"\bbill\s*(no|number|#)?\s*[:\-]?\s*[a-z0-9\-/]+",
)

DATE_PATTERNS = (
    r"\b\d{2}[./-]\d{2}[./-]\d{4}\b",
    r"\b\d{4}[./-]\d{2}[./-]\d{2}\b",
)


def extract_pdf_text(file_content: bytes) -> str:
    try:
        reader = PdfReader(BytesIO(file_content))
    except Exception as exc:
        raise ValueError("Unable to read PDF file.") from exc

    if len(reader.pages) == 0:
        raise ValueError("PDF file has no pages.")

    chunks: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        chunks.append(text)

    full_text = "\n".join(chunks).strip()
    if not full_text:
        raise ValueError("PDF contains no readable text.")

    return full_text


def _contains_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def validate_invoice_document(text: str) -> dict:
    normalized = " ".join(text.split())
    lowered = normalized.lower()

    keyword_hits = sum(1 for keyword in INVOICE_KEYWORDS if keyword in lowered)
    has_amount = _contains_any_pattern(normalized, AMOUNT_PATTERNS)
    has_doc_number = _contains_any_pattern(normalized, DOC_NUMBER_PATTERNS)
    has_date = _contains_any_pattern(normalized, DATE_PATTERNS)

    score = 0
    if keyword_hits >= 2:
        score += 1
    if has_amount:
        score += 1
    if has_doc_number:
        score += 1
    if has_date:
        score += 1

    if score < 3:
        return {
            "is_valid": False,
            "reason": "Document does not look like an invoice/bill.",
            "signals": {
                "keyword_hits": keyword_hits,
                "has_amount": has_amount,
                "has_doc_number": has_doc_number,
                "has_date": has_date,
                "score": score,
            },
        }

    return {
        "is_valid": True,
        "reason": "Invoice-like structure detected.",
        "signals": {
            "keyword_hits": keyword_hits,
            "has_amount": has_amount,
            "has_doc_number": has_doc_number,
            "has_date": has_date,
            "score": score,
        },
    }
