import json
import re
from typing import Dict, List, Optional

from ollama import Client

from app.config import settings


def _dedupe_keep_order(items: List[str], limit: int = 6) -> List[str]:
    seen = set()
    result = []
    for item in items:
        cleaned = " ".join(str(item).split()).strip()
        if not cleaned:
            continue
        key = cleaned.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def _extract_json_block(text: str) -> Dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return {}


def _normalize_payload(payload: Dict) -> Dict:
    normalized = {
        "revenue_trends": payload.get("revenue_trends", []),
        "debt_risk_signals": payload.get("debt_risk_signals", []),
        "risk_factor_highlights": payload.get("risk_factor_highlights", []),
        "red_flags": payload.get("red_flags", []),
        "management_commentary": payload.get("management_commentary", []),
        "evidence_quotes": payload.get("evidence_quotes", []),
        "confidence": payload.get("confidence", 0.0),
    }

    for key in [
        "revenue_trends",
        "debt_risk_signals",
        "risk_factor_highlights",
        "red_flags",
        "management_commentary",
        "evidence_quotes",
    ]:
        if not isinstance(normalized[key], list):
            normalized[key] = []
        normalized[key] = [str(x) for x in normalized[key]]

    try:
        normalized["confidence"] = float(normalized["confidence"])
    except (TypeError, ValueError):
        normalized["confidence"] = 0.0

    normalized["confidence"] = max(0.0, min(1.0, normalized["confidence"]))
    return normalized


def merge_insights(chunks: List[Dict]) -> Dict:
    if not chunks:
        return _normalize_payload({})

    merged_lists = {
        "revenue_trends": [],
        "debt_risk_signals": [],
        "risk_factor_highlights": [],
        "red_flags": [],
        "management_commentary": [],
        "evidence_quotes": [],
    }
    confidences = []
    for chunk in chunks:
        normalized = _normalize_payload(chunk)
        for key in merged_lists:
            merged_lists[key].extend(normalized[key])
        confidences.append(normalized["confidence"])

    result = {k: _dedupe_keep_order(v, limit=8) for k, v in merged_lists.items()}
    result["confidence"] = sum(confidences) / len(confidences) if confidences else 0.0
    return result


def _find_quote_offset(section_text: str, quote: str) -> Optional[int]:
    q = " ".join(str(quote).split()).strip()
    if not q:
        return None
    idx = section_text.lower().find(q.lower())
    return idx if idx >= 0 else None


def attach_evidence_spans(insights: Dict, section_records: Dict[str, Dict]) -> Dict:
    evidence_quotes = insights.get("evidence_quotes", [])
    evidence_spans = []
    for quote in evidence_quotes:
        mapped = False
        for section_name, record in section_records.items():
            section_text = record.get("text", "")
            local_idx = _find_quote_offset(section_text, quote)
            if local_idx is None:
                continue
            start = int(record.get("start", 0)) + local_idx
            end = start + len(quote)
            evidence_spans.append({"quote": quote, "section": section_name, "start": start, "end": end})
            mapped = True
            break
        if not mapped:
            evidence_spans.append({"quote": quote, "section": "unknown", "start": None, "end": None})

    enriched = dict(insights)
    enriched["evidence_spans"] = evidence_spans
    return enriched


class FilingInsightEngine:
    def __init__(self) -> None:
        self.client = Client(host=settings.ollama_base_url)
        self.model = settings.ollama_model
        self.timeout_seconds = settings.ollama_timeout_seconds
        self.max_section_chars = settings.llm_max_section_chars

    def _prompt(self, form_type: str, section_name: str, section_text: str) -> str:
        return f"""
You are extracting filing insights for a financial analysis app.
Use only the provided SEC filing text. Do not infer beyond this text.

Return JSON only with these exact keys:
- revenue_trends: string[]
- debt_risk_signals: string[]
- risk_factor_highlights: string[]
- red_flags: string[]
- management_commentary: string[]
- evidence_quotes: string[]
- confidence: number between 0 and 1

Rules:
- If evidence is insufficient, use empty arrays.
- Keep bullets concise.
- Include brief quote-like snippets in evidence_quotes from the text.

Form: {form_type}
Section: {section_name}
Text:
{section_text[: self.max_section_chars]}
""".strip()

    def _analyze_section(self, form_type: str, section_name: str, section_text: str) -> Dict:
        response = self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": self._prompt(form_type, section_name, section_text)}],
            options={"temperature": 0},
        )
        content = response.get("message", {}).get("content", "")
        payload = _extract_json_block(content)
        return _normalize_payload(payload)

    def extract_from_sections(self, form_type: str, sections: Dict[str, str]) -> Dict:
        chunks = []
        for section_name, section_text in sections.items():
            if not section_text.strip():
                continue
            chunks.append(self._analyze_section(form_type=form_type, section_name=section_name, section_text=section_text))
        return merge_insights(chunks)

    def extract_from_section_records(self, form_type: str, section_records: Dict[str, Dict]) -> Dict:
        sections = {k: v.get("text", "") for k, v in section_records.items()}
        merged = self.extract_from_sections(form_type=form_type, sections=sections)
        return attach_evidence_spans(merged, section_records)
