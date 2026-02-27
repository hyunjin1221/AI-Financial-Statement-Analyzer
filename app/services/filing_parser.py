import re
from typing import Dict

from bs4 import BeautifulSoup

from app.utils.text_clean import normalize_whitespace


SECTION_PATTERNS = {
    "10-K": {
        "business": re.compile(r"\bitem\s+1\b(?!\s*a)\b", re.IGNORECASE),
        "risk_factors": re.compile(r"\bitem\s+1a\b", re.IGNORECASE),
        "mda": re.compile(r"\bitem\s+7\b(?!\s*a)\b", re.IGNORECASE),
    },
    "10-Q": {
        "mda": re.compile(r"\bpart\s+i\s+item\s+2\b", re.IGNORECASE),
        "risk_factors": re.compile(r"\bpart\s+ii\s+item\s+1a\b", re.IGNORECASE),
    },
}

GENERIC_BOUNDARY = re.compile(r"\b(?:part\s+[ivx]+[\s,.-]*)?item\s+\d+[a-z]?\b", re.IGNORECASE)


def filing_to_text(raw_filing: str) -> str:
    """Converts filing body to normalized plain text."""
    soup = BeautifulSoup(raw_filing, "lxml")
    text = soup.get_text(" ", strip=True)
    if not text:
        text = raw_filing
    return normalize_whitespace(text)


def extract_sections_with_spans(text: str, form_type: str) -> Dict[str, Dict]:
    """
    Extracts key form sections by heading starts and next item boundary.
    Returns a map of section_name -> extracted text.
    """
    normalized = normalize_whitespace(text)
    patterns = SECTION_PATTERNS.get(form_type.upper(), {})
    if not patterns:
        return {}

    target_positions = {}
    for section_name, pattern in patterns.items():
        match = pattern.search(normalized)
        if match:
            target_positions[section_name] = match.start()

    if not target_positions:
        return {}

    boundaries = sorted({m.start() for m in GENERIC_BOUNDARY.finditer(normalized)} | {len(normalized)})
    extracted: Dict[str, Dict] = {}

    for section_name, start in sorted(target_positions.items(), key=lambda item: item[1]):
        end = len(normalized)
        for boundary in boundaries:
            if boundary > start:
                end = boundary
                break
        section_text = normalize_whitespace(normalized[start:end])
        if len(section_text) >= 20:
            extracted[section_name] = {"text": section_text, "start": start, "end": end}

    return extracted


def extract_sections(text: str, form_type: str) -> Dict[str, str]:
    section_records = extract_sections_with_spans(text, form_type)
    return {name: payload["text"] for name, payload in section_records.items()}
