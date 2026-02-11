# PDF Invoice Validator (Python, UI + BE)

A Python fullstack project:
- `UI`: web page for PDF upload.
- `BE`: FastAPI endpoint that validates PDF content, checks if it looks like an invoice/bill, and sends it to AI for JSON extraction.

## AI Agent Recommendation
Recommended agent setup:
- `Provider`: OpenAI
- `API`: Responses API
- `Model`: `gpt-4.1-mini` (good quality/cost for structured extraction)
- `Output mode`: Structured JSON (`json_schema`)

This gives stable machine-readable responses and is easy to integrate with backend pipelines.
Environment variables are auto-loaded from `.env` via `python-dotenv`.

## Implemented Features
1. PDF upload through UI.
2. Backend file handling (`multipart/form-data`).
3. PDF text extraction (`pypdf`).
4. Invoice/bill validation with heuristic rules.
5. Real AI extraction to JSON using OpenAI Responses API.
6. Fallback to mock if API key is missing (configurable).
7. If invalid document: returns an error.

## Project Structure
```text
app/
  main.py
  services/
    ai_mock.py
    ai_service.py
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
cp .env.example .env
# edit .env and set your OPENAI_API_KEY
uvicorn app.main:app --reload
```

Open in browser:
- `http://127.0.0.1:8000`

## How to Connect the AI Agent
1. Create API key in OpenAI platform.
2. Copy `.env.example` to `.env` and set:
   - `OPENAI_API_KEY`
3. (Optional) configure:
   - `OPENAI_MODEL` (default: `gpt-4.1-mini`)
   - `USE_MOCK_AI_FALLBACK` (`1` or `0`)
4. Start the app and upload a PDF.
5. Backend flow:
   - Extract text from PDF
   - Validate invoice-like structure
   - Call `app/services/ai_service.py`
   - Receive strict JSON from model

If you want hard-fail behavior (no fallback), set in `.env`:
```bash
USE_MOCK_AI_FALLBACK=0
```

## API
### `POST /api/upload-invoice`
- Form field: `file` (PDF)

Success (`200`):
- document is valid
- returns `validation` + `ai_analysis` (structured JSON)

Errors:
- `400`: not a PDF, empty file, or unreadable PDF
- `422`: document does not look like an invoice/bill
- `500`: missing AI configuration (when fallback disabled)
- `502`: upstream AI call failed

## Troubleshooting `502 Bad Gateway`
If `POST /api/upload-invoice` returns `502`, the app reached AI step but upstream call failed.

Common causes:
1. Invalid or missing `OPENAI_API_KEY`
2. Network/timeout issue when calling OpenAI
3. Rate limits on the API key/project
4. Model access issue for `OPENAI_MODEL`

Quick checks:
1. Confirm `.env` exists and contains `OPENAI_API_KEY=...`
2. Restart server after `.env` changes
3. Temporarily set fallback mode:
   - `USE_MOCK_AI_FALLBACK=1`
4. Try explicit model:
   - `OPENAI_MODEL=gpt-4.1-mini`

## Validation Logic
A document is considered valid if it gets at least 3 out of 4 signals:
1. At least 2 invoice-related keywords (`invoice`, `bill`, `total`, `amount due`, ...)
2. Amount pattern is present (`total`, `amount`, `amount due` + number)
3. Document number pattern is present (`Invoice #...`, `Bill No...`)
4. Date pattern is present (`dd.mm.yyyy`, `yyyy-mm-dd`, ...)

## Tests
Basic validator tests are included:
- `tests/test_pdf_validator.py`

Run tests:
```bash
python3 -m pytest -q
```
