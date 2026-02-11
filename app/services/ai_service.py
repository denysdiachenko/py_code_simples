import json
import os
from typing import Any

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)

from app.services.ai_mock import analyze_with_ai_mock


INVOICE_JSON_SCHEMA: dict[str, Any] = {
    "name": "invoice_analysis",
    "strict": True,
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "is_invoice": {"type": "boolean"},
            "document_type": {"type": "string"},
            "invoice_number": {"type": ["string", "null"]},
            "invoice_date": {"type": ["string", "null"]},
            "due_date": {"type": ["string", "null"]},
            "vendor_name": {"type": ["string", "null"]},
            "customer_name": {"type": ["string", "null"]},
            "currency": {"type": ["string", "null"]},
            "total_amount": {"type": ["number", "null"]},
            "subtotal_amount": {"type": ["number", "null"]},
            "tax_amount": {"type": ["number", "null"]},
            "payment_terms": {"type": ["string", "null"]},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": ["number", "null"]},
                        "unit_price": {"type": ["number", "null"]},
                        "line_total": {"type": ["number", "null"]},
                    },
                    "required": ["description", "quantity", "unit_price", "line_total"],
                },
            },
            "confidence": {"type": "number"},
        },
        "required": [
            "is_invoice",
            "document_type",
            "invoice_number",
            "invoice_date",
            "due_date",
            "vendor_name",
            "customer_name",
            "currency",
            "total_amount",
            "subtotal_amount",
            "tax_amount",
            "payment_terms",
            "line_items",
            "confidence",
        ],
    },
}


REQUIRED_RESULT_KEYS = [
    "is_invoice",
    "document_type",
    "invoice_number",
    "invoice_date",
    "due_date",
    "vendor_name",
    "customer_name",
    "currency",
    "total_amount",
    "subtotal_amount",
    "tax_amount",
    "payment_terms",
    "line_items",
    "confidence",
]


def _extract_output_text(response: Any) -> str:
    output_text = getattr(response, "output_text", None)
    if output_text:
        return output_text

    outputs = getattr(response, "output", None) or []
    parts: list[str] = []
    for item in outputs:
        content_items = getattr(item, "content", None) or []
        for content in content_items:
            text_value = getattr(content, "text", None)
            if text_value:
                parts.append(text_value)
    return "\n".join(parts).strip()


def _extract_chat_completion_text(response: Any) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        return ""
    first = choices[0]
    message = getattr(first, "message", None)
    if not message:
        return ""
    content = getattr(message, "content", None)
    return content or ""


def _build_input_payload(extracted_text: str) -> list[dict[str, Any]]:
    truncated = extracted_text[:12000]
    return [
        {
            "role": "system",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "You extract invoice data from OCR text. "
                        "Return only valid JSON."
                    ),
                }
            ],
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text": (
                        "Analyze this invoice-like document text and extract fields.\n\n"
                        f"{truncated}"
                    ),
                }
            ],
        },
    ]


def _coerce_invoice_json(data: dict[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "is_invoice": False,
        "document_type": "unknown",
        "invoice_number": None,
        "invoice_date": None,
        "due_date": None,
        "vendor_name": None,
        "customer_name": None,
        "currency": None,
        "total_amount": None,
        "subtotal_amount": None,
        "tax_amount": None,
        "payment_terms": None,
        "line_items": [],
        "confidence": 0.0,
    }
    for key in REQUIRED_RESULT_KEYS:
        if key in data:
            defaults[key] = data[key]
    return defaults


def _analyze_with_chat_completions(client: OpenAI, model: str, extracted_text: str) -> dict[str, Any]:
    truncated = extracted_text[:12000]
    completion = client.chat.completions.create(
        model=model,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract invoice data from OCR text and return a JSON object. "
                    f"Required keys: {', '.join(REQUIRED_RESULT_KEYS)}. "
                    "Use null for unknown values."
                ),
            },
            {
                "role": "user",
                "content": f"Analyze this invoice-like document text and extract fields:\n\n{truncated}",
            },
        ],
    )
    raw_json_text = _extract_chat_completion_text(completion)
    if not raw_json_text:
        raise ValueError("AI returned an empty response.")

    try:
        parsed = json.loads(raw_json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI returned invalid JSON: {raw_json_text[:240]}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("AI JSON response must be an object.")
    return _coerce_invoice_json(parsed)


def analyze_invoice_with_ai(extracted_text: str) -> dict:
    api_key = os.getenv("OPENAI_API_KEY")
    model = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    use_mock_fallback = os.getenv("USE_MOCK_AI_FALLBACK", "1") == "1"

    if not api_key:
        if use_mock_fallback:
            mock_result = analyze_with_ai_mock(extracted_text)
            mock_result["note"] = "OPENAI_API_KEY is not set, fallback to mock mode."
            return mock_result
        raise ValueError("OPENAI_API_KEY is not set.")

    client = OpenAI(api_key=api_key)

    # Backward compatibility: older SDKs may not provide `client.responses`.
    if not hasattr(client, "responses"):
        result = _analyze_with_chat_completions(client, model, extracted_text)
        return {
            "status": "ok",
            "provider": "openai",
            "model": model,
            "api_mode": "chat_completions_fallback",
            "result": result,
        }

    input_payload = _build_input_payload(extracted_text)

    try:
        response = client.responses.create(
            model=model,
            input=input_payload,
            text={"format": {"type": "json_schema", "json_schema": INVOICE_JSON_SCHEMA}},
        )
    except BadRequestError:
        # Fallback for environments/models that reject strict schema config.
        response = client.responses.create(
            model=model,
            input=input_payload
            + [
                {
                    "role": "developer",
                    "content": [
                        {
                            "type": "input_text",
                            "text": (
                                "Return a single JSON object with keys: "
                                + ", ".join(REQUIRED_RESULT_KEYS)
                                + ". Use null for unknown values."
                            ),
                        }
                    ],
                }
            ],
            text={"format": {"type": "json_object"}},
        )
    except AuthenticationError as exc:
        raise ValueError(f"OpenAI authentication failed: {str(exc)}") from exc
    except RateLimitError as exc:
        raise RuntimeError(f"OpenAI rate limit reached: {str(exc)}") from exc
    except (APIConnectionError, APITimeoutError) as exc:
        raise RuntimeError(f"OpenAI connection error: {str(exc)}") from exc
    except APIStatusError as exc:
        raise RuntimeError(
            f"OpenAI API error ({exc.status_code}): {str(exc)}"
        ) from exc

    raw_json_text = _extract_output_text(response)
    if not raw_json_text:
        raise ValueError("AI returned an empty response.")

    cleaned = raw_json_text.strip().removeprefix("```json").removesuffix("```").strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"AI returned invalid JSON: {cleaned[:240]}") from exc

    if not isinstance(parsed, dict):
        raise ValueError("AI JSON response must be an object.")

    return {
        "status": "ok",
        "provider": "openai",
        "model": model,
        "result": _coerce_invoice_json(parsed),
    }
