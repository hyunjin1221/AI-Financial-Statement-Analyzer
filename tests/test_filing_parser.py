from app.services.filing_parser import extract_sections, extract_sections_with_spans, filing_to_text


def test_extract_sections_10k() -> None:
    sample = """
    <html><body>
    Item 1 Business We sell products globally.
    Item 1A Risk Factors Our business is exposed to supply chain volatility.
    Item 7 Management's Discussion and Analysis Revenue grew year over year.
    Item 8 Financial Statements and Supplementary Data
    </body></html>
    """
    text = filing_to_text(sample)
    sections = extract_sections(text, "10-K")

    assert "business" in sections
    assert "risk_factors" in sections
    assert "mda" in sections
    assert "Revenue grew year over year." in sections["mda"]


def test_extract_sections_10q() -> None:
    sample = """
    PART I ITEM 2 Management's Discussion and Analysis of Financial Condition and Results of Operations
    Quarterly results improved.
    PART II ITEM 1A Risk Factors Inflation and customer concentration may affect results.
    PART II ITEM 6 Exhibits
    """
    sections = extract_sections(sample, "10-Q")

    assert "mda" in sections
    assert "risk_factors" in sections
    assert "Quarterly results improved." in sections["mda"]


def test_extract_sections_with_spans() -> None:
    sample = "Item 1 Business Text. Item 1A Risk Factors Text. Item 7 MD&A Text. Item 8 Financials."
    records = extract_sections_with_spans(sample, "10-K")
    assert "business" in records
    assert isinstance(records["business"]["start"], int)
    assert records["business"]["end"] > records["business"]["start"]
