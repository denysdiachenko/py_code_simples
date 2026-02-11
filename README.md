# PDF Invoice Validator (Python, UI + BE)

A small Python fullstack project:
- `UI`: web page for PDF upload.
- `BE`: FastAPI endpoint that validates PDF content, checks if it looks like an invoice/bill, and sends it to mocked AI analysis.

## Implemented Features
1. PDF upload through UI.
2. Backend file handling (`multipart/form-data`).
3. PDF text extraction (`pypdf`).
4. Invoice/bill validation with heuristic rules.
5. If valid: calls a mock AI analysis function (placeholder for real integration).
6. If invalid: returns an error.

## Project Structure
```text
app/
  main.py
  services/
    ai_mock.py
    pdf_validator.py
  static/
    index.html
    styles.css
    app.js
tests/
  test_pdf_validator.py
requirements.txt
README.md
```

## Run Locally
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open in browser:
- `http://127.0.0.1:8000`

## API
### `POST /api/upload-invoice`
- Form field: `file` (PDF)

Success (`200`):
- document is valid
- returns `validation` + `ai_analysis` (mock)

Errors:
- `400`: not a PDF, empty file, or unreadable PDF
- `422`: document does not look like an invoice/bill

## Validation Logic
A document is considered valid if it gets at least 3 out of 4 signals:
1. At least 2 invoice-related keywords (`invoice`, `bill`, `total`, `amount due`, ...)
2. Amount pattern is present (`total`, `amount`, `amount due` + number)
3. Document number pattern is present (`Invoice #...`, `Bill No...`)
4. Date pattern is present (`dd.mm.yyyy`, `yyyy-mm-dd`, ...)

## Where to Replace Mock AI with Real Integration
File:
- `app/services/ai_mock.py`

Function:
- `analyze_with_ai_mock(extracted_text: str)`

Replace this function with a real external AI provider call (OpenAI, Azure OpenAI, etc.).

## Tests
Basic validator tests are included:
- `tests/test_pdf_validator.py`

Run tests:
```bash
python3 -m pytest -q
```

Note: in this environment, `pytest` was not installed, so tests were not executed here.
