from app.services.pdf_validator import validate_invoice_document


def test_valid_invoice_like_document():
    text = """
    Invoice #INV-2026-001
    Date: 2026-02-10
    Total: 1999.99 USD
    Please complete payment within 7 days.
    """
    result = validate_invoice_document(text)
    assert result["is_valid"] is True


def test_invalid_non_invoice_document():
    text = """
    Meeting notes
    Agenda for project kickoff
    Discussion about timelines and scope.
    """
    result = validate_invoice_document(text)
    assert result["is_valid"] is False
