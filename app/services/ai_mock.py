def analyze_with_ai_mock(extracted_text: str) -> dict:
    """Mock AI integration.

    Replace this function with a real external AI call when ready.
    """
    words = extracted_text.split()
    preview = " ".join(words[:40])

    return {
        "status": "mocked",
        "summary": "AI analysis is mocked for now.",
        "preview": preview,
        "todo": "Integrate real AI provider call here.",
    }
